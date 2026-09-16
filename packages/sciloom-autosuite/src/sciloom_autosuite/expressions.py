"""Plan expressions with ordered prerequisite tasks for checked array accesses."""

from dataclasses import dataclass
from typing import assert_never

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
    Unary,
    ValueType,
)
from sciloom.core.ir.expressions import ExpressionChecker
from .context import CodegenContext
from .encoding import number
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
    if isinstance(expression, Literal):
        text = (
            ("true" if expression.value else "false")
            if expression.type == ScalarType.BOOLEAN
            else number(expression.value)
        )
        return ExpressionPlan(text, expression.type)
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
        text = f"{expression.op.value} {operand.text}"
        return ExpressionPlan(f"({text})" if nested else text, operand.type, operand.prerequisites)
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
