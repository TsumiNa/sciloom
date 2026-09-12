"""Evaluate typed expressions using session reads and step accounting."""

from __future__ import annotations

import math
import operator
from typing import TYPE_CHECKING
from ..ir import BinaryOp, Expression, Literal, Reference, Unary, UnaryOp
from .values import ScalarValue, coerce, fail
if TYPE_CHECKING:
    from .runtime import Interpreter


def evaluate(session: Interpreter, expression: Expression, frame: dict[str, ScalarValue]) -> ScalarValue:
    session._tick(expression)
    if isinstance(expression, Literal):
        return coerce(expression.value, expression.type, expression)
    if isinstance(expression, Reference):
        return session._read(expression, frame)
    result: ScalarValue
    try:
        if isinstance(expression, Unary):
            value = evaluate(session, expression.operand, frame)
            if expression.op == UnaryOp.NOT:
                result = not value
            elif expression.op == UnaryOp.POSITIVE:
                result = +value
            else:
                result = -value
        else:
            left = evaluate(session, expression.left, frame)
            if expression.op == BinaryOp.AND and not left:
                return False
            if expression.op == BinaryOp.OR and left:
                return True
            right = evaluate(session, expression.right, frame)
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
            }[expression.op](left, right)
    except (ZeroDivisionError, OverflowError) as error:
        fail("numeric_error", str(error), expression)
    if isinstance(result, float) and not math.isfinite(result):
        fail("numeric_error", "Arithmetic produced a nonfinite value.", expression)
    return result
