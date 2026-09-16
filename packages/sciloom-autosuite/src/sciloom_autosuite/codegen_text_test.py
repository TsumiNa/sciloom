"""Text wire mappings are static evidence, not Executor equivalence checks."""

import ast
import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Output, Var, runtime, text
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import Literal, ScalarType
from .encoding import literal_value
from .target import AutoSuiteTarget


@pytest.mark.parametrize("value", ["", "A & B < C", "'quote'", '"double"', "a\\b", "a\r\nb\tc", "試料🧪"])
def test_literal_mapping_preserves_codepoints(value):
    expression = literal_value(Literal(node_id="literal", type=ScalarType.TEXT, value=value))

    def read(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return read(node.left) + read(node.right)
        assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Char"
        assert len(node.args) == 1 and 1 <= node.args[0].value <= 255
        return chr(node.args[0].value)

    # Evaluate only quoted runs, concatenation and the documented Char mapping.
    # This models the emitted expression; it is not running the vendor parser.
    assert read(ast.parse(expression, mode="eval").body) == value
    element = ET.Element("expressiontext")
    element.text = expression
    assert ET.fromstring(ET.tostring(element)).text == expression


@pytest.mark.parametrize("value", ["a\0b", "\ud800", "\uffff"])
def test_unrepresentable_literal_is_target_diagnostic(value):
    class Bad(Function):
        result: Output[str]

        def __init__(self):
            self.value = value

        @runtime
        def run(self) -> None:
            self.result = self.value

    with pytest.raises(CompilationError, match="unsupported_text_literal"):
        Bad().compile(target=AutoSuiteTarget())


class Labels(Function):
    name: Input[str]
    result: Output[list[str]]
    size: Output[int]
    empty: Output[bool]
    label: Var[str] = ""
    defaults: Var[list[str]] = ["A", "B"]

    @runtime
    def run(self) -> None:
        self.label = text.trim(self.name)
        self.label = text.split_part(self.label, ",", 0) + "_processed"
        self.result = [self.label, "O'Reilly\\A\n"]
        self.size = len("ready")
        self.empty = self.name == ""


def test_text_parameters_initial_values_and_intrinsics():
    xml = ET.fromstring(Labels().compile(target=AutoSuiteTarget()).artifact.content)
    assert xml.findtext(".//inputs/item0/variabletype") == "text"
    assert xml.findtext(".//outputs/item0/variabletype") == "text"
    assert xml.findtext(".//outputs/item0/isarray") == "1"
    declarations = {v.findtext("name"): v for v in xml.findall(".//variable")}
    label = declarations["label"]
    assert [label.findtext(p) for p in ("value/type", "value/value", "siunit", "unit")] == ["8", "''", "text", "K/s"]
    assert declarations["defaults"].findtext("values/value0/value") == "'A'"
    expressions = [e.text for e in xml.findall(".//expressiontext")]
    assert "TrimText(name)" in expressions
    assert "SplitTextAndGet(label, ',', 0) + '_processed'" in expressions
    assert "TextLength('ready')" in expressions
    assert "name = ''" in expressions
    assert any("Char(39)" in e and "Char(92)" in e and "Char(10)" in e for e in expressions)


def test_text_array_call_uses_private_copy_binding():
    class Echo(Function):
        values: Input[list[str]]
        result: Output[list[str]]

        @runtime
        def run(self) -> None:
            self.result = self.values

    class Caller(Function):
        values: Input[list[str]]
        result: Output[list[str]]

        def __init__(self):
            self.echo = Echo()

        @runtime
        def run(self) -> None:
            self.result = self.echo(values=self.values)

    xml = ET.fromstring(Caller().compile(target=AutoSuiteTarget()).artifact.content)
    binding = xml.find(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']/functiondata/inputs/item0")
    assert binding.findtext("variabletype") == "text"
    assert binding.findtext("isarray") == "1"
    assert binding.findtext("variablename").startswith("sciloom_tmp_")
    assert not binding.findtext("expression")


def test_unknown_split_selectors_are_not_silently_delegated():
    class Dynamic(Function):
        delimiter: Input[str]
        index: Input[int]
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = text.split_part("a,b", self.delimiter, self.index)

    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        Dynamic().compile(target=AutoSuiteTarget())


def test_runtime_unicode_length_is_not_assumed_equivalent():
    class Length(Function):
        value: Input[str]
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = len(self.value)

    with pytest.raises(CompilationError, match="unsupported_text_length"):
        Length().compile(target=AutoSuiteTarget())


def test_non_bmp_literal_length_is_not_assumed_equivalent():
    class Length(Function):
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = len("🧪")

    with pytest.raises(CompilationError, match="unsupported_text_length"):
        Length().compile(target=AutoSuiteTarget())


@pytest.mark.parametrize("delimiter,index", [("", 0), (",", -1)])
def test_invalid_literal_split_selectors_are_rejected(delimiter, index):
    class Split(Function):
        result: Output[str]

        def __init__(self):
            self.delimiter = delimiter
            self.index = index

        @runtime
        def run(self) -> None:
            self.result = text.split_part("a,b", self.delimiter, self.index)

    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        Split().compile(target=AutoSuiteTarget())


def test_text_index_guards_require_the_failure_gate():
    class Read(Function):
        values: Input[list[str]]
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = self.values[0]

    class Write(Function):
        values: Input[list[str]]

        @runtime
        def run(self) -> None:
            self.values[0] = "new"

    for cls in (Read, Write):
        with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
            cls().compile(target=AutoSuiteTarget())
