"""Properties and methods retain Python typing while contributing data contracts."""

import pytest
from dataclasses import FrozenInstanceError

from sciloom import Agitator, RotationalSpeed, rpm
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker
from sciloom.core.ir.device_contracts import AGITATOR_CONTRACT
from .declarations import bind_device, device_contract, operation


def test_builtin_signatures_and_explicit_profile_capabilities():
    assert device_contract(Agitator) == AGITATOR_CONTRACT
    profile = AutoSuiteIndividualShaker(zone="A", device_id="23")
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

    with pytest.raises(TypeError, match="types must match"):
        device_contract(Mismatch)

    class Nonvoid(Agitator):
        device_type_id = "test.nonvoid/v1"

        @operation(id="test.measure/v1")
        def measure(self) -> float:
            return 1.0

    with pytest.raises(TypeError, match="return None"):
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
