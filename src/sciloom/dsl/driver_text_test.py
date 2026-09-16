"""Runtime text is typed data; its intrinsic calls never execute host code."""

from types import SimpleNamespace

import pytest

from sciloom import Function, Input, Output, Var, runtime, text
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json


class TextParts(Function):
    value: Input[str]
    delimiter: Input[str]
    index: Input[int]
    cleaned: Output[str]
    part: Output[str]
    length: Output[int]
    equal: Output[bool]

    @runtime
    def run(self) -> None:
        self.cleaned = text.trim(self.value)
        self.part = text.split_part(self.cleaned, delimiter=self.delimiter, index=self.index)
        self.length = len(self.part)
        self.equal = self.part == "b"


@pytest.mark.parametrize(
    "value,delimiter,index,cleaned,part",
    [
        (" \ta,,b\r\n", ",", 1, "a,,b", ""),
        (" a,,b ", ",", 2, "a,,b", "b"),
        ("a,,b", ",", 7, "a,,b", ""),
        ("", ",", 0, "", ""),
        ("a;;b;;;;c;;;d", ";;", 4, "a;;b;;;;c;;;d", ";d"),
        (" \U0001f9ea試料\n", ",", 0, "\U0001f9ea試料", "\U0001f9ea試料"),
        ("\u00a0 A \u00a0", ",", 0, "\u00a0 A \u00a0", "\u00a0 A \u00a0"),
        (" 'a'\\b\"\n", ",", 0, "'a'\\b\"", "'a'\\b\""),
    ],
)
def test_text_python_and_json(value, delimiter, index, cleaned, part):
    program = TextParts().to_ir()
    for candidate in (program, from_json(to_json(program))):
        result = Interpreter(candidate).run(inputs={"value": value, "delimiter": delimiter, "index": index})
        assert result.outputs == {"cleaned": cleaned, "part": part, "length": len(part), "equal": part == "b"}


@pytest.mark.parametrize("delimiter,index,code", [("", 0, "text_delimiter"), (",", -1, "index_bounds")])
def test_split_invalid_runtime_arguments(delimiter, index, code):
    with pytest.raises(ExecutionError) as error:
        Interpreter(TextParts().to_ir()).run(inputs={"value": "a", "delimiter": delimiter, "index": index})
    assert error.value.diagnostics[0].code == code


def test_text_list_copy_and_state():
    class Copy(Function):
        values: Input[list[str]]
        result: Output[list[str]]

        @runtime
        def run(self) -> None:
            self.result = self.values
            self.result[0] += "!"

    class Caller(Function):
        words: Var[list[str]] = ["A", "B"]
        output: Output[list[str]]

        def __init__(self):
            self.copy = Copy()

        @runtime
        def run(self) -> None:
            self.output = self.copy(values=self.words)
            self.words[0] += "x"

    instance = Caller()
    first = Interpreter(instance.to_ir())
    old = first.run()
    assert old.outputs["output"] == ("A!", "B")
    assert first.run().outputs["output"] == ("Ax!", "B")
    assert old.outputs["output"] == ("A!", "B")
    assert Interpreter(instance.to_ir()).run().outputs["output"] == ("A!", "B")
    assert Interpreter(Caller().to_ir()).run().outputs["output"] == ("A!", "B")


def test_empty_text_defaults_and_lists():
    class Empty(Function):
        words: Var[list[str]] = []
        value: Var[str] = ""
        result: Output[list[str]]

        @runtime
        def run(self) -> None:
            self.result = self.words

    assert Interpreter(Empty().to_ir()).run().outputs["result"] == ()


def test_text_defaults_require_text_values():
    with pytest.raises(IRValidationError, match="class_schema"):

        class BadText(Function):
            value: Var[str] = 1

    with pytest.raises(IRValidationError, match="class_schema"):

        class MixedList(Function):
            values: Var[list[str]] = ["a", 1]

    with pytest.raises(IRValidationError, match="class_schema"):

        class MissingDefault(Function):
            value: Var[str]


def test_intrinsic_alias_and_host_guard():
    trim = text.trim

    class Aliased(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = trim(value=" A ")

    assert Interpreter(Aliased().to_ir()).run().outputs["value"] == "A"
    with pytest.raises(TypeError):
        trim(" A ")
    with pytest.raises(TypeError):
        text.split_part("a", ",", 0)


def test_similarly_named_call_does_not_execute():
    def forbidden(*args, **kwargs):
        raise AssertionError("Must never run.")

    fake = SimpleNamespace(trim=forbidden)

    class Bad(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = fake.trim("a")

    with pytest.raises(IRValidationError, match="python_subset"):
        Bad().to_ir()


def test_text_rejects_boolean_selector_and_implicit_coercions():
    class BadIndex(Function):
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = text.split_part("a", ",", True)

    class BadAdd(Function):
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = "a" + 1

    class BadCondition(Function):
        value: Input[str]

        @runtime
        def run(self) -> None:
            if self.value:
                self.value = "a"

    for cls, code in ((BadIndex, "index_type"), (BadAdd, "operator_type"), (BadCondition, "condition_type")):
        with pytest.raises(IRValidationError, match=code):
            cls().to_ir()
