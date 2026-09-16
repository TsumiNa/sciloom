"""Static Zone XML mapping; these tests do not execute the AutoSuite parser."""

import xml.etree.ElementTree as ET

import pytest

from examples.resolve_locations import ResolveLocations
from sciloom import Function, Input, Output, Var, Zone, runtime, zones
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import from_json, to_json
from .target import AutoSuiteTarget


def test_zone_defaults_parameters_and_native_queries():
    function = ResolveLocations()
    program = function.to_ir()
    baseline = to_json(program)
    compiled = compile_ir(from_json(baseline), target=AutoSuiteTarget())
    xml = ET.fromstring(compiled.artifact.content)
    selected = xml.find(".//outputs/item0")
    assert selected.findtext("variabletype") == "zone"
    assert selected.findtext("isarray") == "0"
    first = next(v for v in xml.findall(".//variable") if v.findtext("name") == "first")
    assert [first.findtext(p) for p in ("value/type", "value/value", "siunit", "unit", "array")] == [
        "8",
        "",
        "zone",
        "zone",
        "0",
    ]
    expressions = [e.text for e in xml.findall(".//expressiontext")]
    assert "FindZone(first_name)" in expressions
    assert "(first + FindZone(second_name))" in expressions
    assert "ZoneSize(selected)" in expressions
    assert to_json(compiled.semantic_ir) == baseline
    assert function.compile(target=AutoSuiteTarget()).artifact == compiled.artifact


def test_zone_calls_bind_expressions_and_empty_literal_uses_private_storage():
    class Echo(Function):
        location: Input[Zone]
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            self.result = self.location
            self.location = Zone.empty()

    class Caller(Function):
        location: Input[Zone]
        result: Output[Zone]

        def __init__(self):
            self.echo = Echo()

        @runtime
        def run(self) -> None:
            self.result = self.echo(location=self.location)

    xml = ET.fromstring(Caller().compile(target=AutoSuiteTarget()).artifact.content)
    parameters = xml.find(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']/functiondata")
    incoming = parameters.find("inputs/item0")
    outgoing = parameters.find("outputs/item0")
    assert incoming.findtext("variabletype") == outgoing.findtext("variabletype") == "zone"
    assert incoming.findtext("isarray") == "0"
    assert incoming.findtext("expression") == "location"
    assert not incoming.findtext("variablename")
    assert outgoing.findtext("variablename") == "result"
    empty = next(v for v in xml.findall(".//variable") if v.findtext("name").startswith("sciloom_tmp_"))
    empty_name = empty.findtext("name")
    assert empty.findtext("siunit") == "zone" and empty.findtext("value/value") == ""
    assert empty_name in [e.text for e in xml.findall(".//expressiontext")]
    # The expression source stays empty across calls: no task ever writes it.
    assert empty_name not in [e.text for e in xml.findall(".//variablename")]


def test_nonempty_literals_and_unproven_well_name_fail_explicitly():
    class Nonempty(Function):
        saved: Var[Zone] = Zone(well_ids=("opaque:27",))

        @runtime
        def run(self) -> None:
            self.saved = Zone.empty()

    class Label(Function):
        selection: Input[Zone]
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = zones.well_name(self.selection)

    for cls, code in ((Nonempty, "unsupported_zone_literal"), (Label, "unsupported_zone_cardinality")):
        with pytest.raises(CompilationError, match=code):
            cls().compile(target=AutoSuiteTarget())
