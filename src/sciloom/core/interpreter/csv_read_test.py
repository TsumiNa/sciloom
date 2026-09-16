"""CSV selectors, typed conversion, fallback policies and whole-operation results."""

from dataclasses import replace

import pytest

from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.ir import (
    CsvColumn,
    CsvErrorPolicy,
    CsvReadMode,
    FunctionIR,
    ListType,
    Literal,
    LogValue,
    Program,
    ReadCsv,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from sciloom.core.ir.csv import DEFAULT_USED, EOF, INVALID_DATA, IO_ERROR, OK
from sciloom.units import mL, rpm, s
from .environment import CsvReadEvent, ReferenceEnvironment
from .files import MemoryFiles
from .runtime import Interpreter


def recipe_program(*, mode=CsvReadMode.COLUMNS, policy=CsvErrorPolicy.RAISE, row=0, header=True):
    columns = (
        CsvColumn(
            index=Literal(node_id="index0", type=ScalarType.INTEGER, value=0),
            type=ScalarType.TEXT,
            default=Literal(node_id="default0", type=ScalarType.TEXT, value="missing"),
        ),
        CsvColumn(
            index=Literal(node_id="index1", type=ScalarType.INTEGER, value=1),
            type=ScalarType.VOLUME,
            unit=Literal(node_id="unit", type=ScalarType.VOLUME, value=1e-6),
            default=Literal(node_id="default1", type=ScalarType.VOLUME, value=0.0),
        ),
    )
    result_types = [ListType(element_type=c.type) if mode == CsvReadMode.COLUMNS else c.type for c in columns]
    if policy == CsvErrorPolicy.STATUS:
        result_types.insert(0, ScalarType.INTEGER)
    variables = tuple(
        Variable(node_id=f"v{i}", name=f"value{i}", owner_id="f", role=VariableRole.OUTPUT, type=value_type)
        for i, value_type in enumerate(result_types)
    )
    read = ReadCsv(
        node_id="read",
        mode=mode,
        error_policy=policy,
        path=Literal(node_id="path", type=ScalarType.TEXT, value="recipe.csv"),
        header=header,
        row=Literal(node_id="row", type=ScalarType.INTEGER, value=row) if mode == CsvReadMode.ROW else None,
        columns=columns,
        targets=tuple(Reference(node_id=f"r{i}", symbol_id=v.node_id) for i, v in enumerate(variables)),
    )
    return Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="Read", variables=variables, body=(read,)),)
    )


def test_typed_columns_and_defaulted_volume_preserve_alignment_and_snapshots():
    program = recipe_program(policy=CsvErrorPolicy.STATUS)
    before = to_json(program)
    for candidate in (program, from_json(before)):
        files = MemoryFiles({"recipe.csv": b"id,volume\nA,1.5\nB,\n"})
        environment = ReferenceEnvironment(files=files)
        session = Interpreter(candidate, environment=environment)
        result = session.run()
        assert result.outputs == {"value0": DEFAULT_USED, "value1": ("A", "B"), "value2": (1.5 * mL, 0 * mL)}
        event = result.events[0]
        assert isinstance(event, CsvReadEvent) and event.columns == (0, 1) and event.row is None
        assert event.status == DEFAULT_USED
        files.append_bytes("recipe.csv", b"C,2\n")
        assert session.run().outputs["value1"] == ("A", "B", "C")
        assert result.outputs["value1"] == ("A", "B")
    assert to_json(program) == before


@pytest.mark.parametrize("data", [b"", b"id,volume\n"])
def test_empty_columns_succeed_but_selected_row_reports_eof(data):
    files = MemoryFiles({"recipe.csv": data})
    columns = Interpreter(
        recipe_program(policy=CsvErrorPolicy.STATUS), environment=ReferenceEnvironment(files=files)
    ).run()
    assert columns.outputs == {"value0": OK, "value1": (), "value2": ()}
    row = Interpreter(
        recipe_program(mode=CsvReadMode.ROW, policy=CsvErrorPolicy.STATUS),
        environment=ReferenceEnvironment(files=files),
    ).run()
    assert row.outputs == {"value0": EOF, "value1": "missing", "value2": 0 * mL}


@pytest.mark.parametrize("mode", [CsvReadMode.ROW, CsvReadMode.COLUMNS])
@pytest.mark.parametrize("data,status", [(None, IO_ERROR), (b'"unfinished', INVALID_DATA), (b"\xff", INVALID_DATA)])
def test_try_read_whole_operation_failures_have_complete_fallbacks(mode, data, status):
    files = MemoryFiles({} if data is None else {"recipe.csv": data})
    environment = ReferenceEnvironment(files=files)
    result = Interpreter(recipe_program(mode=mode, policy=CsvErrorPolicy.STATUS), environment=environment).run()
    expected = ("missing", 0 * mL) if mode == CsvReadMode.ROW else ((), ())
    assert result.outputs == {"value0": status, "value1": expected[0], "value2": expected[1]}
    assert environment.events[-1].status == status


def test_row_selection_is_zero_based_after_header_and_captures_once():
    class CountingFiles(MemoryFiles):
        reads = 0

        def read_bytes(self, path):
            self.reads += 1
            return super().read_bytes(path)

    files = CountingFiles({"recipe.csv": b'id,volume\nA,1\n"B, quoted",2\n"unclosed'})
    result = Interpreter(
        recipe_program(mode=CsvReadMode.ROW, row=1), environment=ReferenceEnvironment(files=files)
    ).run()
    assert result.outputs == {"value0": "B, quoted", "value1": 2 * mL}
    assert files.reads == 1


def test_unhandled_bad_column_discards_all_lists_even_after_a_default_was_used():
    program = recipe_program(policy=CsvErrorPolicy.STATUS)
    function = program.functions[0]
    read = function.body[0]
    columns = (
        replace(read.columns[0], index=replace(read.columns[0].index, value=9)),
        replace(read.columns[1], default=None),
    )
    program = replace(program, functions=(replace(function, body=(replace(read, columns=columns),)),))
    result = Interpreter(
        program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": b"id,v\nA,not-a-number\n"}))
    ).run()
    assert result.outputs == {"value0": INVALID_DATA, "value1": (), "value2": ()}


@pytest.mark.parametrize("failure", ["bad_cell", "destination_widening"])
def test_ordinary_failure_preserves_destinations_and_records_outcome_before_stopping(failure):
    program = recipe_program(mode=CsvReadMode.ROW)
    function = program.functions[0]
    read = function.body[0]
    variables = (
        replace(
            function.variables[0],
            role=VariableRole.INTERNAL,
            initial=Literal(node_id="initial0", type=ScalarType.TEXT, value="old"),
        ),
        replace(
            function.variables[1],
            role=VariableRole.INTERNAL,
            initial=Literal(node_id="initial1", type=ScalarType.VOLUME, value=7e-6),
        ),
    )
    before = LogValue(
        node_id="before",
        value=Reference(node_id="before-read", symbol_id="v0"),
        category=Literal(node_id="cat", type=ScalarType.TEXT, value="recipe"),
        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="before"),
    )
    after = replace(
        before,
        node_id="after",
        value=replace(before.value, node_id="after-read"),
        category=replace(before.category, node_id="after-cat"),
        stream=replace(before.stream, node_id="after-stream"),
    )
    read = replace(read, columns=(read.columns[0], replace(read.columns[1], default=None)))
    data = b"id,v\nnew,invalid\n"
    code = "csv_invalid_data"
    status = INVALID_DATA
    if failure == "destination_widening":
        variables = (
            variables[0],
            replace(
                variables[1],
                type=ScalarType.REAL,
                initial=replace(variables[1].initial, type=ScalarType.REAL, value=7.0),
            ),
        )
        read = replace(read, columns=(read.columns[0], replace(read.columns[1], type=ScalarType.INTEGER, unit=None)))
        data = ("id,v\nnew," + "9" * 400 + "\n").encode()
        code = "numeric_error"
        status = OK
    program = replace(program, functions=(replace(function, variables=variables, body=(before, read, after)),))
    environment = ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data}))
    session = Interpreter(program, environment=environment)
    for _ in range(2):
        with pytest.raises(ExecutionError, match=code):
            session.run()
    assert [getattr(event, "value", None) for event in environment.events] == ["old", None, "old", None]
    assert [event.status for event in environment.events if isinstance(event, CsvReadEvent)] == [status] * 2


def test_no_default_filesystem_and_invalid_selectors_fail_before_a_read_event():
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(recipe_program()).run()
    with pytest.raises(IRValidationError, match="csv_index"):
        Interpreter(recipe_program(mode=CsvReadMode.ROW, row=-1))


@pytest.mark.parametrize("value", [bytearray(b"data"), RuntimeError("provider failed")])
def test_invalid_file_provider_is_not_disguised_as_recoverable_io_status(value):
    class BadFiles:
        def read_bytes(self, path):
            if isinstance(value, Exception):
                raise value
            return value

    environment = ReferenceEnvironment(files=BadFiles())
    with pytest.raises(ExecutionError, match="file_service_error"):
        Interpreter(recipe_program(policy=CsvErrorPolicy.STATUS), environment=environment).run()
    assert environment.events == ()


@pytest.mark.parametrize(
    "scalar,unit,data,expected",
    [
        (ScalarType.TEXT, None, '\ufeff"日本語, quote"\r\n', "日本語, quote"),
        (ScalarType.TEXT, None, '"a\nline and ""quote"""\n', 'a\nline and "quote"'),
        (ScalarType.TEXT, None, '""\n', ""),
        (ScalarType.INTEGER, None, " +12 \n", 12),
        (ScalarType.REAL, None, " -.5e+2 \n", -50.0),
        (ScalarType.BOOLEAN, None, "TrUe\n", True),
        (ScalarType.BOOLEAN, None, "false\n", False),
        (ScalarType.DURATION, 60.0, "-2\n", -120 * s),
        (ScalarType.ROTATIONAL_SPEED, 1 / 60, "300\n", 300 * rpm),
        (ScalarType.VOLUME, 1e-6, "-2\n", -2 * mL),
    ],
)
def test_scalar_conversion_profile_is_literal_typed_and_unit_explicit(scalar, unit, data, expected):
    program = recipe_program(mode=CsvReadMode.ROW, header=False)
    function = program.functions[0]
    read = function.body[0]
    column = replace(
        read.columns[0],
        type=scalar,
        default=None,
        unit=None if unit is None else Literal(node_id="unit", type=scalar, value=unit),
    )
    program = replace(
        program,
        functions=(
            replace(
                function,
                variables=(replace(function.variables[0], type=scalar),),
                body=(replace(read, columns=(column,), targets=(read.targets[0],)),),
            ),
        ),
    )
    result = Interpreter(
        program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data.encode()}))
    ).run()
    assert result.outputs == {"value0": expected}


@pytest.mark.parametrize(
    "scalar,data",
    [
        (ScalarType.INTEGER, "1.5"),
        (ScalarType.INTEGER, "1+2"),
        (ScalarType.INTEGER, "１"),
        (ScalarType.INTEGER, "1_000"),
        (ScalarType.REAL, "nan"),
        (ScalarType.REAL, "1e999"),
        (ScalarType.REAL, "0x10"),
        (ScalarType.REAL, ""),
        (ScalarType.BOOLEAN, "1"),
        (ScalarType.BOOLEAN, ""),
        (ScalarType.ROTATIONAL_SPEED, "-1"),
    ],
)
def test_invalid_cells_use_only_their_typed_default(scalar, data):
    program = recipe_program(mode=CsvReadMode.ROW, policy=CsvErrorPolicy.STATUS, header=False)
    function = program.functions[0]
    read = function.body[0]
    default = False if scalar == ScalarType.BOOLEAN else 7
    column = replace(
        read.columns[0],
        type=scalar,
        default=replace(read.columns[0].default, type=scalar, value=default),
        unit=Literal(node_id="unit", type=scalar, value=1) if scalar == ScalarType.ROTATIONAL_SPEED else None,
    )
    program = replace(
        program,
        functions=(
            replace(
                function,
                variables=(function.variables[0], replace(function.variables[1], type=scalar)),
                body=(replace(read, columns=(column,), targets=read.targets[:2]),),
            ),
        ),
    )
    result = Interpreter(
        program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": f'"{data}"\n'.encode()}))
    ).run()
    assert result.outputs == {
        "value0": DEFAULT_USED,
        "value1": 420 * rpm if scalar == ScalarType.ROTATIONAL_SPEED else default,
    }


def test_quantity_default_is_canonical_not_scaled_again():
    program = recipe_program(mode=CsvReadMode.ROW)
    function = program.functions[0]
    read = function.body[0]
    column = replace(read.columns[1], default=replace(read.columns[1].default, value=3e-6))
    program = replace(program, functions=(replace(function, body=(replace(read, columns=(read.columns[0], column)),)),))
    result = Interpreter(
        program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": b"id,v\nA,bad\n"}))
    ).run()
    assert result.outputs["value1"] == 3 * mL
