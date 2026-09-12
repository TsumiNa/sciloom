"""Translate scalar Python expressions without executing runtime source."""

from __future__ import annotations

import ast
from typing import cast
from .context import LoweringContext
from ..units import RotationalSpeed
from ..core.ir import Binary, BinaryOp, Expression, Literal, Reference, ScalarType, Unary, UnaryOp


BINARY_OPERATORS = {
    ast.Add: BinaryOp.ADD,
    ast.Sub: BinaryOp.SUBTRACT,
    ast.Mult: BinaryOp.MULTIPLY,
    ast.Div: BinaryOp.DIVIDE,
    ast.Eq: BinaryOp.EQUAL,
    ast.NotEq: BinaryOp.NOT_EQUAL,
    ast.Lt: BinaryOp.LESS,
    ast.LtE: BinaryOp.LESS_EQUAL,
    ast.Gt: BinaryOp.GREATER,
    ast.GtE: BinaryOp.GREATER_EQUAL,
    ast.And: BinaryOp.AND,
    ast.Or: BinaryOp.OR,
}
UNARY_OPERATORS = {ast.UAdd: UnaryOp.POSITIVE, ast.USub: UnaryOp.NEGATIVE, ast.Not: UnaryOp.NOT}

def expression(context: LoweringContext, node: ast.AST) -> Expression:
    if isinstance(node, ast.Constant):
        value = node.value
    elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        if node.attr in context.instance.model_fields:
            return Reference(**context.metadata(node), symbol_id=context.symbol(node.attr))
        value = context.host_attribute(node.attr)
    elif (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and isinstance(node.right, ast.Name)
        and node.right.id in context.unit_names
    ):
        number = expression(context, node.left)
        if not isinstance(number, Literal) or number.type not in (ScalarType.INTEGER, ScalarType.REAL):
            context.fail(
                "quantity_literal",
                "Unit literals require a host numeric value; use Input[RotationalSpeed] for runtime inputs.",
                node,
            )
        try:
            speed = context.unit_names[node.right.id].__rmul__(number.value)
        except (ValueError, TypeError) as error:
            context.fail("quantity_literal", str(error), node)
        return Literal(**context.metadata(node), type=ScalarType.ROTATIONAL_SPEED, value=speed.rps)
    elif isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
        return Binary(
            **context.metadata(node),
            op=BINARY_OPERATORS[type(node.op)],
            left=expression(context, node.left),
            right=expression(context, node.right),
        )
    elif isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
        return Unary(**context.metadata(node), op=UNARY_OPERATORS[type(node.op)], operand=expression(context, node.operand))
    elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in BINARY_OPERATORS:
        return Binary(
            **context.metadata(node),
            op=BINARY_OPERATORS[type(node.ops[0])],
            left=expression(context, node.left),
            right=expression(context, node.comparators[0]),
        )
    elif isinstance(node, ast.BoolOp):
        result = expression(context, node.values[0])
        for value_node in node.values[1:]:
            result = Binary(
                **context.metadata(node), op=BINARY_OPERATORS[type(node.op)], left=result, right=expression(context, value_node)
            )
        return result
    else:
        context.fail("python_subset", f"Unsupported runtime expression: {type(node).__name__}.", node)
    if isinstance(value, RotationalSpeed):
        return Literal(**context.metadata(node), type=ScalarType.ROTATIONAL_SPEED, value=value.rps)
    scalar = {bool: ScalarType.BOOLEAN, int: ScalarType.INTEGER, float: ScalarType.REAL}.get(type(value))
    if scalar is None:
        context.fail("host_value", "Only scalar bool/int/float host values can enter runtime expressions.", node)
    return Literal(**context.metadata(node), type=scalar, value=cast(bool | int | float, value))
