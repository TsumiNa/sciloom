"""Bounded transfer intent has explicit facts, ordered capture and no partial action."""

from dataclasses import replace

import pytest

from examples.developer.transfer_sample_ir import (
    DESTINATION,
    LOCATIONS,
    SOURCE,
    BenchLiquidHandler,
    TransferRecordingTarget,
    build_program,
)
from examples.transfer_sample import TransferSample
from sciloom import Function, Input, LiquidHandler, Zone, mL, mL_per_min, runtime
from sciloom.core.bindings import DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.ir import DeviceAt, ZoneLiteral, from_json, to_json
from sciloom.devices.declarations import bind_device
from sciloom_autosuite import AutoSuiteTarget
from . import DeviceEvent, Interpreter, LogEvent, ReferenceEnvironment, TransferEvent


def environment(program, **overrides):
    options = {"device_bindings": TransferRecordingTarget().resolve_devices(program), "locations": LOCATIONS}
    options.update(overrides)
    return ReferenceEnvironment(**options)


def with_body(program, body):
    return replace(program, functions=(replace(program.functions[0], body=tuple(body)),))


def test_python_direct_json_and_specialization_record_same_transfer():
    target = TransferRecordingTarget()
    compiled = TransferSample().compile(target=target)
    direct = build_program()
    states = []
    for program in (compiled.semantic_ir, compiled.specialized_ir, direct, from_json(to_json(direct))):
        result = Interpreter(program, environment=environment(program)).run(
            inputs={"source": SOURCE, "destination": DESTINATION}
        )
        assert [type(event) for event in result.events] == [DeviceEvent] * 3 + [TransferEvent, LogEvent]
        event = result.events[3]
        assert event.source == SOURCE and event.destination == DESTINATION and event.volume == 0.25 * mL
        state = next(iter(result.resources.values()))
        assert state.configuration == state.applied_configuration == event.configuration
        assert not state.enabled and not result.physical_devices[event.physical_id].enabled
        assert result.physical_devices[event.physical_id].applied_configuration == event.configuration
        states.append(state)
        with pytest.raises(TypeError):
            event.configuration["air_gap"] = 1 * mL
    assert all(state == states[0] for state in states)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("source", Zone.empty(), "transfer_location"),
        ("destination", Zone.empty(), "transfer_location"),
        ("source", Zone(well_ids=("well:source", "well:destination")), "transfer_location"),
        ("destination", Zone(well_ids=("well:unknown",)), "unknown_well"),
        ("source", DESTINATION, "transfer_location"),
        ("destination", SOURCE, "transfer_location"),
    ],
)
def test_invalid_location_has_no_transfer_or_following_log(field, value, code):
    program = build_program()
    env = environment(program)
    session = Interpreter(program, environment=env)
    inputs = {"source": SOURCE, "destination": DESTINATION, field: value}
    with pytest.raises(ExecutionError, match=code):
        session.run(inputs=inputs)
    assert len(env.events) == 3 and all(isinstance(e, DeviceEvent) for e in env.events)
    assert all(not event.state.applied_configuration for event in env.events)


@pytest.mark.parametrize(
    "index,value,code",
    [
        (0, 0.0, "transfer_range"),
        (0, -1.0, "transfer_range"),
        (1, 0.0, "transfer_range"),
        (1, -1.0, "transfer_range"),
        (2, -1e-9, "transfer_range"),
        (2, 1e-6, "transfer_capacity"),
        (3, 0.0, "transfer_range"),
        (3, -1e-9, "transfer_range"),
        (3, 1e-6, "transfer_capacity"),
    ],
)
def test_invalid_parameters_fail_before_action(index, value, code):
    program = build_program()
    body = list(program.functions[0].body)
    if index < 3:
        body[index] = replace(body[index], value=replace(body[index].value, value=value))
    else:
        command = body[3]
        body[3] = replace(
            command,
            arguments=(
                *command.arguments[:2],
                replace(command.arguments[2], value=replace(command.arguments[2].value, value=value)),
            ),
        )
    program = with_body(program, body)
    env = environment(program)
    with pytest.raises(ExecutionError, match=code):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert len(env.events) == 3 and not any(isinstance(e, (TransferEvent, LogEvent)) for e in env.events)


def test_capacity_boundary_and_configuration_snapshots_across_invocations():
    program = build_program()
    body = list(program.functions[0].body)
    # Exactly representable binary quantities avoid conflating capacity with decimal rounding.
    body[2] = replace(body[2], value=replace(body[2].value, value=0.25))
    command = body[3]
    body[3] = replace(
        command,
        arguments=(
            *command.arguments[:2],
            replace(command.arguments[2], value=replace(command.arguments[2].value, value=0.75)),
        ),
    )
    program = with_body(program, body)
    binding = environment(program).device_bindings.devices[0]
    from sciloom.units import Volume

    env = environment(
        program, device_bindings=DeviceBindings(devices=(replace(binding, usable_capacity=Volume(m3=1)),))
    )
    session = Interpreter(program, environment=env)
    first = session.run(inputs={"source": SOURCE, "destination": DESTINATION})
    second = session.run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert first.resources == second.resources
    assert first.events[3].configuration["air_gap"].m3 == 0.25
    assert len([e for e in env.events if isinstance(e, TransferEvent)]) == 2


@pytest.mark.parametrize("service", ["locations", "device_bindings"])
def test_missing_services_are_not_inferred(service):
    program = build_program()
    env = environment(program, **{service: None})
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert len(env.events) == 3


def test_plain_binding_and_unknown_deployment_wells_fail():
    program = build_program()
    fixed = environment(program).device_bindings.devices[0]
    for binding, code in (
        (fixed.binding, "transfer_binding"),
        (replace(fixed, source_wells=Zone(well_ids=("unknown",))), "transfer_binding"),
    ):
        env = environment(program, device_bindings=DeviceBindings(devices=(binding,)))
        with pytest.raises(ExecutionError, match=code):
            Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
        assert len(env.events) == 3

    class PlainTarget(TransferRecordingTarget):
        def resolve_devices(self, program):
            return DeviceBindings(devices=(fixed.binding,))

    with pytest.raises(CompilationError, match="TransferDeviceBinding"):
        compile_ir(program, target=PlainTarget())


def test_same_well_rejected_even_when_allowed_in_both_roles():
    program = build_program()
    fixed = environment(program).device_bindings.devices[0]
    env = environment(program, device_bindings=DeviceBindings(devices=(replace(fixed, destination_wells=SOURCE),)))
    with pytest.raises(ExecutionError, match="distinct"):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": SOURCE})
    assert not any(isinstance(e, TransferEvent) for e in env.events)


@pytest.mark.parametrize("missing", [0, 1, 2])
def test_each_configuration_required_by_compile_and_reference(missing):
    program = build_program()
    program = with_body(program, [s for i, s in enumerate(program.functions[0].body) if i != missing])
    with pytest.raises(CompilationError, match="device_configuration"):
        compile_ir(program, target=TransferRecordingTarget())
    env = environment(program)
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert len(env.events) == 2


def test_reordered_json_arguments_evaluated_once_in_declared_order(monkeypatch):
    from . import runtime as executor

    program = build_program()
    body = list(program.functions[0].body)
    command = body[3]
    body[3] = replace(command, arguments=tuple(reversed(command.arguments)))
    program = from_json(to_json(with_body(program, body)))
    captured = []
    original = executor.evaluate
    tracked = {a.value.node_id for a in command.arguments}

    def evaluate(session, expression, frame):
        if expression.node_id in tracked:
            captured.append(expression.node_id)
        return original(session, expression, frame)

    monkeypatch.setattr(executor, "evaluate", evaluate)
    Interpreter(program, environment=environment(program)).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert captured == [a.value.node_id for a in command.arguments]


class ChildTransfer(Function):
    liquid: LiquidHandler
    source: Input[Zone]
    destination: Input[Zone]

    @runtime
    def run(self):
        self.liquid.transfer(self.source, self.destination, 0.25 * mL)


class SharedTransfer(Function):
    liquid: LiquidHandler
    source: Input[Zone]
    destination: Input[Zone]

    def __init__(self):
        self.child = ChildTransfer()
        self.child.liquid = self.liquid

    @runtime
    def run(self):
        self.liquid.aspirate_flow = 1 * mL_per_min
        self.liquid.dispense_flow = 2 * mL_per_min
        self.liquid.air_gap = 0 * mL
        self.child(source=self.source, destination=self.destination)
        self.liquid.aspirate_flow = 3 * mL_per_min
        self.child(source=self.source, destination=self.destination)


def test_shared_cross_function_configuration_snapshots():
    compiled = SharedTransfer().compile(target=TransferRecordingTarget())
    program = from_json(compiled.artifact.content.decode())
    result = Interpreter(program, environment=environment(program)).run(
        inputs={"source": SOURCE, "destination": DESTINATION}
    )
    transfers = [e for e in result.events if isinstance(e, TransferEvent)]
    assert [e.configuration["aspirate_flow"] for e in transfers] == [1 * mL_per_min, 3 * mL_per_min]
    assert not result.resources["resource:liquid"].enabled
    assert result.resources["resource:liquid"].applied_configuration == transfers[-1].configuration


@pytest.mark.parametrize("profile", [LiquidHandler, BenchLiquidHandler])
@pytest.mark.parametrize("scoped", [False, True])
def test_dynamic_tool_selection_rejected_and_native_transfer_gated(profile, scoped):
    program = build_program()
    if scoped:
        program = with_body(
            program,
            (
                DeviceAt(
                    node_id="at",
                    resource_id="liquid",
                    location=ZoneLiteral(node_id="at-zone", well_ids=SOURCE.well_ids),
                    body=program.functions[0].body,
                ),
            ),
        )
    bindings = DeviceBindings(
        devices=(
            DeviceSelectionBinding(
                logical_id="liquid",
                candidates=(
                    DeviceCandidate(
                        binding=bind_device(logical_id="liquid", device=profile(), physical_id="tool:1"),
                        wells=SOURCE,
                    ),
                ),
            ),
        )
    )
    with pytest.raises(IRValidationError, match="unsupported_transfer_selection"):
        Interpreter(program, environment=environment(program, device_bindings=bindings))
    codes = {d.code for d in AutoSuiteTarget().validate(program)}
    assert "unsupported_device_command" in codes


def test_configuration_only_liquid_handler_still_requires_fixed_deployment():
    program = build_program()
    program = with_body(program, program.functions[0].body[:3])
    candidate = bind_device(logical_id="liquid", device=BenchLiquidHandler(), physical_id="tool:1")
    bindings = DeviceBindings(
        devices=(
            DeviceSelectionBinding(
                logical_id="liquid",
                candidates=(DeviceCandidate(binding=candidate, wells=SOURCE),),
            ),
        )
    )

    class DynamicTarget(TransferRecordingTarget):
        def resolve_devices(self, program):
            return bindings

    with pytest.raises(CompilationError, match="unsupported_transfer_selection"):
        compile_ir(program, target=DynamicTarget())
    with pytest.raises(IRValidationError, match="unsupported_transfer_selection"):
        Interpreter(program, environment=environment(program, device_bindings=bindings))
    # The family restriction does not make fixed configuration writes require an action.
    compiled = compile_ir(program, target=TransferRecordingTarget())
    result = Interpreter(compiled.specialized_ir, environment=environment(program)).run(
        inputs={"source": SOURCE, "destination": DESTINATION},
    )
    assert len(result.events) == 3 and all(isinstance(event, DeviceEvent) for event in result.events)
    assert not next(iter(result.resources.values())).applied_configuration


@pytest.mark.parametrize("loop", [False, True])
def test_conditional_configuration_not_assumed_from_previous_call(loop):
    class Conditional(Function):
        liquid: LiquidHandler
        source: Input[Zone]
        destination: Input[Zone]
        configure: Input[bool]

        def __init__(self):
            self.use_loop = loop

        @runtime
        def run(self):
            self.liquid.aspirate_flow = 1 * mL_per_min
            self.liquid.dispense_flow = 2 * mL_per_min
            if self.use_loop:
                while self.configure:
                    self.liquid.air_gap = 0 * mL
                    self.configure = False
            else:
                if self.configure:
                    self.liquid.air_gap = 0 * mL
            self.liquid.transfer(self.source, self.destination, 0.25 * mL)

    with pytest.raises(CompilationError, match="device_configuration"):
        Conditional().compile(target=TransferRecordingTarget())
    program = Conditional().to_ir()
    env = environment(program)
    session = Interpreter(program, environment=env)
    inputs = {"source": SOURCE, "destination": DESTINATION}
    session.run(inputs={**inputs, "configure": True})
    assert isinstance(session.run(inputs={**inputs, "configure": False}).events[-1], TransferEvent)
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=environment(program)).run(inputs={**inputs, "configure": False})


def test_independent_child_does_not_borrow_configuration():
    class Independent(SharedTransfer):
        def __init__(self):
            self.child = ChildTransfer()

    class SeparateTarget(TransferRecordingTarget):
        def resolve_devices(self, program):
            original = super().resolve_devices(program).devices[0]
            return DeviceBindings(
                devices=(
                    original,
                    replace(
                        original,
                        binding=replace(
                            original.binding,
                            logical_id="child.liquid",
                            physical_id="reference:child",
                        ),
                    ),
                )
            )

    target = SeparateTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        Independent().compile(target=target)
    program = Independent().to_ir()
    env = environment(program, device_bindings=target.resolve_devices(program))
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert len(env.events) == 3


def test_derived_contract_cannot_waive_family_requirements_and_can_add_extras():
    from sciloom.devices import operation

    class Extra(LiquidHandler):
        device_type_id = "test.extra-liquid/v1"
        writable_properties = ("aspirate_flow", "dispense_flow", "air_gap", "gain")
        required_configuration = ("gain",)
        supported_operations = (LiquidHandler.transfer,)

        @property
        def gain(self) -> float:
            pytest.fail("host getter must not execute")

        @gain.setter
        @operation(id="test.extra-liquid.gain/v1")
        def gain(self, value: float) -> None:
            pytest.fail("host setter must not execute")

    class ExtraTarget(TransferRecordingTarget):
        def resolve_devices(self, program):
            original = super().resolve_devices(program).devices[0]
            return DeviceBindings(
                devices=(
                    replace(
                        original,
                        binding=bind_device(
                            logical_id="liquid",
                            device=Extra(),
                            physical_id=original.physical_id,
                        ),
                    ),
                )
            )

    target = ExtraTarget()
    for author in (TransferSample(), ChildTransfer()):
        with pytest.raises(CompilationError, match="device_configuration"):
            author.compile(target=target)
        program = author.to_ir()
        env = environment(program, device_bindings=target.resolve_devices(program))
        with pytest.raises(ExecutionError, match="device_configuration"):
            Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
        assert not any(isinstance(e, TransferEvent) for e in env.events)


def test_failed_later_transfer_preserves_previous_applied_state_and_history():
    program = build_program()
    env = environment(program)
    session = Interpreter(program, environment=env)
    success = session.run(inputs={"source": SOURCE, "destination": DESTINATION})
    with pytest.raises(ExecutionError, match="unknown_well"):
        session.run(inputs={"source": SOURCE, "destination": Zone(well_ids=("missing",))})
    assert session._devices.states == success.resources
    assert session._devices.physical == success.physical_devices
    assert len([e for e in env.events if isinstance(e, TransferEvent)]) == 1
    assert len([e for e in env.events if isinstance(e, LogEvent)]) == 1
