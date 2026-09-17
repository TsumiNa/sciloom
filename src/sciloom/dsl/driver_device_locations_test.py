"""Logical configuration and captured physical selections have separate lifetimes."""

from dataclasses import dataclass, replace

import pytest

from sciloom import (
    Agitator,
    Function,
    Input,
    Output,
    RotationalSpeed,
    Timer,
    Zone,
    at,
    comptime,
    notify,
    rpm,
    runtime,
    s,
)
from sciloom.core.bindings import DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.bindings_selection_test import selection
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import DeviceEvent, Interpreter, ReferenceEnvironment, VirtualClock
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import LocationDirectory, Well


@dataclass
class SelectionTarget:
    bindings: DeviceBindings
    target_id = "test.selection/v1"

    def resolve_devices(self, program):
        return self.bindings

    def validate(self, program):
        return ()

    def emit(self, program):
        return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")


def environment(bindings=None):
    return ReferenceEnvironment(
        device_bindings=DeviceBindings(devices=(selection(),)) if bindings is None else bindings,
        locations=LocationDirectory(
            wells=tuple(Well(identity=name, name=name.upper()) for name in ("a", "b", "outside", "c", "d"))
        ),
    )


class ChooseTwice(Function):
    mixer: Agitator
    first: Input[Zone]
    second: Input[Zone]
    speed: Input[RotationalSpeed]
    stop_second: Input[bool]

    @runtime
    def run(self) -> None:
        self.mixer.speed = self.speed
        self.speed = 1200 * rpm
        with at(self.mixer, self.first):
            self.first = self.second
            self.mixer.start()
        self.mixer.speed = 600 * rpm
        with at(self.mixer, self.second):
            self.mixer.start()
            if self.stop_second:
                self.mixer.stop()


def test_selection_capture_does_not_stop_previous_controller_or_share_snapshots():
    env = environment()
    authored = ChooseTwice().to_ir()
    compiled = compile_ir(authored, target=SelectionTarget(env.device_bindings))
    assert authored == compiled.semantic_ir
    for program in (compiled.specialized_ir, from_json(to_json(compiled.specialized_ir))):
        session = Interpreter(program, environment=env)
        inputs = {
            "first": Zone(well_ids=("a",)),
            "second": Zone(well_ids=("b",)),
            "speed": 300 * rpm,
            "stop_second": True,
        }
        result = session.run(inputs=inputs)
        assert result.physical_devices["test:1"].enabled
        assert not result.physical_devices["test:2"].enabled
        assert result.physical_devices["test:1"].applied_configuration == {"speed": 300 * rpm}
        assert result.physical_devices["test:2"].applied_configuration == {"speed": 600 * rpm}
        logical = result.resources["resource:mixer"]
        assert logical.configuration == logical.applied_configuration == {"speed": 600 * rpm}
        assert not logical.enabled
        events = [event for event in result.events if isinstance(event, DeviceEvent)]
        assert [event.physical_id for event in events] == [None, "test:1", None, "test:2", "test:2"]
        assert events[1].physical_state == result.physical_devices["test:1"]
        later = session.run(
            inputs={**inputs, "first": inputs["second"], "second": inputs["first"], "stop_second": False}
        )
        assert all(state.enabled for state in later.physical_devices.values())
        assert not result.physical_devices["test:2"].enabled
        with pytest.raises(TypeError):
            result.physical_devices["test:1"] = later.physical_devices["test:1"]
        with pytest.raises(TypeError):
            result.physical_devices["test:1"].applied_configuration["speed"] = 1 * rpm


@pytest.mark.parametrize(
    "ids,code",
    [
        ((), "device_location"),
        (("unknown",), "unknown_well"),
        (("outside",), "device_location"),
        (("a", "b"), "device_location"),
    ],
)
def test_invalid_location_fails_before_body_while_prior_configuration_remains(ids, code):
    env = environment()
    session = Interpreter(ChooseTwice().to_ir(), environment=env)
    with pytest.raises(ExecutionError, match=code):
        session.run(
            inputs={
                "first": Zone(well_ids=ids),
                "second": Zone(well_ids=("b",)),
                "speed": 300 * rpm,
                "stop_second": False,
            }
        )
    assert len(env.events) == 1 and env.events[0].state.configuration == {"speed": 300 * rpm}
    assert env.events[0].physical_id is None
    # No stale scope from a failed selection; this valid invocation succeeds.
    result = session.run(
        inputs={
            "first": Zone(well_ids=("a",)),
            "second": Zone(well_ids=("b",)),
            "speed": 300 * rpm,
            "stop_second": False,
        }
    )
    assert all(state.enabled for state in result.physical_devices.values())


def test_child_calls_inherit_selection_and_return_configuration():
    class Configure(Function):
        mixer: Agitator

        @runtime
        def run(self) -> None:
            self.mixer.speed = 420 * rpm

    class Start(Function):
        mixer: Agitator

        @runtime
        def run(self) -> None:
            self.mixer.start()

    class Parent(Function):
        mixer: Agitator
        location: Input[Zone]

        def __init__(self):
            self.configure = Configure()
            self.start = Start()
            self.configure.mixer = self.mixer
            self.start.mixer = self.mixer

        @runtime
        def run(self) -> None:
            self.configure()
            with at(self.mixer, self.location):
                self.start()
                self.mixer.stop()

    env = environment()
    compiled = Parent().compile(target=SelectionTarget(env.device_bindings))
    result = Interpreter(compiled.specialized_ir, environment=env).run(inputs={"location": Zone(well_ids=("b",))})
    assert result.physical_devices["test:2"].applied_configuration == {"speed": 420 * rpm}
    assert not result.physical_devices["test:2"].enabled
    assert result.physical_devices["test:1"].applied_configuration == {}


def test_failure_unwinds_scope_without_stopping_or_rolling_back_device_effects():
    class FailInside(Function):
        mixer: Agitator
        location: Input[Zone]
        fail: Input[bool]

        @runtime
        def run(self) -> None:
            self.mixer.speed = 300 * rpm
            with at(self.mixer, self.location):
                self.mixer.start()
                if self.fail:
                    notify("No response is supplied")

    env = environment()
    session = Interpreter(FailInside().to_ir(), environment=env)
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        session.run(inputs={"location": Zone(well_ids=("a",)), "fail": True})
    assert env.events[-1].physical_state.enabled
    result = session.run(inputs={"location": Zone(well_ids=("b",)), "fail": False})
    assert all(state.enabled for state in result.physical_devices.values())


def test_missing_scope_and_nested_selection_through_calls_are_static_errors():
    class Missing(Function):
        mixer: Agitator

        @runtime
        def run(self) -> None:
            self.mixer.speed = 300 * rpm
            self.mixer.start()

    class Nested(Missing):
        location: Input[Zone]

        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location):
                with at(self.mixer, self.location):
                    pass

    class Select(Function):
        mixer: Agitator
        location: Input[Zone]

        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location):
                pass

    class Caller(Select):
        def __init__(self):
            self.child = Select()
            self.child.mixer = self.mixer

        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location):
                self.child(location=self.location)

    env = environment()
    target = SelectionTarget(env.device_bindings)
    with pytest.raises(CompilationError, match="device_selection_required"):
        Missing().compile(target=target)
    with pytest.raises(IRValidationError, match="device_selection_nesting"):
        Nested().to_ir()
    with pytest.raises(CompilationError, match="device_selection_nesting"):
        Caller().compile(target=target)
    with pytest.raises(IRValidationError, match="device_selection_nesting"):
        Interpreter(Caller().to_ir(), environment=env)


@pytest.mark.parametrize("other_well", ["c", "a"])
def test_different_device_scopes_can_nest_and_sessions_do_not_share_physical_state(other_well):
    class Two(Function):
        mixer: Agitator
        other: Agitator
        first: Input[Zone]
        second: Input[Zone]
        enabled: Input[bool]

        @runtime
        def run(self) -> None:
            if self.enabled:
                self.mixer.speed = 300 * rpm
                self.other.speed = 450 * rpm
                with at(self.mixer, self.first):
                    with at(self.other, self.second):
                        self.mixer.start()
                        self.other.start()

    base = selection().candidates[0].binding
    other = DeviceSelectionBinding(
        logical_id="other",
        candidates=(
            DeviceCandidate(
                binding=replace(base, logical_id="other", physical_id="test:3"),
                wells=Zone(well_ids=(other_well,)),
            ),
        ),
    )
    env = environment(DeviceBindings(devices=(selection(), other)))
    compiled = Two().compile(target=SelectionTarget(env.device_bindings))
    inputs = {"first": Zone(well_ids=("a",)), "second": Zone(well_ids=(other_well,)), "enabled": True}
    started = Interpreter(compiled.specialized_ir, environment=env).run(inputs=inputs)
    fresh = Interpreter(compiled.specialized_ir, environment=env).run(inputs={**inputs, "enabled": False})
    assert started.physical_devices["test:1"].enabled and started.physical_devices["test:3"].enabled
    assert started.physical_devices["test:1"].applied_configuration == {"speed": 300 * rpm}
    assert started.physical_devices["test:3"].applied_configuration == {"speed": 450 * rpm}
    assert not any(state.enabled for state in fresh.physical_devices.values())


def test_fixed_reference_binding_records_physical_state_without_location_scope():
    class Fixed(Function):
        mixer: Agitator

        @runtime
        def run(self) -> None:
            self.mixer.speed = 300 * rpm
            self.mixer.start()

    program = Fixed().to_ir()
    old = Interpreter(program).run()
    assert not old.physical_devices and all(event.physical_id is None for event in old.events)
    env = ReferenceEnvironment(device_bindings=DeviceBindings(devices=(selection().candidates[0].binding,)))
    bound = Interpreter(program, environment=env).run()
    assert bound.resources == old.resources
    assert bound.physical_devices["test:1"].enabled


def test_scope_body_guarantees_escape_on_normal_return_and_specialization_visits_body():
    class Body(Function):
        mixer: Agitator
        location: Input[Zone]
        result: Output[list[float]]
        timer: Timer

        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location):
                if comptime.supports(self.mixer, Agitator.start):
                    self.mixer.speed = 300 * rpm
                self.result = [1.0]
                self.timer.start()
            with at(self.mixer, self.location):
                self.mixer.start()
            self.timer.wait_until(5 * s)

    env = replace(environment(), clock=VirtualClock())
    authored = Body().to_ir()
    before = to_json(authored)
    compiled = compile_ir(from_json(before), target=SelectionTarget(env.device_bindings))
    result = Interpreter(compiled.specialized_ir, environment=env).run(inputs={"location": Zone(well_ids=("a",))})
    assert result.outputs == {"result": (1.0,)}
    assert env.clock.monotonic() == 5
    assert result.physical_devices["test:1"].enabled
    assert to_json(authored) == before
    # Backend analyses must also descend into the new structured scope.
    from sciloom_autosuite.timing import validate_timer_scopes
    from sciloom_autosuite.validation import validate_array_outputs

    assert validate_timer_scopes(compiled.specialized_ir) == ()
    assert validate_array_outputs(compiled.specialized_ir) == ()


def test_location_syntax_and_host_access_have_explicit_boundaries():
    class Base(Function):
        mixer: Agitator
        location: Input[Zone]

    class WrongType(Base):
        @runtime
        def run(self) -> None:
            with at(self.mixer, "rack"):
                pass

    class WrongDevice(Base):
        @runtime
        def run(self) -> None:
            with at(self.location, self.location):
                pass

    class Alias(Base):
        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location) as selected:
                pass

    class Multiple(Base):
        @runtime
        def run(self) -> None:
            with at(self.mixer, self.location), at(self.mixer, self.location):
                pass

    for model, code in (
        (WrongType, "zone_type"),
        (WrongDevice, "device_reference"),
        (Alias, "device_location_scope"),
        (Multiple, "device_location_scope"),
    ):
        with pytest.raises(IRValidationError, match=code):
            model().to_ir()
    with pytest.raises(TypeError, match="@runtime"):
        at(Base().mixer, Zone.empty())


def test_dynamic_reference_execution_requires_both_directory_and_binding_services():
    inputs = {"first": Zone(well_ids=("a",)), "second": Zone(well_ids=("b",)), "speed": 300 * rpm, "stop_second": True}
    for env in (
        ReferenceEnvironment(),
        ReferenceEnvironment(locations=environment().locations),
        ReferenceEnvironment(device_bindings=environment().device_bindings),
    ):
        with pytest.raises(ExecutionError, match="missing_environment_service"):
            Interpreter(ChooseTwice().to_ir(), environment=env).run(inputs=inputs)
