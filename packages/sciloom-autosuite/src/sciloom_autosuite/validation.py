"""Conservative array-output initialization checks for reusable vendor storage."""

from typing import assert_never

from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import (
    Assignment,
    Call,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    Expression,
    If,
    ListGet,
    ListLiteral,
    ListSet,
    ListType,
    Literal,
    Program,
    Reference,
    ScalarType,
    StartAgitation,
    Statement,
    StopAgitation,
    TextLength,
    TextSplitPart,
    VariableRole,
    While,
)
from sciloom.core.ir.expressions import ExpressionChecker
from sciloom.core.ir.traversal import iter_nodes


def validate_text_guards(program: Program) -> tuple[Diagnostic, ...]:
    """Reject new text operations needing unverified AutoSuite failure propagation."""
    errors = []
    symbols = {v.node_id: v for f in program.functions for v in f.variables}
    checker = ExpressionChecker(symbols, lambda *args: None)
    for function in program.functions:
        for node, path in iter_nodes(function):
            message = None
            code = "unsupported_runtime_guard"
            if isinstance(node, TextLength):
                if not (
                    isinstance(node.value, Literal)
                    and isinstance(node.value.value, str)
                    and all(ord(c) <= 0xFFFF for c in node.value.value)
                ):
                    message = "AutoSuite text length currently requires literal BMP text; Unicode code-point equivalence for runtime text is unverified."
                    code = "unsupported_text_length"
            elif isinstance(node, TextSplitPart):
                if not (
                    isinstance(node.delimiter, Literal)
                    and node.delimiter.type == ScalarType.TEXT
                    and isinstance(node.delimiter.value, str)
                    and node.delimiter.value
                    and isinstance(node.index, Literal)
                    and type(node.index.value) is int
                    and node.index.value >= 0
                ):
                    message = "AutoSuite split requires a literal nonempty delimiter and a literal nonnegative index until runtime failure propagation is verified."
            elif isinstance(node, (ListGet, ListSet)):
                value = node.value if isinstance(node, ListGet) else node.target
                if checker.check(value, function, path) == ListType(element_type=ScalarType.TEXT):
                    bounded = (
                        isinstance(node, ListGet)
                        and isinstance(node.value, ListLiteral)
                        and isinstance(node.index, Literal)
                        and type(node.index.value) is int
                        and 0 <= node.index.value < len(node.value.elements)
                    )
                    if not bounded:
                        message = "Text-list indexing needs verified runtime bounds failure; use whole-list values or reference execution for now."
            if message:
                errors.append(
                    Diagnostic(
                        code=code,
                        message=message,
                        path=path,
                        node_id=node.node_id,
                        source=node.source,
                    )
                )
    return tuple(errors)


def validate_array_outputs(program: Program) -> tuple[Diagnostic, ...]:
    """Do not let persistent vendor parameter storage stand in for an unset output.

    This target requires definite whole-list assignment before reads and returns.
    Assignments in a possibly-zero-iteration loop are not definite assignments.
    """
    errors = []
    for function in program.functions:
        outputs = {
            v.node_id for v in function.variables if v.role == VariableRole.OUTPUT and isinstance(v.type, ListType)
        }

        def read(expression: Expression, assigned: set[str]) -> None:
            for node, _ in iter_nodes(expression):
                if isinstance(node, Reference) and node.symbol_id in outputs - assigned:
                    errors.append(
                        Diagnostic(
                            code="list_output_initialization",
                            message="Assign a whole list to this output before reading it.",
                            path="$",
                            node_id=node.node_id,
                            source=node.source,
                        )
                    )

        def block(body: tuple[Statement, ...], assigned: set[str]) -> set[str]:
            assigned = assigned.copy()
            for statement in body:
                if isinstance(statement, Assignment):
                    read(statement.value, assigned)
                    assigned.add(statement.target.symbol_id)
                elif isinstance(statement, ListSet):
                    for expression in (statement.target, statement.index, statement.value):
                        read(expression, assigned)
                elif isinstance(statement, Call):
                    for binding in statement.inputs:
                        read(binding.value, assigned)
                    assigned.update(binding.target.symbol_id for binding in statement.outputs)
                elif isinstance(statement, If):
                    read(statement.condition, assigned)
                    assigned = block(statement.then_body, assigned) & block(statement.else_body, assigned)
                elif isinstance(statement, While):
                    read(statement.condition, assigned)
                    block(statement.body, assigned)
                elif isinstance(statement, ConfigureProperty):
                    read(statement.value, assigned)
                elif isinstance(statement, (StartAgitation, StopAgitation)):
                    pass  # Lifecycle commands have no variable reads or writes.
                elif isinstance(statement, (DeviceCommand, DeviceIf)):
                    pass  # Unsupported here; the task emitter explicitly rejects them.
                else:
                    assert_never(statement)
            return assigned

        assigned = block(function.body, set())
        if outputs - assigned:
            errors.append(
                Diagnostic(
                    code="list_output_initialization",
                    message="AutoSuite requires whole-list output assignment on every return path.",
                    path="$",
                    node_id=function.node_id,
                    source=function.source,
                )
            )
    return tuple(errors)
