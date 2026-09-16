"""Native sequential macros retain capture, target isolation and lexical scopes.

These are XML/reference checks, not Executor simulation results.
"""

import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Output, Timer, Var, Zone, runtime, s, zones
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from .target import AutoSuiteTarget


class Clear(Function):
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
            self.count += 1
            self.rack = Zone.empty()
            self.well = self.clear()
        self.last = self.well


def test_native_iterator_is_private_captured_and_wrapped_in_nonempty_guard():
    program = Visit().to_ir()
    before = to_json(program)
    compiled = compile_ir(from_json(before), target=AutoSuiteTarget())
    assert compiled.semantic_ir == compiled.specialized_ir == program
    assert to_json(program) == before
    assert Visit().compile(target=AutoSuiteTarget()).artifact == compiled.artifact
    xml = ET.fromstring(compiled.artifact.content)
    sequential = next(task for task in xml.iter() if task.findtext("executionmode") == "1")
    configuration = sequential.find("sequentialzones")
    assert configuration.findtext("count") == "1"
    source = configuration.findtext("sequentialzone0/zonename")
    iterator = configuration.findtext("sequentialzone0/variablename")
    assert configuration.findtext("sequentialzone0/fragmentsize") == "1"
    assert source != "rack" and iterator != "well" and source != iterator
    local = sequential.find("variables/variable")
    assert local.findtext("name") == iterator
    assert [local.findtext(p) for p in ("value/type", "value/value", "siunit", "unit", "array")] == [
        "8",
        "",
        "zone",
        "zone",
        "0",
    ]
    assert sequential.findtext("loopvariable") != sequential.findtext("fragmentvariable")
    tasks = list(sequential.find("tasks"))
    assert tasks[0].findtext("variablename") == "well" and tasks[0].findtext("expressiontext") == iterator
    call = sequential.find(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']")
    assert call.findtext("functiondata/outputs/item0/variablename") == "well"
    # No user assignment/callee return writes the native iterator.
    assert iterator not in [task.findtext("variablename") for task in sequential.findall(".//task")]
    wrapper = next(task for task in xml.iter() if task.findtext("name") == "Skip empty Zone")
    assert wrapper.findtext("conditionif") == f"ZoneSize({source}) > 0"
    assert wrapper.findtext("executionmode") == "0" and list(wrapper.find("tasks")) == [sequential]
    captures = [task for task in xml.iter() if task.findtext("variablename") == source]
    assert len(captures) == 1 and captures[0].findtext("expressiontext") == "rack"
    for ids in ((), ("27",), ("27", "0", "8")):
        result = Interpreter(program).run(inputs={"rack": Zone(well_ids=ids)})
        assert result.outputs == {"count": len(ids), "last": Zone.empty()}


def test_nested_loops_and_user_counter_names_get_distinct_native_storage():
    class Nested(Function):
        rack: Input[Zone]
        loop: Var[Zone] = Zone.empty()
        fragment: Var[int] = 0

        @runtime
        def run(self) -> None:
            for self.loop in self.rack:
                for self.loop in self.rack:
                    self.fragment += 1

    xml = ET.fromstring(Nested().compile(target=AutoSuiteTarget()).artifact.content)
    loops = [node for node in xml.iter() if node.findtext("executionmode") == "1"]
    assert len(loops) == 2
    iterators = [node.findtext("sequentialzones/sequentialzone0/variablename") for node in loops]
    sources = [node.findtext("sequentialzones/sequentialzone0/zonename") for node in loops]
    assert len(set(iterators + sources)) == 4
    for node in loops:
        assert node.findtext("loopvariable") not in ("loop", "fragment")
        assert node.findtext("fragmentvariable") not in ("loop", "fragment")


def test_unknown_bounds_and_group_divisibility_remain_explicit_target_gates():
    class Index(Function):
        rack: Input[Zone]
        well: Output[Zone]

        @runtime
        def run(self) -> None:
            self.well = self.rack[0]

    class Group(Function):
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()

        @runtime
        def run(self) -> None:
            for self.well in zones.fragments(self.rack, size=2):
                pass

    for cls, code in ((Index, "unsupported_zone_index"), (Group, "unsupported_zone_grouping")):
        with pytest.raises(CompilationError, match=code):
            cls().compile(target=AutoSuiteTarget())


def test_lists_assigned_only_inside_loop_are_not_definite_outputs():
    class Incomplete(Function):
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()
        values: Output[list[int]]

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.values = [1]

    with pytest.raises(CompilationError, match="list_output_initialization"):
        Incomplete().compile(target=AutoSuiteTarget())


def test_timer_start_and_wait_share_sequential_macro_but_cannot_reset_across_scopes():
    class Timed(Function):
        rack: Input[Zone]
        well: Var[Zone] = Zone.empty()
        timer: Timer

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.timer.start()
                self.timer.wait_until(2 * s)

    Timed().compile(target=AutoSuiteTarget())

    class Reset(Timed):
        @runtime
        def run(self) -> None:
            self.timer.start()
            for self.well in self.rack:
                self.timer.start()
                self.timer.wait_until(2 * s)

    with pytest.raises(CompilationError, match="unsupported_timer_scope"):
        Reset().compile(target=AutoSuiteTarget())
