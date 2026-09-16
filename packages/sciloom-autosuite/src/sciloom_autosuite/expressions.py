"""Plan expressions with ordered prerequisite tasks for checked array accesses."""

from dataclasses import dataclass
from typing import assert_never

from sciloom.core.diagnostics import CompilationError, Diagnostic
from sciloom.core.ir import (
    Binary,
    BinaryOp,
    Expression,
    FunctionIR,
    ListGet,
    ListLength,
    ListLiteral,
    ListType,
    Literal,
    Reference,
    ScalarType,
    TextLength,
    TextSplitPart,
    TextTrim,
    Unary,
    UnaryOp,
    ValueType,
    WellName,
    ZoneCombine,
    ZoneFind,
    ZoneLength,
    ZoneLiteral,
    ZoneType,
)
from sciloom.core.ir.expressions import ExpressionChecker
from .context import CodegenContext
from .encoding import literal_value
from .primitives import macro, set_variable
from .xml import XmlNode


@dataclass(frozen=True)
class ExpressionPlan:
    text: str
    type: ValueType
    prerequisites: tuple[XmlNode, ...] = ()


def materialize(context: CodegenContext, function: FunctionIR, plan: ExpressionPlan, tag: str) -> ExpressionPlan:
    """Evaluate now, before later prerequisites or a call can affect the value."""
    name = context.temporary(function, plan.type)
    task = set_variable(context, tag, name, plan.text, array=isinstance(plan.type, ListType))
    return ExpressionPlan(name, plan.type, (*plan.prerequisites, task))


def checked_read(
    context: CodegenContext, function: FunctionIR, array: str, index: ExpressionPlan, element_type: ScalarType, tag: str
) -> tuple[ExpressionPlan, str]:
    """Capture index once; turn negative indices into a documented out-of-range read."""
    captured = materialize(context, function, index, tag)
    negative = macro(
        context,
        tag,
        context.fresh_id(),
        function,
        (set_variable(context, "task", captured.text, f"ArraySize({array})"),),
        name="Reject negative index",
        condition_type="1",
        condition=f"{captured.text} < 0",
    )
    value = context.temporary(function, element_type)
    read = set_variable(context, tag, value, f"{array}[{captured.text}]")
    return ExpressionPlan(value, element_type, (*captured.prerequisites, negative, read)), captured.text


def plan_expression(
    context: CodegenContext, function: FunctionIR, expression: Expression, tag: str, *, nested: bool = False
) -> ExpressionPlan:
    if isinstance(expression, ZoneLiteral):
        if expression.well_ids:
            raise CompilationError(
                (
                    Diagnostic(
                        code="unsupported_zone_literal",
                        message="AutoSuite cannot encode opaque well identities as a Zone expression; use zones.find.",
                        path="$",
                        node_id=expression.node_id,
                        source=expression.source,
                    ),
                )
            )
        # A fresh, never-written Zone variable uses the observed empty initial
        # representation. Do not guess an expression literal for an empty Zone.
        return ExpressionPlan(context.temporary(function, ZoneType()), ZoneType())
    if isinstance(expression, ZoneFind):
        zone_name = plan_expression(context, function, expression.name, tag)
        return ExpressionPlan(f"FindZone({zone_name.text})", ZoneType(), zone_name.prerequisites)
    if isinstance(expression, ZoneLength):
        value = plan_expression(context, function, expression.value, tag)
        return ExpressionPlan(f"ZoneSize({value.text})", ScalarType.INTEGER, value.prerequisites)
    if isinstance(expression, ZoneCombine):
        left_zone = plan_expression(context, function, expression.left, tag)
        right_zone = plan_expression(context, function, expression.right, tag)
        if right_zone.prerequisites:
            left_zone = materialize(context, function, left_zone, tag)
        return ExpressionPlan(
            f"({left_zone.text} + {right_zone.text})", ZoneType(), (*left_zone.prerequisites, *right_zone.prerequisites)
        )
    if isinstance(expression, WellName):
        raise CompilationError(
            (
                Diagnostic(
                    code="unsupported_zone_cardinality",
                    message="well_name requires a verified single-well check before AutoSuite WellFullName can be emitted.",
                    path="$",
                    node_id=expression.node_id,
                    source=expression.source,
                ),
            )
        )
    if isinstance(expression, Literal):
        return ExpressionPlan(literal_value(expression), expression.type)
    if isinstance(expression, (TextLength, TextTrim)):
        value = plan_expression(context, function, expression.value, tag)
        name = "TextLength" if isinstance(expression, TextLength) else "TrimText"
        kind = ScalarType.INTEGER if isinstance(expression, TextLength) else ScalarType.TEXT
        return ExpressionPlan(f"{name}({value.text})", kind, value.prerequisites)
    if isinstance(expression, TextSplitPart):
        arguments = [
            plan_expression(context, function, arg, tag)
            for arg in (expression.value, expression.delimiter, expression.index)
        ]
        if any(arg.prerequisites for arg in arguments):
            arguments = [materialize(context, function, arg, tag) for arg in arguments]
        text = "SplitTextAndGet(" + ", ".join(arg.text for arg in arguments) + ")"
        return ExpressionPlan(text, ScalarType.TEXT, tuple(task for arg in arguments for task in arg.prerequisites))
    if isinstance(expression, Reference):
        return ExpressionPlan(context.names[expression.symbol_id], context.variables[expression.symbol_id].type)
    if isinstance(expression, ListLiteral):
        name = context.temporary(function, expression.type, length=len(expression.elements))
        tasks: list[XmlNode] = []
        for i, element in enumerate(expression.elements):
            value = plan_expression(context, function, element, tag)
            tasks.extend(value.prerequisites)
            tasks.append(set_variable(context, tag, name, value.text, index=str(i)))
        return ExpressionPlan(name, expression.type, tuple(tasks))
    if isinstance(expression, (ListLength, ListGet)):
        array = plan_expression(context, function, expression.value, tag)
        assert isinstance(array.type, ListType)
        if isinstance(expression, ListLength):
            return ExpressionPlan(f"ArraySize({array.text})", ScalarType.INTEGER, array.prerequisites)
        index = plan_expression(context, function, expression.index, tag)
        value, _ = checked_read(context, function, array.text, index, array.type.element_type, tag)
        return ExpressionPlan(value.text, value.type, (*array.prerequisites, *value.prerequisites))
    if isinstance(expression, Unary):
        operand = plan_expression(context, function, expression.operand, tag, nested=True)
        op = expression.op
        if op in (UnaryOp.ABSOLUTE, UnaryOp.FLOOR, UnaryOp.ROUND):
            if op in (UnaryOp.FLOOR, UnaryOp.ROUND) and operand.type == ScalarType.INTEGER:
                return operand
            if op == UnaryOp.ROUND:
                # Target validation rejects this before code generation.
                raise CompilationError(
                    (
                        Diagnostic(
                            code="unsupported_rounding",
                            message="AutoSuite real round has no verified ties-to-even mapping.",
                            path="$",
                            node_id=expression.node_id,
                            source=expression.source,
                        ),
                    )
                )
            result_type = ScalarType.INTEGER if op == UnaryOp.FLOOR else operand.type
            return ExpressionPlan(f"{op.value}({operand.text})", result_type, operand.prerequisites)
        if op in (UnaryOp.POSITIVE, UnaryOp.NEGATIVE, UnaryOp.NOT):
            text = f"{op.value} {operand.text}"
            return ExpressionPlan(f"({text})" if nested else text, operand.type, operand.prerequisites)
        assert_never(op)
    if not isinstance(expression, Binary):
        assert_never(expression)
    left = plan_expression(context, function, expression.left, tag, nested=True)
    right = plan_expression(context, function, expression.right, tag, nested=True)
    if right.prerequisites:
        left = materialize(context, function, left, tag)
    operator = {BinaryOp.EQUAL: "=", BinaryOp.NOT_EQUAL: "<>"}.get(expression.op, expression.op.value)
    text = f"{left.text} {operator} {right.text}"
    value_type = ExpressionChecker(context.variables, lambda *args: None).check(expression, function, "$")
    assert value_type is not None
    return ExpressionPlan(f"({text})" if nested else text, value_type, (*left.prerequisites, *right.prerequisites))
