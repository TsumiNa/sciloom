"""Property tasks use observed native modes and preserve selection/capture checks."""

import gzip
import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Output, Var, WellProperty, Zone, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import from_json, to_json
from .conftest import corpus_file
from .target import AutoSuiteTarget


class Label(Function):
    rack: Input[Zone]
    text: Input[str]
    well: Var[Zone] = Zone.empty()
    previous: Output[str]

    def __init__(self):
        self.label = WellProperty("sample_ID<&", str)

    @runtime
    def run(self) -> None:
        self.label[self.rack] = self.text
        self.previous = ""
        for self.well in self.rack:
            self.previous = self.label.get(self.well, default=self.text)


def test_native_single_value_write_and_defaulted_read_match_evidence():
    program = Label().to_ir()
    compiled = compile_ir(from_json(to_json(program)), target=AutoSuiteTarget())
    assert compiled.semantic_ir == compiled.specialized_ir == program
    assert Label().compile(target=AutoSuiteTarget()).artifact == compiled.artifact
    xml = ET.fromstring(compiled.artifact.content)
    write = xml.find(".//*[@typeid='Chemspeed.SATaskSetProperty.1']")
    assert [
        (c.tag, c.text or "")
        for c in write
        if c.tag not in {"description", "edittime", "id", "name", "destzonename", "propvalueexprtext"}
    ] == [
        ("propertytype", "2"),
        ("propname", "sample_ID<&"),
        ("valuemode", "0"),
        ("variablename", ""),
        ("resulttype", "text"),
        ("propertyunit", ""),
    ]
    zone, value = write.findtext("destzonename"), write.findtext("propvalueexprtext")
    writes = [n for n in xml.iter() if n.get("typeid") == "Chemspeed.SATaskSetVariable.1"]
    value_capture = next(n for n in writes if n.findtext("variablename") == value)
    zone_capture = next(n for n in writes if n.findtext("variablename") == zone)
    assert value_capture.findtext("expressiontext") == "text"
    assert zone_capture.findtext("expressiontext") == "rack"
    assert writes.index(value_capture) < writes.index(zone_capture)
    assert any(
        n.findtext("conditionif") == f"ZoneSize({zone}) > 0" and n.find("tasks/task") is write for n in xml.iter()
    )
    read = xml.find(".//*[@typeid='Chemspeed.SATaskGetProperty.1']")
    assert read.findtext("userpropertymode") == "2" and read.findtext("fallbackmode") == "1"
    assert read.findtext("propname") == "sample_ID<&" and read.findtext("destvariablename") == "previous"
    source, fallback = read.findtext("sourcezonename"), read.findtext("fallback")
    assert source != "well" and fallback != "text" and source != fallback
    source_capture = next(n for n in writes if n.findtext("variablename") == source)
    fallback_capture = next(n for n in writes if n.findtext("variablename") == fallback)
    assert source_capture.findtext("expressiontext") == "well"
    assert fallback_capture.findtext("expressiontext") == "text"
    assert writes.index(source_capture) < writes.index(fallback_capture)


@pytest.mark.requires_corpus
def test_task_envelopes_and_modes_match_primary_app_and_export():
    app = ET.fromstring(gzip.decompress(corpus_file("app/config20260909_polymerization.app").read_bytes()))
    exported = ET.parse(corpus_file("extracted/latest_app/functions/45_Write Well Log.asfp")).getroot()
    generated = ET.fromstring(Label().compile(target=AutoSuiteTarget()).artifact.content)
    for source, kind, changes in (
        (app, "Set", {"destzonename", "propname", "propvalueexprtext"}),
        (exported, "Get", {"sourcezonename", "propname", "destvariablename", "fallback"}),
    ):
        typeid = f"Chemspeed.SATask{kind}Property.1"
        native = next(
            node
            for node in source.iter()
            if node.get("typeid") == typeid and (kind == "Get" or node.findtext("valuemode") == "0")
        )
        task = generated.find(f".//*[@typeid='{typeid}']")
        assert [c.tag for c in task] == [c.tag for c in native]
        for child in native:
            if child.tag not in changes | {"description", "name", "edittime", "id"}:
                assert (task.findtext(child.tag) or "") == (child.text or "")


def test_strict_or_unproven_read_requires_runtime_failure_evidence():
    class Unproven(Label):
        @runtime
        def run(self) -> None:
            self.previous = self.label.get(self.rack, default="")

    class Strict(Label):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.previous = self.label.get(self.well)

    for model in (Unproven, Strict):
        with pytest.raises(CompilationError, match="unsupported_well_property_read"):
            model().compile(target=AutoSuiteTarget())


def test_single_well_facts_follow_assignments_and_branch_intersection():
    class Safe(Label):
        copy: Var[Zone] = Zone.empty()
        enabled: Input[bool]

        @runtime
        def run(self) -> None:
            self.previous = ""
            for self.well in self.rack:
                if self.enabled:
                    self.copy = self.well
                else:
                    self.copy = self.well
                self.previous = self.label.get(self.copy, default="")

    Safe().compile(target=AutoSuiteTarget())

    class Bad(Safe):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                if self.enabled:
                    self.well = Zone.empty()
                self.previous = self.label.get(self.well, default="")

    with pytest.raises(CompilationError, match="unsupported_well_property_read"):
        Bad().compile(target=AutoSuiteTarget())


def test_loop_mutation_invalidates_facts_on_later_iterations_and_empty_paths():
    class Later(Label):
        copy: Var[Zone] = Zone.empty()
        index: Var[int] = 0

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.copy = self.well
                while self.index < 2:
                    self.previous = self.label.get(self.copy, default="")
                    self.copy = self.rack
                    self.index += 1

    class Empty(Label):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                pass
            self.previous = self.label.get(self.well, default="")

    for model in (Later, Empty):
        with pytest.raises(CompilationError, match="unsupported_well_property_read"):
            model().compile(target=AutoSuiteTarget())


def test_callee_output_and_reused_nested_target_invalidate_single_well():
    class Clear(Function):
        value: Output[Zone]

        @runtime
        def run(self) -> None:
            self.value = Zone.empty()

    class CallOutput(Label):
        def __init__(self):
            super().__init__()
            self.clear = Clear()

        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                self.well = self.clear()
                self.previous = self.label.get(self.well, default="")

    class Nested(Label):
        @runtime
        def run(self) -> None:
            for self.well in self.rack:
                for self.well in self.rack:
                    self.well = Zone.empty()
                self.previous = self.label.get(self.well, default="")

    for model in (CallOutput, Nested):
        with pytest.raises(CompilationError, match="unsupported_well_property_read"):
            model().compile(target=AutoSuiteTarget())
