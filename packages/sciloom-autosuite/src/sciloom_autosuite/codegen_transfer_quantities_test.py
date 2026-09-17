"""Transfer quantity core support never falls through to an unverified native encoding."""

import pytest

from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import FunctionIR, ListType, Literal, LogValue, Program, ScalarType, Variable, VariableRole
from .encoding import literal_value, value_encoding
from .target import AutoSuiteTarget


@pytest.mark.parametrize("kind", (ScalarType.FLOW_RATE, ScalarType.LENGTH))
@pytest.mark.parametrize("array", [False, True])
def test_transfer_quantity_declarations_and_direct_encoding_reject(kind, array):
    value_type = ListType(element_type=kind) if array else kind
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="TransferQuantity",
                variables=(
                    Variable(node_id="input", name="value", owner_id="f", role=VariableRole.INPUT, type=value_type),
                ),
            ),
        ),
    )
    with pytest.raises(CompilationError, match="unsupported_transfer_quantity"):
        compile_ir(program, target=AutoSuiteTarget())
    with pytest.raises(CompilationError, match="unsupported_transfer_quantity"):
        value_encoding(value_type)


@pytest.mark.parametrize("kind", (ScalarType.FLOW_RATE, ScalarType.LENGTH))
def test_transfer_quantity_literal_without_any_variable_rejects(kind):
    value = Literal(node_id="value", type=kind, value=300.0)
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="TransferQuantity",
                body=(
                    LogValue(
                        node_id="log",
                        value=value,
                        category=Literal(node_id="cat", type=ScalarType.TEXT, value="transfer_quantity"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="value"),
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(CompilationError, match="unsupported_transfer_quantity"):
        compile_ir(program, target=AutoSuiteTarget())
    with pytest.raises(CompilationError, match="unsupported_transfer_quantity"):
        literal_value(value)
