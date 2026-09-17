"""Direct JSON v4 thermal vocabulary has bounded affine arithmetic."""

from dataclasses import replace

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.specialization import specialize
from . import (
    Assignment,
    Binary,
    BinaryOp,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from .types import THERMAL_QUANTITIES

T = ScalarType.TEMPERATURE
D = ScalarType.TEMPERATURE_DIFFERENCE
R = ScalarType.TEMPERATURE_RATE
N = ScalarType.REAL
B = ScalarType.BOOLEAN


def thermal_program(op, left_type, right_type, result_type):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Thermal",
                variables=(
                    Variable(node_id="result", owner_id="f", name="result", role=VariableRole.OUTPUT, type=result_type),
                ),
                body=(
                    Assignment(
                        node_id="assign",
                        target=Reference(node_id="target", symbol_id="result"),
                        value=Binary(
                            node_id="binary",
                            op=op,
                            left=Literal(node_id="left", type=left_type, value=300.0),
                            right=Literal(node_id="right", type=right_type, value=2.0),
                        ),
                    ),
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "op,left,right,result,expected",
    [
        (BinaryOp.SUBTRACT, T, T, D, 298.0),
        (BinaryOp.ADD, T, D, T, 302.0),
        (BinaryOp.ADD, D, T, T, 302.0),
        (BinaryOp.SUBTRACT, T, D, T, 298.0),
        (BinaryOp.ADD, D, D, D, 302.0),
        (BinaryOp.SUBTRACT, D, D, D, 298.0),
        (BinaryOp.MULTIPLY, D, N, D, 600.0),
        (BinaryOp.MULTIPLY, N, D, D, 600.0),
        (BinaryOp.DIVIDE, D, N, D, 150.0),
        (BinaryOp.DIVIDE, D, D, N, 150.0),
        (BinaryOp.ADD, R, R, R, 302.0),
        (BinaryOp.SUBTRACT, R, R, R, 298.0),
        (BinaryOp.MULTIPLY, R, N, R, 600.0),
        (BinaryOp.MULTIPLY, N, R, R, 600.0),
        (BinaryOp.DIVIDE, R, N, R, 150.0),
        (BinaryOp.DIVIDE, R, R, N, 150.0),
        *(
            (op, kind, kind, B, expected)
            for kind in THERMAL_QUANTITIES
            for op, expected in (
                (BinaryOp.LESS, False),
                (BinaryOp.LESS_EQUAL, False),
                (BinaryOp.GREATER, True),
                (BinaryOp.GREATER_EQUAL, True),
                (BinaryOp.EQUAL, False),
                (BinaryOp.NOT_EQUAL, True),
            )
        ),
    ],
)
def test_direct_ir_json_specialization_matrix(op, left, right, result, expected):
    program = thermal_program(op, left, right, result)
    encoded = to_json(program)
    restored = from_json(encoded)
    assert restored == program and restored.format_version == 4
    for candidate in (program, restored, specialize(restored, bindings=DeviceBindings())):
        value = Interpreter(candidate).run().outputs["result"]
        canonical = value.kelvin if result in (T, D) else value.kelvin_per_second if result == R else value
        assert canonical == expected
    assert to_json(restored) == encoded


@pytest.mark.parametrize(
    "op,left,right",
    [
        (BinaryOp.ADD, T, T),
        (BinaryOp.MULTIPLY, T, N),
        (BinaryOp.MULTIPLY, N, T),
        (BinaryOp.DIVIDE, T, N),
        (BinaryOp.DIVIDE, T, T),
        (BinaryOp.SUBTRACT, D, T),
        (BinaryOp.ADD, T, R),
        (BinaryOp.ADD, D, R),
        (BinaryOp.MULTIPLY, R, ScalarType.DURATION),
        (BinaryOp.EQUAL, T, D),
        (BinaryOp.LESS, D, R),
    ],
)
def test_invalid_thermal_matrix_rejects_before_execution(op, left, right):
    with pytest.raises(IRValidationError, match="operator_type"):
        to_json(thermal_program(op, left, right, T))


@pytest.mark.parametrize("kind", THERMAL_QUANTITIES)
@pytest.mark.parametrize("value", [True, "1", float("inf"), float("nan"), 10**1000])
def test_bad_thermal_literals_cannot_enter_from_direct_or_json(kind, value):
    program = thermal_program(BinaryOp.EQUAL, kind, kind, B)
    document = to_dict(program)
    document["functions"][0]["body"][0]["value"]["left"]["value"] = value
    with pytest.raises(IRValidationError):
        from_dict(document)
    function = program.functions[0]
    statement = function.body[0]
    invalid = replace(
        program,
        functions=(
            replace(
                function,
                body=(
                    replace(
                        statement,
                        value=replace(statement.value, left=Literal(node_id="left", type=kind, value=value)),
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(IRValidationError):
        to_json(invalid)


def test_negative_absolute_literal_rejected_and_wrong_result_type_not_coerced():
    document = to_dict(thermal_program(BinaryOp.SUBTRACT, T, T, D))
    document["functions"][0]["body"][0]["value"]["left"]["value"] = -1
    with pytest.raises(IRValidationError, match="literal_type"):
        from_dict(document)
    with pytest.raises(IRValidationError, match="type_mismatch"):
        to_json(thermal_program(BinaryOp.SUBTRACT, T, T, T))
