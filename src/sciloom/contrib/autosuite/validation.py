"""Conservative array-output initialization checks for reusable vendor storage."""

from ...core.diagnostics import Diagnostic
from ...core.ir import (
    Assignment,
    Call,
    Expression,
    If,
    ListSet,
    ListType,
    Program,
    Reference,
    ConfigureProperty,
    Statement,
    VariableRole,
    While,
)
from ...core.ir.traversal import iter_nodes


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
