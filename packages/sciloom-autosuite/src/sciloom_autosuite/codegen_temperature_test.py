"""Thermal core support never falls through to an unverified native encoding."""

import pytest

from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import FunctionIR, ListType, Literal, LogValue, Program, ScalarType, Variable, VariableRole
from sciloom.core.ir.types import THERMAL_QUANTITIES
from .encoding import literal_value, value_encoding
from .target import AutoSuiteTarget


@pytest.mark.parametrize("kind", THERMAL_QUANTITIES)
@pytest.mark.parametrize("array", [False, True])
def test_thermal_declarations_and_direct_encoding_reject(kind, array):
    value_type = ListType(element_type=kind) if array else kind
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Thermal",
                variables=(
                    Variable(node_id="input", name="value", owner_id="f", role=VariableRole.INPUT, type=value_type),
                ),
            ),
        ),
    )
    with pytest.raises(CompilationError, match="unsupported_temperature_type"):
        compile_ir(program, target=AutoSuiteTarget())
    with pytest.raises(CompilationError, match="unsupported_temperature_type"):
        value_encoding(value_type)


@pytest.mark.parametrize("kind", THERMAL_QUANTITIES)
def test_thermal_literal_without_any_variable_rejects(kind):
    value = Literal(node_id="value", type=kind, value=300.0)
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Thermal",
                body=(
                    LogValue(
                        node_id="log",
                        value=value,
                        category=Literal(node_id="cat", type=ScalarType.TEXT, value="thermal"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="value"),
                    ),
                ),
            ),
        ),
    )
    with pytest.raises(CompilationError, match="unsupported_temperature_type"):
        compile_ir(program, target=AutoSuiteTarget())
    with pytest.raises(CompilationError, match="unsupported_temperature_type"):
        literal_value(value)
