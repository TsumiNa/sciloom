"""Clock-read task scheduling and corpus mapping, not vendor clock execution."""

import ast
import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Output, Var, now_text, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import from_json, to_json
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .target import AutoSuiteTarget


class Stamp(Function):
    stamp: Output[str]

    @runtime
    def run(self) -> None:
        self.stamp = now_text("%Y-%m-%d_%H%M%S")


class ClockWire(WireModel):
    """Supply distinct clock results to test scheduling, assuming DateTime semantics."""

    def __init__(self, content):
        super().__init__(content)
        self.formats = []

    def expression(self, text, frame):
        if text.startswith("DateTime("):
            self.formats.append(ast.literal_eval(text[len("DateTime(") : -1]))
            return f"read{len(self.formats)}"
        return super().expression(text, frame)


def test_reads_in_child_calls_and_loops_are_not_duplicated_by_later_use():
    class Caller(Function):
        stamp: Output[str]
        path: Output[str]
        index: Var[int] = 0

        def __init__(self):
            self.child = Stamp()

        @runtime
        def run(self) -> None:
            self.index = 0
            while self.index < 2:
                self.stamp = self.child()
                self.path = self.stamp + "/" + self.stamp
                self.index += 1

    authored = Caller().to_ir()
    before = to_json(authored)
    for program in (authored, from_json(before)):
        compiled = compile_ir(program, target=AutoSuiteTarget())
        wire = ClockWire(compiled.artifact.content)
        assert wire.run() == {"stamp": "read2", "path": "read2/read2"}
        assert wire.formats == ["%Y-%m-%d_%H%M%S"] * 2
        assert len([e for e in wire.root.iter("expressiontext") if "DateTime(" in e.text]) == 1
        assert compiled.specialized_ir == program
    assert to_json(authored) == before


def test_clock_format_uses_text_expression_encoding_then_xml_escaping():
    class Escaped(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = now_text("試料 & < '%Y'\\\n%%")

    content = Escaped().compile(target=AutoSuiteTarget()).artifact.content
    expression = ET.fromstring(content).findtext(".//expressiontext")
    assert expression.startswith("DateTime(")
    assert "Char(39)" in expression and "Char(92)" in expression and "Char(10)" in expression
    assert "試料 & < " in expression
    assert b"&amp;" in content and b"&lt;" in content


def test_unrepresentable_format_reports_the_clock_source():
    class Bad(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = now_text("a\0b")

    with pytest.raises(CompilationError) as error:
        Bad().compile(target=AutoSuiteTarget())
    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == "unsupported_text_literal"
    assert diagnostic.source.path == __file__


@pytest.mark.requires_corpus
def test_set_variable_clock_task_matches_native_timestamp_function():
    native = ET.parse(corpus_file("extracted/latest_app/functions/15_util Get Time Stamp.asfp")).find(
        ".//*[@typeid='Chemspeed.SATaskSetVariable.1']"
    )
    generated = ET.fromstring(Stamp().compile(target=AutoSuiteTarget()).artifact.content).find(
        ".//*[@typeid='Chemspeed.SATaskSetVariable.1']"
    )
    assert [c.tag for c in generated] == [c.tag for c in native]
    for child in native:
        if child.tag not in {"id", "edittime", "variablename", "description", "name"}:
            assert generated.findtext(child.tag) == (child.text or "")
