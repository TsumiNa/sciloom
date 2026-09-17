"""Direct quantity IR retains dimensions across validation, JSON and execution."""

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


def expression_program(op, left, right, result):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Quantities",
                variables=(
                    Variable(node_id="result", owner_id="f", name="result", role=VariableRole.OUTPUT, type=result),
                ),
                body=(
                    Assignment(
                        node_id="assign",
                        target=Reference(node_id="target", symbol_id="result"),
                        value=Binary(
                            node_id="binary",
                            op=op,
                            left=Literal(node_id="left", type=left, value=-6.0),
                            right=Literal(node_id="right", type=right, value=2.0),
                        ),
                    ),
                ),
            ),
        ),
    )


@pytest.mark.parametrize("kind,field", [(ScalarType.FLOW_RATE, "m3_per_second"), (ScalarType.LENGTH, "metres")])
@pytest.mark.parametrize(
    "op,other,result,expected",
    [
        (BinaryOp.ADD, None, None, -4.0),
        (BinaryOp.SUBTRACT, None, None, -8.0),
        (BinaryOp.MULTIPLY, ScalarType.REAL, None, -12.0),
        (BinaryOp.DIVIDE, ScalarType.REAL, None, -3.0),
        (BinaryOp.DIVIDE, None, ScalarType.REAL, -3.0),
        (BinaryOp.LESS, None, ScalarType.BOOLEAN, True),
        (BinaryOp.LESS_EQUAL, None, ScalarType.BOOLEAN, True),
        (BinaryOp.GREATER, None, ScalarType.BOOLEAN, False),
        (BinaryOp.GREATER_EQUAL, None, ScalarType.BOOLEAN, False),
        (BinaryOp.EQUAL, None, ScalarType.BOOLEAN, False),
        (BinaryOp.NOT_EQUAL, None, ScalarType.BOOLEAN, True),
    ],
)
def test_quantity_matrix_survives_direct_json_and_specialization(kind, field, op, other, result, expected):
    result_type = result or kind
    program = expression_program(op, kind, other or kind, result_type)
    encoded = to_json(program)
    restored = from_json(encoded)
    assert restored == program and restored.format_version == 4 and to_json(restored) == encoded
    for candidate in (program, restored, specialize(restored, bindings=DeviceBindings())):
        value = Interpreter(candidate).run().outputs["result"]
        assert (getattr(value, field) if result is None else value) == expected


@pytest.mark.parametrize(
    "op", [BinaryOp.ADD, BinaryOp.SUBTRACT, BinaryOp.MULTIPLY, BinaryOp.DIVIDE, BinaryOp.EQUAL, BinaryOp.LESS]
)
def test_cross_dimensions_have_no_implicit_coercion(op):
    with pytest.raises(IRValidationError, match="operator_type"):
        to_json(expression_program(op, ScalarType.FLOW_RATE, ScalarType.LENGTH, ScalarType.FLOW_RATE))


@pytest.mark.parametrize("kind", [ScalarType.FLOW_RATE, ScalarType.LENGTH])
@pytest.mark.parametrize("bad", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_literals_reject_direct_and_json(kind, bad):
    program = expression_program(BinaryOp.ADD, kind, kind, kind)
    document = to_dict(program)
    document["functions"][0]["body"][0]["value"]["left"]["value"] = bad
    with pytest.raises(IRValidationError):
        from_dict(document)
    function = program.functions[0]
    statement = function.body[0]
    malformed = replace(
        program,
        functions=(
            replace(
                function,
                body=(
                    replace(
                        statement, value=replace(statement.value, left=Literal(node_id="left", type=kind, value=bad))
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(IRValidationError):
        to_json(malformed)
