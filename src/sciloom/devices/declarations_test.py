"""Properties and methods retain Python typing while contributing data contracts."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom import Agitator, Zone, rpm
from sciloom.conftest import StubShaker
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import LifecycleCommandContract, LifecycleEffect
from sciloom.core.ir.device_contracts import AGITATOR_CONTRACT
from .declarations import bind_device, device_contract, operation


def test_builtin_signatures_and_explicit_profile_capabilities():
    assert device_contract(Agitator) == AGITATOR_CONTRACT
    profile = StubShaker()
    binding = bind_device(logical_id="agitator", device=profile, physical_id="test:23")
    assert binding.contract.required_configuration == binding.writable_properties
    assert len(binding.supported_operations) == 2
    with pytest.raises(FrozenInstanceError):
        profile.speed = 600 * rpm
    with pytest.raises(TypeError, match="compiled"):
        Agitator().speed = 600 * rpm
    with pytest.raises(TypeError, match="reads"):
        _ = profile.speed
    with pytest.raises(TypeError, match="compiled"):
        profile.start()


def test_mismatched_property_types_and_nonvoid_commands_are_rejected():
    class Mismatch(Agitator):
        device_type_id = "test.mismatch/v1"

        @property
        def gain(self) -> float:
            pytest.fail("getter must not execute")

        @gain.setter
        @operation(id="test.gain/v1")
        def gain(self, value: int) -> None:
            pytest.fail("setter must not execute")

    with pytest.raises(IRValidationError, match="types must match"):
        device_contract(Mismatch)

    class Nonvoid(Agitator):
        device_type_id = "test.nonvoid/v1"

        @operation(id="test.measure/v1")
        def measure(self) -> float:
            return 1.0

    with pytest.raises(IRValidationError, match="return None"):
        device_contract(Nonvoid)


def test_concrete_profiles_cannot_infer_capabilities_from_inheritance():
    class Implicit(Agitator):
        device_type_id = "test.implicit/v1"

    with pytest.raises(TypeError, match="explicitly declare"):
        bind_device(logical_id="agitator", device=Implicit(), physical_id="test:1")


def test_unregistered_host_members_are_inspected_without_getattr_execution():
    class HostValue:
        def __getattr__(self, name):
            pytest.fail("declaration inspection must not invoke user attribute lookup")

    class Contract(Agitator):
        device_type_id = "test.static-inspection/v1"
        metadata = HostValue()

    assert device_contract(Contract).properties == AGITATOR_CONTRACT.properties


def test_zone_values_do_not_expand_device_property_or_command_types():
    class LocatedProperty(Agitator):
        device_type_id = "test.located-property/v1"

        @property
        def location(self) -> Zone:
            pytest.fail("getter must not execute")

        @location.setter
        @operation(id="test.location/v1")
        def location(self, value: Zone) -> None:
            pytest.fail("setter must not execute")

    class LocatedCommand(Agitator):
        device_type_id = "test.located-command/v1"

        @operation(id="test.located-command.perform/v1")
        def perform(self, location: Zone) -> None:
            pytest.fail("command must not execute")

    for cls in (LocatedProperty, LocatedCommand):
        with pytest.raises(IRValidationError, match="device_contract"):
            device_contract(cls)


@pytest.mark.parametrize(
    "options",
    [
        {"requires": ("speed",)},
        {"lifecycle": "apply_and_enable"},
        {"lifecycle": LifecycleEffect.DISABLE, "requires": ("speed", "speed")},
        {"lifecycle": LifecycleEffect.DISABLE, "requires": ["speed"]},
        {"lifecycle": LifecycleEffect.DISABLE, "requires": (1,)},
    ],
)
def test_invalid_decorator_metadata_rejected(options):
    with pytest.raises(IRValidationError):
        operation(id="test.lifecycle/v1", **options)


def test_lifecycle_requires_resolves_inherited_properties_without_changing_ancestor_contracts():
    class Extension(Agitator):
        device_type_id = "test.requirements/v1"

        @operation(id="test.requirements.halt/v1", lifecycle=LifecycleEffect.DISABLE, requires=("speed",))
        def halt(self) -> None:
            pytest.fail("Declaration body must not execute")

    contract = device_contract(Extension)
    command = contract.operations[-1]
    assert isinstance(command, LifecycleCommandContract)
    assert command.required_configuration == AGITATOR_CONTRACT.required_configuration
    assert contract.operations[:-1] == AGITATOR_CONTRACT.operations


@pytest.mark.parametrize("kind", ["argument", "setter", "missing"])
def test_lifecycle_rejects_uninterpreted_arguments_setters_and_unknown_property_names(kind):
    class WithArgument(Agitator):
        device_type_id = "test.argument/v1"

        @operation(id="test.argument.apply/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE)
        def apply(self, ignored: float) -> None: ...

    class WithSetter(Agitator):
        device_type_id = "test.setter/v1"

        @property
        def gain(self) -> float:
            return 1.0

        @gain.setter
        @operation(id="test.setter.gain/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE)
        def gain(self, value: float) -> None: ...

    class Missing(Agitator):
        device_type_id = "test.missing/v1"

        @operation(id="test.missing.apply/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE, requires=("unknown",))
        def apply(self) -> None: ...

    with pytest.raises(IRValidationError):
        device_contract({"argument": WithArgument, "setter": WithSetter, "missing": Missing}[kind])
