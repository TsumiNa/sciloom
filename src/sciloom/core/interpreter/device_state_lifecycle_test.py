"""Lifecycle contracts define effects without guessing command names."""

from dataclasses import replace

import pytest

from examples.developer.lifecycle_commands import AdjustableAgitator, BenchAgitator, Reconfigure, RecordingTarget
from sciloom import Function, Input, rpm, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.ir import (
    ConfigureProperty,
    DeviceCommand,
    LifecycleCommandContract,
    LifecycleEffect,
    Literal,
    ScalarType,
    from_json,
    to_json,
)
from sciloom.devices import operation
from sciloom.devices.declarations import bind_device
from .environment import ReferenceEnvironment
from .runtime import Interpreter


def test_compiled_and_json_lifecycle_capture_reapply_disable_and_frozen_history():
    target = RecordingTarget()
    compiled = Reconfigure().compile(target=target)
    for program in (compiled.semantic_ir, compiled.specialized_ir, from_json(compiled.artifact.content.decode())):
        bindings = target.resolve_devices(program)
        session = Interpreter(program, environment=ReferenceEnvironment(device_bindings=bindings))
        first = session.run()
        states = [event.state for event in first.events]
        assert len(states) == 7
        assert states[1].configuration == {"speed": 600 * rpm, "gain": 1.0}
        assert states[1].applied_configuration == {} and not states[1].enabled
        assert states[2].applied_configuration == states[1].configuration and states[2].enabled
        assert states[3].configuration["gain"] == 2.0 and states[3].applied_configuration["gain"] == 1.0
        assert states[4].applied_configuration["gain"] == 2.0 and states[4].enabled
        assert states[5].configuration["gain"] == 3.0 and states[5].enabled
        assert states[6].configuration == states[5].configuration
        assert states[6].applied_configuration == states[4].applied_configuration and not states[6].enabled
        assert first.physical_devices["bench-actuator-1"].applied_configuration == states[4].applied_configuration
        assert not first.physical_devices["bench-actuator-1"].enabled
        assert session.run().resources == first.resources
        assert states[1].configuration["gain"] == 1.0
        with pytest.raises(TypeError):
            states[1].configuration["gain"] = 9.0


class Apply(Function):
    agitator: AdjustableAgitator

    @runtime
    def run(self):
        self.agitator.apply()


class Parent(Function):
    agitator: AdjustableAgitator

    def __init__(self):
        self.child = Apply()
        self.child.agitator = self.agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm
        self.agitator.gain = 1.0
        self.child()
        self.agitator.gain = 2.0
        self.child()
        self.agitator.halt()


def test_shared_configuration_repeated_child_calls():
    target = RecordingTarget()
    compiled = Parent().compile(target=target)
    result = Interpreter(compiled.specialized_ir).run()
    applies = [event for event in result.events if event.operation_id.endswith(".apply/v1")]
    assert [event.state.applied_configuration["gain"] for event in applies] == [1.0, 2.0]
    assert not result.resources["resource:agitator"].enabled


def test_missing_configuration_fails_before_later_effects():
    class Missing(Function):
        agitator: AdjustableAgitator

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            self.agitator.apply()
            self.agitator.gain = 9.0

    with pytest.raises(CompilationError, match="device_configuration"):
        Missing().compile(target=RecordingTarget())
    environment = ReferenceEnvironment()
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(Missing().to_ir(), environment=environment).run()
    assert len(environment.events) == 1
    assert environment.events[0].state.configuration == {"speed": 600 * rpm}


def test_conditional_or_zero_iteration_configuration_cannot_prove_entry_requirements():
    class Conditional(Function):
        agitator: AdjustableAgitator
        flag: Input[bool]

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            if self.flag:
                self.agitator.gain = 2.0
            self.agitator.apply()

    class Loop(Function):
        agitator: AdjustableAgitator
        flag: Input[bool]

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            while self.flag:
                self.agitator.gain = 2.0
                self.flag = False
            self.agitator.apply()

    for cls in (Conditional, Loop, Apply):
        with pytest.raises(CompilationError, match="device_configuration"):
            cls().compile(target=RecordingTarget())
    session = Interpreter(Conditional().to_ir())
    session.run(inputs={"flag": True})
    assert session.run(inputs={"flag": False}).resources["resource:agitator"].enabled
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(Conditional().to_ir()).run(inputs={"flag": False})


def test_disable_does_not_implicitly_require_device_configuration():
    class Stop(Function):
        agitator: AdjustableAgitator

        @runtime
        def run(self):
            self.agitator.halt()

    compiled = Stop().compile(target=RecordingTarget())
    result = Interpreter(compiled.specialized_ir).run()
    assert result.resources["resource:agitator"].configuration == {}
    assert not result.resources["resource:agitator"].enabled


def test_forged_json_effect_and_ancestor_conflicts_cannot_pass_trusted_binding():
    program = Reconfigure().to_ir()
    bindings = RecordingTarget().resolve_devices(program)
    forged = replace(
        program,
        device_types=tuple(
            replace(
                contract,
                operations=tuple(
                    replace(op, effect=LifecycleEffect.DISABLE)
                    if isinstance(op, LifecycleCommandContract) and op.name == "apply"
                    else op
                    for op in contract.operations
                ),
            )
            for contract in program.device_types
        ),
    )
    restored = from_json(to_json(forged))
    with pytest.raises(IRValidationError, match="trusted contract"):
        Interpreter(restored, environment=ReferenceEnvironment(device_bindings=bindings))
    concrete = Reconfigure().compile(target=RecordingTarget()).specialized_ir
    conflict = replace(
        concrete,
        device_types=tuple(
            replace(
                contract,
                operations=tuple(
                    replace(op, effect=LifecycleEffect.DISABLE)
                    if isinstance(op, LifecycleCommandContract) and op.name == "apply"
                    else op
                    for op in contract.operations
                ),
            )
            if contract.type_id == "example.bench-agitator/v1"
            else contract
            for contract in concrete.device_types
        ),
    )
    with pytest.raises(IRValidationError, match="device_contract"):
        to_json(conflict)


def test_ordinary_command_is_not_inferred_as_a_lifecycle_effect():
    class Unknown(AdjustableAgitator):
        device_type_id = "test.unknown-lifecycle/v1"

        @operation(id="test.unknown-lifecycle.execute/v1")
        def execute(self) -> None:
            pytest.fail("Must never execute Python device code")

    class Use(Function):
        agitator: Unknown

        @runtime
        def run(self):
            self.agitator.execute()
            self.agitator.halt()

    program = from_json(to_json(Use().to_ir()))
    assert isinstance(program.functions[0].body[0], DeviceCommand)
    environment = ReferenceEnvironment()
    with pytest.raises(ExecutionError, match="unsupported_operation"):
        Interpreter(program, environment=environment).run()
    assert environment.events == ()


def test_explicit_disable_preconditions_and_writable_binding_checks():
    program = Reconfigure().compile(target=RecordingTarget()).specialized_ir
    contracts = tuple(
        replace(
            contract,
            operations=tuple(
                replace(op, required_configuration=("example.adjustable-agitator.gain/v1",))
                if isinstance(op, LifecycleCommandContract) and op.name == "halt"
                else op
                for op in contract.operations
            ),
        )
        for contract in program.device_types
    )
    base_binding = RecordingTarget().resolve_devices(program).devices[0]
    binding = replace(
        base_binding,
        contract=next(c for c in contracts if c.type_id == base_binding.contract.type_id),
        base_contracts=tuple(c for c in contracts if c.type_id in base_binding.contract.base_type_ids),
    )
    bindings = DeviceBindings(devices=(binding,))
    function = program.functions[0]
    halt = function.body[-1]
    program = replace(program, device_types=contracts, functions=(replace(function, body=(halt,)),))
    assert {d.code for d in validate_device_usage(program, bindings)} == {"device_configuration"}
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=ReferenceEnvironment(device_bindings=bindings)).run()
    gain_write = next(
        n for n in function.body if isinstance(n, ConfigureProperty) and n.property_id.endswith(".gain/v1")
    )
    # Literal write avoids depending on the example's local gain initialization.
    gain_write = replace(gain_write, value=Literal(node_id="gain", type=ScalarType.REAL, value=2.0))
    satisfied = replace(program, functions=(replace(function, body=(gain_write, halt)),))
    assert validate_device_usage(satisfied, bindings) == ()
    state = (
        Interpreter(satisfied, environment=ReferenceEnvironment(device_bindings=bindings))
        .run()
        .resources["resource:agitator"]
    )
    assert state.configuration == {"gain": 2.0} and state.applied_configuration == {} and not state.enabled
    # Even a profile with no device-wide requirements must make a supported
    # command's explicit requirements writable.
    with pytest.raises(ValueError, match="lifecycle command configuration"):
        replace(
            binding,
            contract=replace(binding.contract, required_configuration=()),
            writable_properties=("sciloom.agitator.speed/v1",),
        )


def test_configuration_inside_loop_is_available_to_child_before_each_apply():
    class LoopParent(Function):
        agitator: AdjustableAgitator
        again: Input[bool]

        def __init__(self):
            self.child = Apply()
            self.child.agitator = self.agitator

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            while self.again:
                self.agitator.gain = 2.0
                self.child()
                self.again = False

    compiled = LoopParent().compile(target=RecordingTarget())
    assert Interpreter(compiled.specialized_ir).run(inputs={"again": True}).resources["resource:agitator"].enabled
    assert not Interpreter(compiled.specialized_ir).run(inputs={"again": False}).resources["resource:agitator"].enabled


def test_distinct_child_resource_cannot_borrow_parent_configuration():
    class Independent(Function):
        agitator: AdjustableAgitator

        def __init__(self):
            self.child = Apply()

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            self.agitator.gain = 1.0
            self.child()
            self.agitator.apply()

    class SeparateTarget(RecordingTarget):
        def resolve_devices(self, program):
            return DeviceBindings(
                devices=tuple(
                    bind_device(logical_id=name, device=BenchAgitator(), physical_id=identity)
                    for name, identity in (("agitator", "parent-actuator"), ("child.agitator", "child-actuator"))
                )
            )

    with pytest.raises(CompilationError, match="device_configuration"):
        Independent().compile(target=SeparateTarget())
    environment = ReferenceEnvironment()
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(Independent().to_ir(), environment=environment).run()
    assert len(environment.events) == 2
    assert all(not event.state.enabled for event in environment.events)
