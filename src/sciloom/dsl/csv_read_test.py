"""CSV syntax preserves typed columns, runtime selectors and atomic results."""

import pytest

from sciloom import Function, Input, Output, Var, Volume, csv, mL, runtime
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import ReadCsv, from_json, to_json
from sciloom_autosuite import AutoSuiteTarget


class ReadRecipe(Function):
    path: Input[str]
    reagent_index: Input[int]
    ids: Output[list[str]]
    volumes: Output[list[Volume]]
    status: Output[int]
    used_default: Output[bool]

    @runtime
    def run(self) -> None:
        self.status, self.ids, self.volumes = csv.try_read_columns(
            self.path,
            header=True,
            columns=(
                csv.Column(index=0, value_type=str, default="missing"),
                csv.Column(index=self.reagent_index + 1, value_type=Volume, unit=mL, default=0 * mL),
            ),
        )
        self.used_default = self.status == csv.DEFAULT_USED


def test_dsl_json_dynamic_column_and_named_status_agree():
    program = ReadRecipe().to_ir()
    assert isinstance(program.functions[0].body[0], ReadCsv)
    for candidate in (program, from_json(to_json(program))):
        files = MemoryFiles({"recipe.csv": b"id,A,B\nfirst,1,2\nsecond,3,\n"})
        result = Interpreter(candidate, environment=ReferenceEnvironment(files=files)).run(
            inputs={"path": "recipe.csv", "reagent_index": 1}
        )
        assert result.outputs == {
            "status": csv.DEFAULT_USED,
            "ids": ("first", "second"),
            "volumes": (2 * mL, 0 * mL),
            "used_default": True,
        }
    with pytest.raises(CompilationError, match="unsupported_csv_semantics"):
        ReadRecipe().compile(target=AutoSuiteTarget())


def test_single_column_tuple_child_call_and_independent_list_values():
    class Read(Function):
        values: Output[list[int]]

        @runtime
        def run(self) -> None:
            (self.values,) = csv.read_columns("data.csv", header=False, columns=(csv.Column(index=0, value_type=int),))

    class Parent(Function):
        first: Output[list[int]]
        second: Output[list[int]]

        def __init__(self):
            self.read = Read()

        @runtime
        def run(self) -> None:
            self.first = self.read()
            self.second = self.first
            self.second[0] = 9

    environment = ReferenceEnvironment(files=MemoryFiles({"data.csv": b"1\n2\n"}))
    result = Interpreter(Parent().to_ir(), environment=environment).run()
    assert result.outputs == {"first": (1, 2), "second": (9, 2)}


def test_runtime_row_and_default_are_captured_before_output_overwrite():
    class Row(Function):
        row: Input[int]
        default: Input[str]
        status: Output[int]

        @runtime
        def run(self) -> None:
            self.status, self.default = csv.try_read_row(
                "data.csv",
                row=self.row,
                header=False,
                columns=(csv.Column(index=1, value_type=str, default=self.default),),
            )

    environment = ReferenceEnvironment(files=MemoryFiles({"data.csv": b"a,b\nc\n"}))
    session = Interpreter(Row().to_ir(), environment=environment)
    assert session.run(inputs={"row": 1, "default": "fallback"}).outputs == {"status": csv.DEFAULT_USED}
    assert environment.events[-1].row == 1
    with pytest.raises(ExecutionError, match="csv_index"):
        session.run(inputs={"row": -1, "default": "fallback"})
    assert len(environment.events) == 1


def test_csv_syntax_rejects_incomplete_bindings_and_runtime_metadata():
    class NoTuple(Function):
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = csv.read_row("a", row=0, header=False, columns=(csv.Column(index=0, value_type=str),))

    class Duplicate(Function):
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result, self.result = csv.read_row(
                "a",
                row=0,
                header=False,
                columns=(csv.Column(index=0, value_type=str), csv.Column(index=1, value_type=str)),
            )

    class RuntimeHeader(Function):
        header: Input[bool]
        result: Output[str]

        @runtime
        def run(self) -> None:
            (self.result,) = csv.read_row(
                "a", row=0, header=self.header, columns=(csv.Column(index=0, value_type=str),)
            )

    class MissingDefault(Function):
        result: Output[str]
        status: Output[int]

        @runtime
        def run(self) -> None:
            self.status, self.result = csv.try_read_row(
                "a", row=0, header=False, columns=(csv.Column(index=0, value_type=str),)
            )

    class WrongUnit(Function):
        result: Output[Volume]

        @runtime
        def run(self) -> None:
            (self.result,) = csv.read_row("a", row=0, header=False, columns=(csv.Column(index=0, value_type=Volume),))

    class Nested(Function):
        result: Var[int] = 0

        @runtime
        def run(self) -> None:
            self.result = len(csv.read_columns("a", header=False, columns=(csv.Column(index=0, value_type=str),)))

    class ObjectColumn(Function):
        result: Output[str]

        @runtime
        def run(self) -> None:
            (self.result,) = csv.read_row("a", row=0, header=False, columns=(csv.Column(index=0, value_type=object),))

    for model, code in (
        (NoTuple, "csv_binding"),
        (Duplicate, "csv_binding"),
        (RuntimeHeader, "csv_metadata"),
        (MissingDefault, "csv_default"),
        (WrongUnit, "csv_unit"),
        (Nested, "python_subset"),
        (ObjectColumn, "csv_columns"),
    ):
        with pytest.raises(IRValidationError, match=code):
            model().to_ir()
