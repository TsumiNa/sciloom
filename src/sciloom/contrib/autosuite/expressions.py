"""Render validated scalar IR expressions in AutoSuite expression syntax."""

from __future__ import annotations

from ...core.ir import BinaryOp, Expression, Literal, Reference, ScalarType, Unary
from .context import CodegenContext
from .encoding import number


def render_expression(context: CodegenContext, expression: Expression, *, nested: bool = False) -> str:
    if isinstance(expression, Literal):
        return (
            ("true" if expression.value else "false")
            if expression.type == ScalarType.BOOLEAN
            else number(expression.value)
        )
    if isinstance(expression, Reference):
        return context.names[expression.symbol_id]
    if isinstance(expression, Unary):
        text = f"{expression.op.value} {render_expression(context, expression.operand, nested=True)}"
    else:
        operator = {BinaryOp.EQUAL: "=", BinaryOp.NOT_EQUAL: "<>"}.get(expression.op, expression.op.value)
        text = f"{render_expression(context, expression.left, nested=True)} {operator} {render_expression(context, expression.right, nested=True)}"
    return f"({text})" if nested else text
