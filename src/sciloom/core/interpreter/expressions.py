"""Evaluate typed expressions using session reads and step accounting."""

from __future__ import annotations

import math
import operator
from typing import TYPE_CHECKING, assert_never

from sciloom.core.ir import (
    Binary,
    BinaryOp,
    Expression,
    ListGet,
    ListLength,
    ListLiteral,
    Literal,
    Reference,
    Unary,
    UnaryOp,
)
from sciloom.core.ir.model import Node
from .values import RuntimeValue, ScalarValue, checked_index, coerce, fail

if TYPE_CHECKING:
    from .runtime import Interpreter


def evaluate(session: Interpreter, expression: Expression, frame: dict[str, RuntimeValue]) -> RuntimeValue:
    session._tick(expression)
    if isinstance(expression, ListLiteral):
        elements: list[ScalarValue] = []
        for item in expression.elements:
            element = evaluate(session, item, frame)
            assert not isinstance(element, tuple)  # Validated homogeneous scalar elements.
            elements.append(element)
        return coerce(tuple(elements), expression.type, expression)
    if isinstance(expression, (ListLength, ListGet)):
        values = evaluate(session, expression.value, frame)
        assert isinstance(values, tuple)
        if isinstance(expression, ListLength):
            return len(values)
        index = checked_index(values, evaluate(session, expression.index, frame), expression)
        return values[index]
    if isinstance(expression, Literal):
        return coerce(expression.value, expression.type, expression)
    if isinstance(expression, Reference):
        return session._read(expression, frame)
    result: ScalarValue
    try:
        if isinstance(expression, Unary):
            value = evaluate(session, expression.operand, frame)
            assert not isinstance(value, tuple)
            if expression.op == UnaryOp.NOT:
                result = not value
            elif expression.op == UnaryOp.POSITIVE:
                result = +value
            elif expression.op == UnaryOp.NEGATIVE:
                result = -value
            else:
                assert_never(expression.op)
        elif isinstance(expression, Binary):
            left = evaluate(session, expression.left, frame)
            assert not isinstance(left, tuple)
            if expression.op == BinaryOp.AND and not left:
                return False
            if expression.op == BinaryOp.OR and left:
                return True
            right = evaluate(session, expression.right, frame)
            assert not isinstance(right, tuple)
            result = apply_binary(expression.op, left, right, expression)
        else:
            assert_never(expression)
    except (ZeroDivisionError, OverflowError) as error:
        fail("numeric_error", str(error), expression)
    if isinstance(result, float) and not math.isfinite(result):
        fail("numeric_error", "Arithmetic produced a nonfinite value.", expression)
    return result


def apply_binary(op: BinaryOp, left: ScalarValue, right: ScalarValue, node: Node) -> ScalarValue:
    """Apply a validated scalar operation, also used by augmented list writes."""
    try:
        result = {
            BinaryOp.ADD: operator.add,
            BinaryOp.SUBTRACT: operator.sub,
            BinaryOp.MULTIPLY: operator.mul,
            BinaryOp.DIVIDE: operator.truediv,
            BinaryOp.EQUAL: operator.eq,
            BinaryOp.NOT_EQUAL: operator.ne,
            BinaryOp.LESS: operator.lt,
            BinaryOp.LESS_EQUAL: operator.le,
            BinaryOp.GREATER: operator.gt,
            BinaryOp.GREATER_EQUAL: operator.ge,
            BinaryOp.AND: operator.and_,
            BinaryOp.OR: operator.or_,
        }[op](left, right)
    except (ZeroDivisionError, OverflowError) as error:
        fail("numeric_error", str(error), node)
    if isinstance(result, float) and not math.isfinite(result):
        fail("numeric_error", "Arithmetic produced a nonfinite value.", node)
    return result
