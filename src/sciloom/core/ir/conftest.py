"""Shared semantic fixtures for colocated IR tests."""

import pytest

from sciloom.core.ir import (
    Assignment,
    Call,
    FunctionIR,
    InputBinding,
    Literal,
    OutputBinding,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
)


@pytest.fixture
def package() -> Program:
    """The semantic shape of Test12: identity function + caller storing 2.5."""
    callee = FunctionIR(
        node_id="fn:identity",
        name="Identity",
        variables=(
            Variable(node_id="var:x", owner_id="fn:identity", name="x", role=VariableRole.INPUT, type=ScalarType.REAL),
            Variable(node_id="var:y", owner_id="fn:identity", name="y", role=VariableRole.OUTPUT, type=ScalarType.REAL),
        ),
        body=(
            Assignment(
                node_id="stmt:copy",
                target=Reference(node_id="ref:y", symbol_id="var:y"),
                value=Reference(node_id="ref:x", symbol_id="var:x"),
            ),
        ),
    )
    caller = FunctionIR(
        node_id="fn:caller",
        name="Caller",
        variables=(
            Variable(
                node_id="var:result",
                owner_id="fn:caller",
                name="result",
                role=VariableRole.INTERNAL,
                type=ScalarType.REAL,
                initial=Literal(node_id="lit:initial", type=ScalarType.REAL, value=0.0),
            ),
        ),
        body=(
            Call(
                node_id="stmt:call",
                function_id="fn:identity",
                inputs=(
                    InputBinding(
                        parameter_id="var:x",
                        value=Literal(
                            node_id="lit:argument",
                            type=ScalarType.REAL,
                            value=2.5,
                        ),
                    ),
                ),
                outputs=(
                    OutputBinding(
                        parameter_id="var:y",
                        target=Reference(
                            node_id="ref:result",
                            symbol_id="var:result",
                        ),
                    ),
                ),
            ),
        ),
    )
    return Program(entry_function_id=caller.node_id, functions=(callee, caller))
