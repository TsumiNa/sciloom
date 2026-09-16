"""CSV wire records and semantic checks reject incomplete or ambiguous reads."""

from copy import deepcopy

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.specialization import specialize
from . import (
    CsvColumn,
    CsvErrorPolicy,
    CsvReadMode,
    FunctionIR,
    Literal,
    Program,
    ReadCsv,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def row_program():
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Row",
                variables=(
                    Variable(node_id="v", owner_id="f", name="result", type=ScalarType.REAL, role=VariableRole.OUTPUT),
                ),
                body=(
                    ReadCsv(
                        node_id="read",
                        path=Literal(node_id="path", type=ScalarType.TEXT, value="data.csv"),
                        mode=CsvReadMode.ROW,
                        error_policy=CsvErrorPolicy.RAISE,
                        header=False,
                        row=Literal(node_id="row", type=ScalarType.INTEGER, value=0),
                        columns=(
                            CsvColumn(
                                index=Literal(node_id="index", type=ScalarType.INTEGER, value=0), type=ScalarType.REAL
                            ),
                        ),
                        targets=(Reference(node_id="target", symbol_id="v"),),
                    ),
                ),
            ),
        ),
    )


def test_csv_stable_kinds_round_trip_specialization_and_configuration():
    program = row_program()
    canonical = to_json(program)
    restored = from_json(canonical)
    assert restored == program
    assert specialize(restored, bindings=DeviceBindings()) == program
    assert validate_device_usage(program, DeviceBindings()) == ()
    document = to_dict(program)
    assert document["format_version"] == 4
    read = document["functions"][0]["body"][0]
    assert read["kind"] == "ReadCsv"
    assert read["columns"][0]["kind"] == "CsvColumn"
    assert to_json(program) == canonical


@pytest.mark.parametrize(
    "change",
    [
        "unknown_field",
        "unknown_kind",
        "unknown_mode",
        "unknown_policy",
        "unknown_type",
        "header_type",
        "row_missing",
        "row_for_columns",
        "row_boolean",
        "column_negative",
        "empty_columns",
        "path_type",
        "empty_path",
        "duplicate_target",
        "missing_target",
        "target_type",
        "target_owner",
        "missing_unit",
        "wrong_unit",
        "zero_unit",
        "wrong_default",
        "try_missing_default",
    ],
)
def test_csv_wire_and_type_errors_are_rejected(change):
    document = to_dict(row_program())
    function = document["functions"][0]
    read = function["body"][0]
    column = read["columns"][0]
    if change == "unknown_field":
        read["delimiter"] = ";"
    elif change == "unknown_kind":
        column["kind"] = "import.external.Column"
    elif change == "unknown_mode":
        read["mode"] = "cells"
    elif change == "unknown_policy":
        read["error_policy"] = "ignore"
    elif change == "unknown_type":
        column["type"] = "object"
    elif change == "header_type":
        read["header"] = 1
    elif change == "row_missing":
        read["row"] = None
    elif change == "row_for_columns":
        read["mode"] = "columns"
    elif change == "row_boolean":
        read["row"].update(type="boolean", value=True)
    elif change == "column_negative":
        column["index"]["value"] = -1
    elif change == "empty_columns":
        read["columns"] = []
    elif change == "path_type":
        read["path"].update(type="integer", value=1)
    elif change == "empty_path":
        read["path"]["value"] = ""
    elif change == "duplicate_target":
        other = deepcopy(column)
        other["index"]["node_id"] = "index2"
        read["columns"].append(other)
        read["targets"].append(dict(read["targets"][0], node_id="target2"))
    elif change == "missing_target":
        read["targets"] = []
    elif change == "target_type":
        function["variables"][0]["type"] = "text"
    elif change == "target_owner":
        function["variables"][0]["owner_id"] = "another"
    elif change == "missing_unit":
        column["type"] = "volume"
    elif change in ("wrong_unit", "zero_unit"):
        column["type"] = "volume"
        column["unit"] = dict(
            column["index"],
            node_id="unit",
            type="volume" if change == "zero_unit" else "duration",
            value=0 if change == "zero_unit" else 1,
        )
    elif change == "wrong_default":
        column["default"] = dict(column["index"], node_id="default", type="text", value="fallback")
    else:
        read["error_policy"] = "status"
    with pytest.raises(IRValidationError):
        from_dict(document)
