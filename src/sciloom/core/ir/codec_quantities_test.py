"""Direct quantity IR uses the existing literal/binary v4 representation."""

import pytest

from sciloom.core.interpreter import Interpreter
from sciloom.units import Duration, Volume
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
    from_json,
    to_json,
)


@pytest.mark.parametrize(
    "kind,factor,expected",
    [(ScalarType.VOLUME, 1e-6, Volume(m3=-2e-6)), (ScalarType.DURATION, 60.0, Duration(seconds=-120))],
)
def test_direct_quantity_construction_and_json(kind, factor, expected):
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Quantity",
                variables=(
                    Variable(node_id="n", owner_id="f", name="number", role=VariableRole.INPUT, type=ScalarType.REAL),
                    Variable(node_id="q", owner_id="f", name="quantity", role=VariableRole.OUTPUT, type=kind),
                ),
                body=(
                    Assignment(
                        node_id="write",
                        target=Reference(node_id="out", symbol_id="q"),
                        value=Binary(
                            node_id="scale",
                            op=BinaryOp.MULTIPLY,
                            left=Reference(node_id="in", symbol_id="n"),
                            right=Literal(node_id="unit", type=kind, value=factor),
                        ),
                    ),
                ),
            ),
        ),
    )
    restored = from_json(to_json(program))
    assert restored == program
    assert restored.format_version == 4
    for candidate in (program, restored):
        assert Interpreter(candidate).run(inputs={"number": -2.0}).outputs == {"quantity": expected}
