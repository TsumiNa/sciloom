"""Unary enum extensions retain v4 shape and validate dimension/result types."""

import pytest

from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import Interpreter
from . import (
    Assignment,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Unary,
    UnaryOp,
    Variable,
    VariableRole,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def numeric_program(op, kind, value, result_kind):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Numeric",
                variables=(
                    Variable(node_id="out", owner_id="f", name="result", role=VariableRole.OUTPUT, type=result_kind),
                ),
                body=(
                    Assignment(
                        node_id="write",
                        target=Reference(node_id="target", symbol_id="out"),
                        value=Unary(
                            node_id="operation", op=op, operand=Literal(node_id="argument", type=kind, value=value)
                        ),
                    ),
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "op,value,expected",
    [
        (UnaryOp.ABSOLUTE, -1.25, 1.25),
        (UnaryOp.FLOOR, -1.25, -2),
        (UnaryOp.ROUND, -2.5, -2),
        (UnaryOp.ROUND, 3.5, 4),
    ],
)
def test_direct_numeric_ir_and_json(op, value, expected):
    result_kind = ScalarType.REAL if op == UnaryOp.ABSOLUTE else ScalarType.INTEGER
    program = numeric_program(op, ScalarType.REAL, value, result_kind)
    document = to_dict(program)
    assert document["format_version"] == 4
    assert document["functions"][0]["body"][0]["value"]["kind"] == "Unary"
    restored = from_json(to_json(program))
    assert restored == program
    for candidate in (program, restored):
        assert Interpreter(candidate).run().outputs == {"result": expected}
    document["functions"][0]["body"][0]["value"]["op"] = "round_to_unknown_mode"
    with pytest.raises(IRValidationError, match="Unknown UnaryOp"):
        from_dict(document)


@pytest.mark.parametrize("op", [UnaryOp.ABSOLUTE, UnaryOp.FLOOR, UnaryOp.ROUND])
@pytest.mark.parametrize("kind,value", [(ScalarType.BOOLEAN, True), (ScalarType.TEXT, "1")])
def test_numeric_operations_reject_nonnumeric_types(op, kind, value):
    with pytest.raises(IRValidationError, match="operator_type"):
        to_json(numeric_program(op, kind, value, ScalarType.INTEGER))


@pytest.mark.parametrize("op", [UnaryOp.FLOOR, UnaryOp.ROUND])
@pytest.mark.parametrize("kind", [ScalarType.VOLUME, ScalarType.DURATION, ScalarType.ROTATIONAL_SPEED])
def test_rounding_requires_explicit_unit_conversion(op, kind):
    with pytest.raises(IRValidationError, match="operator_type"):
        to_json(numeric_program(op, kind, 1.5, ScalarType.INTEGER))


def test_numeric_result_type_is_not_inferred_from_destination():
    with pytest.raises(IRValidationError, match="type_mismatch"):
        to_json(numeric_program(UnaryOp.ABSOLUTE, ScalarType.REAL, -1.25, ScalarType.INTEGER))
