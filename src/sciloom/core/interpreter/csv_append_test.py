"""One encoded row per append; failed writes never claim a rollback."""

from dataclasses import FrozenInstanceError, replace

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.ir import (
    AppendCsv,
    CsvErrorPolicy,
    FunctionIR,
    ListLiteral,
    ListType,
    Literal,
    LogValue,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from sciloom.core.ir.csv import IO_ERROR, OK
from sciloom.core.specialization import specialize
from sciloom.units import mL
from sciloom_autosuite import AutoSuiteTarget
from .environment import CsvAppendEvent, ReferenceEnvironment
from .files import LocalFiles, MemoryFiles
from .runtime import Interpreter


def append_program(*, status=False):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Append",
                variables=(
                    Variable(
                        node_id="status", owner_id="f", name="status", role=VariableRole.OUTPUT, type=ScalarType.INTEGER
                    ),
                )
                if status
                else (),
                body=(
                    AppendCsv(
                        node_id="append",
                        path=Literal(node_id="path", type=ScalarType.TEXT, value="log.csv"),
                        values=(
                            Literal(node_id="text", type=ScalarType.TEXT, value='A,"quoted"\nnext'),
                            Literal(node_id="volume", type=ScalarType.VOLUME, value=2e-6),
                            Literal(node_id="flag", type=ScalarType.BOOLEAN, value=True),
                        ),
                        error_policy=CsvErrorPolicy.STATUS if status else CsvErrorPolicy.RAISE,
                        status=Reference(node_id="result", symbol_id="status") if status else None,
                    ),
                ),
            ),
        ),
    )


def test_direct_json_specialization_append_bytes_and_immutable_events():
    program = append_program(status=True)
    canonical = to_json(program)
    for candidate in (program, from_json(canonical), specialize(program, bindings=DeviceBindings())):
        files = MemoryFiles()
        environment = ReferenceEnvironment(files=files)
        session = Interpreter(candidate, environment=environment)
        first = session.run()
        assert first.outputs == {"status": OK}
        expected = b'"A,""quoted""\nnext",2e-06,true\r\n'
        assert files.read_bytes("log.csv") == expected
        prior = files.snapshot()
        session.run()
        assert files.read_bytes("log.csv") == expected * 2
        assert prior["log.csv"] == expected
        (event,) = first.events
        assert isinstance(event, CsvAppendEvent)
        assert event.values == ('A,"quoted"\nnext', 2 * mL, True)
        assert event.status == OK
        with pytest.raises(FrozenInstanceError):
            event.status = IO_ERROR
    assert to_json(program) == canonical
    with pytest.raises(CompilationError, match="unsupported_csv_append"):
        compile_ir(program, target=AutoSuiteTarget())


@pytest.mark.parametrize("status", [False, True])
def test_partial_write_keeps_bytes_and_only_try_append_continues(status):
    class PartialFiles(MemoryFiles):
        attempts = 0

        def append_bytes(self, path, data):
            self.attempts += 1
            super().append_bytes(path, data[:3])
            raise OSError("disk failure after a prefix")

    program = append_program(status=status)
    function = program.functions[0]
    after = LogValue(
        node_id="after",
        value=Literal(node_id="message", type=ScalarType.TEXT, value="continued"),
        category=Literal(node_id="cat", type=ScalarType.TEXT, value="test"),
        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="status"),
    )
    program = replace(program, functions=(replace(function, body=(*function.body, after)),))
    files = PartialFiles({"log.csv": b"old\r\n"})
    environment = ReferenceEnvironment(files=files)
    session = Interpreter(program, environment=environment)
    if status:
        assert session.run().outputs == {"status": IO_ERROR}
        assert len(environment.events) == 2
    else:
        with pytest.raises(ExecutionError, match="csv_io_error"):
            session.run()
        assert len(environment.events) == 1
    assert environment.events[0].status == IO_ERROR
    assert files.read_bytes("log.csv") == b'old\r\n"A,'
    assert files.attempts == 1


@pytest.mark.parametrize("failure", [ValueError("bug"), TypeError("bug"), RuntimeError("bug"), 1])
def test_provider_faults_are_fatal_even_in_try_form(failure):
    class FaultyFiles:
        def append_bytes(self, path, data):
            if isinstance(failure, Exception):
                raise failure
            return failure

    environment = ReferenceEnvironment(files=FaultyFiles())
    with pytest.raises(ExecutionError, match="file_service_error"):
        Interpreter(append_program(status=True), environment=environment).run()
    assert environment.events == ()


def test_missing_service_and_invalid_encoding_precede_file_effects():
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(append_program()).run()
    program = append_program()
    function = program.functions[0]
    append = function.body[0]
    append = replace(append, values=(replace(append.values[0], value="\ud800"),))
    files = MemoryFiles()
    environment = ReferenceEnvironment(files=files)
    with pytest.raises(ExecutionError, match="csv_encoding"):
        Interpreter(replace(program, functions=(replace(function, body=(append,)),)), environment=environment).run()
    assert files.snapshot() == {} and environment.events == ()


def test_explicit_local_files_do_not_create_parent_directories(tmp_path):
    program = append_program(status=True)
    function = program.functions[0]
    append = function.body[0]
    for path, code in (("nested/log.csv", None), ("../log.csv", "csv_path")):
        candidate = replace(
            program, functions=(replace(function, body=(replace(append, path=replace(append.path, value=path)),)),)
        )
        environment = ReferenceEnvironment(files=LocalFiles(tmp_path))
        if code:
            with pytest.raises(ExecutionError, match=code):
                Interpreter(candidate, environment=environment).run()
            assert environment.events == ()
        else:
            assert Interpreter(candidate, environment=environment).run().outputs == {"status": IO_ERROR}
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", ["empty", "list", "path", "missing_status", "extra_status", "wrong_status"])
def test_append_structure_and_binding_rules(change):
    program = append_program(status=True)
    function = program.functions[0]
    append = function.body[0]
    if change == "empty":
        append = replace(append, values=())
    elif change == "list":
        append = replace(
            append,
            values=(
                ListLiteral(node_id="list", type=ListType(element_type=ScalarType.TEXT), elements=(append.values[0],)),
            ),
        )
    elif change == "path":
        append = replace(append, path=replace(append.path, type=ScalarType.INTEGER, value=1))
    elif change == "missing_status":
        append = replace(append, status=None)
    elif change == "extra_status":
        append = replace(append, error_policy=CsvErrorPolicy.RAISE)
    else:
        function = replace(function, variables=(replace(function.variables[0], type=ScalarType.REAL),))
    candidate = replace(program, functions=(replace(function, body=(append,)),))
    with pytest.raises(IRValidationError):
        to_json(candidate)
