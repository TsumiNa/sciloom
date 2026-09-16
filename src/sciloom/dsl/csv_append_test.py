"""CSV row appends preserve capture, statement order and explicit result binding."""

import pytest

from sciloom import Function, Input, Output, Var, csv, mL, runtime
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import CsvAppendEvent, Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import AppendCsv, from_json, to_json
from sciloom_autosuite import AutoSuiteTarget


class AppendLog(Function):
    path: Input[str]
    label: Input[str]
    status: Output[int]
    count: Var[int] = 4

    @runtime
    def run(self) -> None:
        self.count = csv.try_append_row(self.path, values=(self.label, self.count, 2 * mL))
        self.status = self.count
        self.label = "changed"
        csv.append_row(self.path, values=(self.label,))


def test_append_captures_before_status_write_and_keeps_event_snapshots():
    program = AppendLog().to_ir()
    assert isinstance(program.functions[0].body[0], AppendCsv)
    for candidate in (program, from_json(to_json(program))):
        files = MemoryFiles()
        environment = ReferenceEnvironment(files=files)
        session = Interpreter(candidate, environment=environment)
        result = session.run(inputs={"path": "log.csv", "label": '日本語,"a"'})
        assert result.outputs == {"status": csv.OK}
        assert files.snapshot()["log.csv"] == '"日本語,""a""",4,2e-06\r\nchanged\r\n'.encode()
        event = result.events[0]
        assert isinstance(event, CsvAppendEvent) and event.values == ('日本語,"a"', 4, 2 * mL)
        session.run(inputs={"path": "log.csv", "label": "second"})
        assert len(environment.events) == 4 and len(result.events) == 2
        assert files.snapshot()["log.csv"].endswith(b"second,0,2e-06\r\nchanged\r\n")
    with pytest.raises(CompilationError, match="unsupported_csv_append"):
        AppendLog().compile(target=AutoSuiteTarget())


def test_append_in_child_loop_and_read_back_without_repairing_existing_content():
    class Write(Function):
        count: Var[int] = 0

        @runtime
        def run(self) -> None:
            self.count = 0
            while self.count < 2:
                csv.append_row("rows.csv", values=(self.count,))
                self.count += 1

    class Parent(Function):
        values: Output[list[int]]

        def __init__(self):
            self.write = Write()

        @runtime
        def run(self) -> None:
            self.write()
            (self.values,) = csv.read_columns("rows.csv", header=False, columns=(csv.Column(index=0, value_type=int),))

    files = MemoryFiles({"rows.csv": b"2"})
    session = Interpreter(Parent().to_ir(), environment=ReferenceEnvironment(files=files))
    first = session.run()
    assert first.outputs == {"values": (20, 1)}
    assert files.snapshot()["rows.csv"] == b"20\r\n1\r\n"  # no invented separator before the first append
    assert session.run().outputs == {"values": (20, 1, 0, 1)}
    isolated = Interpreter(Parent().to_ir(), environment=ReferenceEnvironment(files=MemoryFiles()))
    assert isolated.run().outputs == {"values": (0, 1)}
    assert first.outputs == {"values": (20, 1)}


def test_arguments_fail_before_any_file_effect():
    class Invalid(Function):
        index: Input[int]
        values: Input[list[str]]

        @runtime
        def run(self) -> None:
            csv.append_row("log.csv", values=("first", self.values[self.index]))

    files = MemoryFiles()
    environment = ReferenceEnvironment(files=files)
    with pytest.raises(ExecutionError):
        Interpreter(Invalid().to_ir(), environment=environment).run(inputs={"index": 2, "values": ["one"]})
    assert files.snapshot() == {} and environment.events == ()


def test_unsupported_append_shapes_and_types_fail_before_execution():
    class Unbound(Function):
        @runtime
        def run(self) -> None:
            csv.try_append_row("log.csv", values=("one",))

    class BoundVoid(Function):
        status: Output[int]

        @runtime
        def run(self) -> None:
            self.status = csv.append_row("log.csv", values=("one",))

    class Empty(Function):
        @runtime
        def run(self) -> None:
            csv.append_row("log.csv", values=())

    class ListValue(Function):
        values: Input[list[str]]

        @runtime
        def run(self) -> None:
            csv.append_row("log.csv", values=(self.values,))

    class WrongStatus(Function):
        status: Output[bool]

        @runtime
        def run(self) -> None:
            self.status = csv.try_append_row("log.csv", values=("one",))

    class Nested(Function):
        status: Output[int]

        @runtime
        def run(self) -> None:
            self.status = 1 + csv.try_append_row("log.csv", values=("one",))

    class Expanded(Function):
        values = ("one",)

        @runtime
        def run(self) -> None:
            csv.append_row("log.csv", values=(*self.values,))

    for model in (Unbound, BoundVoid, Empty, ListValue, WrongStatus, Nested, Expanded):
        with pytest.raises(IRValidationError):
            model().to_ir()
