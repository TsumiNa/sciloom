"""Author Zone loops capture selections and preserve explicit runtime state."""

import pytest

from sciloom import Agitator, Function, Input, Output, Timer, Var, Zone, comptime, log, rpm, runtime, s, zones
from sciloom.conftest import RecordingTarget, StubShaker
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import ForEachZone, from_json, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.core.locations import LocationDirectory, Well


class Clear(Function):
    value: Input[Zone]
    result: Output[Zone]

    @runtime
    def run(self) -> None:
        self.result = Zone.empty()


class Visit(Function):
    rack: Input[Zone]
    well: Var[Zone] = Zone.empty()
    count: Output[int]
    last: Output[Zone]

    def __init__(self):
        self.clear = Clear()

    @runtime
    def run(self) -> None:
        self.count = 0
        for self.well in self.rack:
            log(zones.well_name(self.well), category="rack", stream="well")
            self.count += 1
            self.rack = Zone.empty()
            self.well = self.clear(value=self.well)
        self.last = self.well


def test_captured_selection_survives_source_and_target_writes_and_callee_outputs():
    directory = LocationDirectory(wells=(Well(identity="27", name="first"), Well(identity="0", name="second")))
    for program in (Visit().to_ir(), from_json(to_json(Visit().to_ir()))):
        session = Interpreter(program, environment=ReferenceEnvironment(locations=directory))
        result = session.run(inputs={"rack": Zone(well_ids=("27", "0"))})
        assert result.outputs == {"count": 2, "last": Zone.empty()}
        assert [event.value for event in result.events] == ["first", "second"]
        assert session.run(inputs={"rack": Zone.empty()}).outputs == {"count": 0, "last": Zone.empty()}


class Grouped(Function):
    rack: Input[Zone]
    well: Var[Zone] = Zone.empty()
    count: Var[int] = 0
    result: Output[int]

    def __init__(self, size=2):
        self.size = size

    @runtime
    def run(self) -> None:
        for self.well in zones.fragments(self.rack, size=self.size):
            log(len(self.well), category="rack", stream="group size")
            self.count += 1
        self.result = self.count


def test_group_validation_precedes_all_body_effects_and_prior_effects_survive_failure():
    environment = ReferenceEnvironment()
    session = Interpreter(Grouped().to_ir(), environment=environment)
    before = session.run(inputs={"rack": Zone(well_ids=("a", "b"))})
    assert before.outputs == {"result": 1}
    with pytest.raises(ExecutionError, match="zone_fragment_size"):
        session.run(inputs={"rack": Zone(well_ids=("x", "y", "z"))})
    after = session.run(inputs={"rack": Zone.empty()})
    assert after.outputs == {"result": 1}
    assert after.state == before.state
    assert len(environment.events) == 1
    assert Interpreter(Grouped().to_ir()).run(inputs={"rack": Zone.empty()}).outputs == {"result": 0}


@pytest.mark.parametrize("size", [0, -1, True, 2.0, "2", None])
def test_group_size_is_an_exact_positive_host_integer(size):
    with pytest.raises(IRValidationError, match="zone_fragment_size"):
        Grouped(size).to_ir()


def test_nested_loops_can_reuse_target_without_corrupting_captured_selections():
    class Nested(Function):
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()
        count: Output[int]
        last: Output[Zone]

        @runtime
        def run(self) -> None:
            self.count = 0
            for self.well in self.rack:
                for self.well in self.rack:
                    self.count += 1
                self.well = Zone.empty()
            self.last = self.well

    result = Interpreter(Nested().to_ir()).run(inputs={"rack": Zone(well_ids=("27", "0", "8"))})
    assert result.outputs == {"count": 9, "last": Zone.empty()}


def test_index_failure_preserves_destination_and_stops_later_effects():
    class Select(Function):
        rack: Input[Zone]
        index: Input[int]
        enabled: Input[bool]
        selected: Var[Zone] = Zone.empty()
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            if self.enabled:
                self.selected = self.rack[self.index]
                log(self.index, category="rack", stream="selected")
            self.result = self.selected

    environment = ReferenceEnvironment()
    session = Interpreter(Select().to_ir(), environment=environment)
    inputs = {"rack": Zone(well_ids=("27", "0")), "index": 0, "enabled": True}
    before = session.run(inputs=inputs)
    for index in (-1, 2):
        with pytest.raises(ExecutionError, match="index_bounds"):
            session.run(inputs={**inputs, "index": index})
    assert session.run(inputs={**inputs, "enabled": False}).outputs == before.outputs
    assert len(environment.events) == 1


def test_loop_targets_language_and_marker_boundaries():
    class InputTarget(Function):
        rack: Input[Zone]

        @runtime
        def run(self) -> None:
            for self.rack in self.rack:
                pass

    class OutputTarget(Function):
        rack: Input[Zone]
        well: Output[Zone]

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                pass

    class LocalTarget(Visit):
        @runtime
        def run(self) -> None:
            for well in self.rack:
                pass

    class RuntimeSize(Grouped):
        dynamic_size: Input[int]

        @runtime
        def run(self) -> None:
            for self.well in zones.fragments(self.rack, size=self.dynamic_size):
                pass

    class Else(Visit):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                pass
            else:
                self.count = 0

    class Break(Visit):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                break

    class Continue(Visit):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                continue

    class IterateList(Visit):
        values: Input[list[int]]

        @runtime
        def run(self) -> None:
            for self.well in self.values:
                pass

    for cls, code in (
        (InputTarget, "zone_loop_target"),
        (OutputTarget, "zone_loop_target"),
        (LocalTarget, "python_subset"),
        (RuntimeSize, "zone_fragment_size"),
        (Else, "python_subset"),
        (Break, "python_subset"),
        (Continue, "python_subset"),
        (IterateList, "zone_type"),
    ):
        with pytest.raises(IRValidationError, match=code):
            cls().to_ir()
    with pytest.raises(TypeError, match="@runtime"):
        zones.fragments(Zone.empty(), size=2)


def test_specialization_and_definite_configuration_traverse_loop_bodies():
    class Configure(Function):
        shaker: Agitator
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                if comptime.supports(self.shaker, Agitator.start):
                    self.shaker.speed = 300 * rpm
                    self.shaker.start()

    target = RecordingTarget(devices={"shaker": StubShaker()})
    authored = Configure().to_ir()
    result = Configure().compile(target=target)
    assert any(isinstance(node, ForEachZone) for node, _ in iter_nodes(result.specialized_ir))
    assert result.semantic_ir == authored
    assert "DeviceIf" not in to_json(result.specialized_ir)

    class Incomplete(Configure):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.shaker.speed = 300 * rpm
            self.shaker.start()

    class Unconfigured(Configure):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.shaker.start()

    for cls in (Incomplete, Unconfigured):
        with pytest.raises(CompilationError, match="device_configuration"):
            cls().compile(target=target)


def test_timer_start_inside_a_possibly_empty_loop_does_not_escape_it():
    class Timed(Function):
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()
        timer: Timer

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.timer.start()
            self.timer.wait_until(2 * s)

    with pytest.raises(CompilationError, match="timer_not_started"):
        Timed().compile(target=RecordingTarget(devices={}))


def test_literal_empty_loop_has_no_configuration_or_timer_requirements():
    class Empty(Function):
        shaker: Agitator
        timer: Timer
        well: Var[Zone] = Zone.empty()

        @runtime
        def run(self) -> None:
            for self.well in Zone.empty():
                self.shaker.start()
                self.timer.wait_until(2 * s)

    Empty().compile(target=RecordingTarget(devices={"shaker": StubShaker()}))


def test_fragment_alias_keyword_binding_and_singleton_groups():
    groups = zones.fragments

    class Alias(Grouped):
        @runtime
        def run(self) -> None:
            for self.well in groups(value=self.rack, size=1):
                self.count += 1
            self.result = self.count

    assert Interpreter(Alias().to_ir()).run(inputs={"rack": Zone(well_ids=("a", "b"))}).outputs == {"result": 2}
