"""Translate typed Python expressions without executing runtime source."""

from __future__ import annotations

import ast
import inspect
from typing import TypeGuard, cast

from sciloom.core.ir import (
    Binary,
    BinaryOp,
    Expression,
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
)
from sciloom.flow import text
from sciloom.units import RotationalSpeed
from .context import LoweringContext

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


def expression(context: LoweringContext, node: ast.AST, expected: ValueType | None = None) -> Expression:
    if context.device_member(node) is not None:
        context.fail(
            "device_property_read",
            "Device getters are not supported; use a runtime variable for the configured value.",
            node,
        )
    if isinstance(node, ast.List):
        element_type = expected.element_type if isinstance(expected, ListType) else None
        elements = tuple(expression(context, item, element_type) for item in node.elts)
        return _list_literal(context, node, elements, expected)
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            context.fail("python_subset", "List slicing is unsupported.", node)
        return ListGet(
            **context.metadata(node), value=expression(context, node.value), index=expression(context, node.slice)
        )
    if is_length_call(node):
        if not context.source.allows_len:
            context.fail(
                "python_subset", "len must resolve to the Python builtin; shadowed calls are unsupported.", node
            )
        if len(node.args) != 1 or node.keywords:
            context.fail("python_subset", "len requires one positional list or text argument.", node)
        metadata = context.metadata(node)
        length_value = expression(context, node.args[0])
        if context.type_of(length_value) == ScalarType.TEXT:
            return TextLength(**metadata, value=length_value)
        return ListLength(**metadata, value=length_value)
    if isinstance(node, ast.Call):
        marker = context.static_object(node.func)
        if marker is text.trim or marker is text.split_part:
            intrinsic = text.trim if marker is text.trim else text.split_part
            if any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
                context.fail("python_subset", "Text operations do not accept argument expansion.", node)
            try:
                bound = inspect.signature(intrinsic).bind(
                    *node.args, **{k.arg: k.value for k in node.keywords if k.arg is not None}
                )
            except TypeError as error:
                context.fail("python_subset", str(error), node)
            arguments = {name: expression(context, value) for name, value in bound.arguments.items()}
            if marker is text.trim:
                return TextTrim(**context.metadata(node), value=arguments["value"])
            return TextSplitPart(
                **context.metadata(node),
                value=arguments["value"],
                delimiter=arguments["delimiter"],
                index=arguments["index"],
            )
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
        and node.right.id in context.source.unit_names
    ):
        number = expression(context, node.left)
        if not isinstance(number, Literal) or number.type not in (ScalarType.INTEGER, ScalarType.REAL):
            context.fail(
                "quantity_literal",
                "Unit literals require a host numeric value; use Input[RotationalSpeed] for runtime inputs.",
                node,
            )
        try:
            speed = context.source.unit_names[node.right.id].__rmul__(cast(int | float, number.value))
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
        return Unary(
            **context.metadata(node), op=UNARY_OPERATORS[type(node.op)], operand=expression(context, node.operand)
        )
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
                **context.metadata(node),
                op=BINARY_OPERATORS[type(node.op)],
                left=result,
                right=expression(context, value_node),
            )
        return result
    else:
        context.fail("python_subset", f"Unsupported runtime expression: {type(node).__name__}.", node)
    if isinstance(value, RotationalSpeed):
        return Literal(**context.metadata(node), type=ScalarType.ROTATIONAL_SPEED, value=value.rps)
    scalar = {bool: ScalarType.BOOLEAN, int: ScalarType.INTEGER, float: ScalarType.REAL, str: ScalarType.TEXT}.get(
        type(value)
    )
    if scalar is None:
        context.fail("host_value", "Only scalar bool/int/float/str host values can enter runtime expressions.", node)
    return Literal(**context.metadata(node), type=scalar, value=cast(bool | int | float | str, value))


def is_length_call(node: ast.AST) -> TypeGuard[ast.Call]:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def is_expression_call(context: LoweringContext, node: ast.AST) -> bool:
    if is_length_call(node):
        return True
    if isinstance(node, ast.Call):
        marker = context.static_object(node.func)
        return marker is text.trim or marker is text.split_part
    return False


def _list_literal(
    context: LoweringContext, node: ast.AST, elements: tuple[Expression, ...], expected: ValueType | None
) -> ListLiteral:
    if isinstance(expected, ListType):
        list_type = expected
    else:
        types = {context.type_of(element) for element in elements}
        if not types:
            context.fail("list_type", "An empty list needs a declared list element type.", node)
        if types <= {ScalarType.INTEGER, ScalarType.REAL}:
            element_type = ScalarType.REAL if ScalarType.REAL in types else ScalarType.INTEGER
        elif len(types) == 1 and isinstance(next(iter(types)), ScalarType):
            only_type = next(iter(types))
            assert isinstance(only_type, ScalarType)
            element_type = only_type
        else:
            context.fail("list_type", "Lists must be one-dimensional and homogeneous.", node)
        list_type = ListType(element_type=element_type)
    return ListLiteral(**context.metadata(node), type=list_type, elements=elements)
