"""Conservative array-output initialization checks for reusable vendor storage."""

from typing import assert_never

from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import (
    AppendCsv,
    Assignment,
    Binary,
    BinaryOp,
    Call,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    Expression,
    ForEachZone,
    If,
    ListGet,
    ListLiteral,
    ListSet,
    ListType,
    Literal,
    LogValue,
    Notify,
    Program,
    ReadCsv,
    ReadWallTime,
    ReadWellProperty,
    Reference,
    ScalarType,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    TextLength,
    TextSplitPart,
    Unary,
    UnaryOp,
    VariableRole,
    Wait,
    WaitUntil,
    WellName,
    While,
    WriteWellProperty,
    ZoneGet,
    ZoneLiteral,
)
from sciloom.core.ir.expressions import ExpressionChecker
from sciloom.core.ir.traversal import iter_nodes
from sciloom.core.ir.types import QUANTITIES


def _safe_speed_factor(value: Expression, op: BinaryOp) -> bool:
    return (
        isinstance(value, Literal)
        and type(value.value) in (int, float)
        and isinstance(value.value, (int, float))
        and (value.value > 0 if op == BinaryOp.DIVIDE else value.value >= 0)
    )


def validate_runtime_guards(program: Program) -> tuple[Diagnostic, ...]:
    """Reject new value operations needing unverified AutoSuite runtime checks."""
    errors = []
    symbols = {v.node_id: v for f in program.functions for v in f.variables}
    checker = ExpressionChecker(symbols, lambda *args: None)
    for function_index, function in enumerate(program.functions):
        for node, path in iter_nodes(function, f"$.functions[{function_index}]"):
            message = None
            code = "unsupported_runtime_guard"
            if isinstance(node, ZoneLiteral) and node.well_ids:
                code = "unsupported_zone_literal"
                message = "AutoSuite cannot encode opaque well identities as a Zone expression; use zones.find or Zone inputs."
            elif isinstance(node, WellName):
                code = "unsupported_zone_cardinality"
                message = "well_name requires a verified single-well check before AutoSuite WellFullName can be emitted; reference execution is available."
            elif isinstance(node, ZoneGet):
                code = "unsupported_zone_index"
                message = "Zone indexing requires verified bounds failure propagation before AutoSuite tasks can be emitted; reference execution is available."
            elif isinstance(node, ForEachZone) and node.fragment_size != 1:
                code = "unsupported_zone_grouping"
                message = "Grouped Zone traversal requires verified divisibility failure propagation; single-well traversal and reference execution are available."
            elif isinstance(node, ReadCsv):
                code = "unsupported_csv_semantics"
                message = "AutoSuite CSV expression evaluation, conversion and per-column result aggregation are not verified against typed literal CSV semantics; reference execution is available."
            elif isinstance(node, AppendCsv):
                code = "unsupported_csv_append"
                message = "The observed AutoSuite export mode has not been verified to append without overwrite; encoding and failure propagation also require platform validation."
            elif isinstance(node, (Wait, WaitUntil)):
                duration = node.duration
                if not isinstance(duration, Literal):
                    message = "AutoSuite waits require a literal duration until runtime range failure propagation is verified."
                elif not (isinstance(duration.value, (int, float)) and 0 <= duration.value <= 79_999 * 3600):
                    code = "wait_duration"
                    message = "AutoSuite wait duration must be within 0–79,999 hours."
            elif isinstance(node, Unary) and node.op == UnaryOp.ROUND:
                if checker.check(node.operand, function, path) != ScalarType.INTEGER:
                    message = "AutoSuite round for real values has no verified Python ties-to-even mapping or expansion range; round of an integer remains an identity."
                    code = "unsupported_rounding"
            elif isinstance(node, TextLength):
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
                value_type = checker.check(value, function, path)
                if isinstance(value_type, ListType) and value_type.element_type in (
                    ScalarType.TEXT,
                    ScalarType.VOLUME,
                    ScalarType.DURATION,
                ):
                    bounded = (
                        isinstance(node, ListGet)
                        and isinstance(node.value, ListLiteral)
                        and isinstance(node.index, Literal)
                        and type(node.index.value) is int
                        and 0 <= node.index.value < len(node.value.elements)
                    )
                    if not bounded:
                        message = "Text/volume/duration-list indexing needs verified runtime bounds failure; use whole-list values or reference execution for now."
                elif (
                    isinstance(node, ListSet)
                    and value_type == ListType(element_type=ScalarType.ROTATIONAL_SPEED)
                    and node.op in (BinaryOp.MULTIPLY, BinaryOp.DIVIDE)
                ):
                    if not _safe_speed_factor(node.value, node.op):
                        message = "Speed scaling needs a literal nonnegative factor (positive for division) until runtime failure propagation is verified."
            elif isinstance(node, Binary):
                left = checker.check(node.left, function, path)
                if node.op == BinaryOp.DIVIDE and left in QUANTITIES:
                    divisor = node.right
                    if not (
                        isinstance(divisor, Literal) and type(divisor.value) in (int, float) and divisor.value != 0
                    ):
                        message = "Quantity division requires a literal nonzero divisor until runtime failure propagation is verified."
                result = checker.check(node, function, path)
                if result == ScalarType.ROTATIONAL_SPEED:
                    factor = node.right if left == ScalarType.ROTATIONAL_SPEED else node.left
                    if not _safe_speed_factor(factor, node.op):
                        message = "Speed scaling needs a literal nonnegative factor (positive for division) until runtime failure propagation is verified."
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
                elif isinstance(statement, LogValue):
                    for expression in (statement.value, statement.category, statement.stream):
                        read(expression, assigned)
                elif isinstance(statement, Notify):
                    read(statement.message, assigned)
                elif isinstance(statement, AppendCsv):
                    read(statement.path, assigned)
                    for value in statement.values:
                        read(value, assigned)
                    if statement.status is not None:
                        assigned.add(statement.status.symbol_id)
                elif isinstance(statement, ReadCsv):
                    read(statement.path, assigned)
                    if statement.row is not None:
                        read(statement.row, assigned)
                    for column in statement.columns:
                        read(column.index, assigned)
                        if column.default is not None:
                            read(column.default, assigned)
                    assigned.update(target.symbol_id for target in statement.targets)
                elif isinstance(statement, ReadWallTime):
                    assigned.add(statement.target.symbol_id)
                elif isinstance(statement, (ReadWellProperty, WriteWellProperty)):
                    read(statement.zone, assigned)
                    if isinstance(statement, WriteWellProperty):
                        read(statement.value, assigned)
                    else:
                        if statement.default is not None:
                            read(statement.default, assigned)
                        assigned.add(statement.target.symbol_id)
                elif isinstance(statement, (Wait, WaitUntil)):
                    read(statement.duration, assigned)
                elif isinstance(statement, StartTimer):
                    pass
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
                elif isinstance(statement, ForEachZone):
                    read(statement.value, assigned)
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
