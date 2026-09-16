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
    TextLength,
    TextSplitPart,
    TextTrim,
    Unary,
    UnaryOp,
    WellName,
    ZoneCombine,
    ZoneFind,
    ZoneGet,
    ZoneLength,
    ZoneLiteral,
)
from sciloom.core.ir.model import Node
from sciloom.core.locations import Zone
from .environment import _require_service
from .values import RuntimeValue, ScalarValue, checked_index, coerce, fail

if TYPE_CHECKING:
    from .runtime import Interpreter


def evaluate(session: Interpreter, expression: Expression, frame: dict[str, RuntimeValue]) -> RuntimeValue:
    session._tick(expression)
    if isinstance(expression, ZoneLiteral):
        return Zone(well_ids=expression.well_ids)
    if isinstance(expression, ZoneFind):
        name = evaluate(session, expression.name, frame)
        assert isinstance(name, str)
        directory = _require_service(session.environment.locations, "locations", expression)
        return directory.find(name)
    if isinstance(expression, ZoneCombine):
        left_zone = evaluate(session, expression.left, frame)
        right_zone = evaluate(session, expression.right, frame)
        assert isinstance(left_zone, Zone) and isinstance(right_zone, Zone)
        return Zone(well_ids=tuple(dict.fromkeys((*left_zone.well_ids, *right_zone.well_ids))))
    if isinstance(expression, (ZoneLength, ZoneGet, WellName)):
        zone = evaluate(session, expression.value, frame)
        assert isinstance(zone, Zone)
        if isinstance(expression, ZoneLength):
            return len(zone)
        if isinstance(expression, ZoneGet):
            index = evaluate(session, expression.index, frame)
            if type(index) is not int:
                fail("index_type", "Zone indices must be integers, excluding bool.", expression)
            if index < 0 or index >= len(zone):
                fail("index_bounds", "Zone index is outside the selection.", expression)
            return zone[index]
        if len(zone) != 1:
            fail("zone_cardinality", "well_name requires exactly one well.", expression)
        directory = _require_service(session.environment.locations, "locations", expression)
        try:
            return directory.well_name(zone)
        except KeyError:
            fail("unknown_well", "The well identity is absent from the location directory.", expression)
    if isinstance(expression, (TextLength, TextTrim, TextSplitPart)):
        text_value = evaluate(session, expression.value, frame)
        assert isinstance(text_value, str)
        if isinstance(expression, TextLength):
            return len(text_value)
        if isinstance(expression, TextTrim):
            return text_value.strip(" \t\r\n")
        delimiter = evaluate(session, expression.delimiter, frame)
        index = evaluate(session, expression.index, frame)
        assert isinstance(delimiter, str) and type(index) is int
        if not delimiter:
            fail("text_delimiter", "Split delimiter must not be empty.", expression)
        if index < 0:
            fail("index_bounds", "Text part indices must be nonnegative.", expression)
        parts = text_value.split(delimiter)
        return parts[index] if index < len(parts) else ""
    if isinstance(expression, ListLiteral):
        elements: list[ScalarValue] = []
        for item in expression.elements:
            element = evaluate(session, item, frame)
            assert not isinstance(element, (tuple, Zone))  # Validated homogeneous scalar elements.
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
            assert not isinstance(value, (tuple, str, Zone))
            if expression.op == UnaryOp.NOT:
                result = not value
            elif expression.op == UnaryOp.POSITIVE:
                result = +value
            elif expression.op == UnaryOp.NEGATIVE:
                result = -value
            elif expression.op == UnaryOp.ABSOLUTE:
                result = abs(value)
            elif expression.op == UnaryOp.FLOOR:
                result = math.floor(value)
            elif expression.op == UnaryOp.ROUND:
                result = round(value)
            else:
                assert_never(expression.op)
        elif isinstance(expression, Binary):
            left = evaluate(session, expression.left, frame)
            assert not isinstance(left, (tuple, Zone))
            if expression.op == BinaryOp.AND and not left:
                return False
            if expression.op == BinaryOp.OR and left:
                return True
            right = evaluate(session, expression.right, frame)
            assert not isinstance(right, (tuple, Zone))
            result = apply_binary(expression.op, left, right, expression)
        else:
            assert_never(expression)
    except (ZeroDivisionError, OverflowError) as error:
        fail("numeric_error", str(error), expression)
    if isinstance(result, float) and not math.isfinite(result):
        fail("numeric_error", "Arithmetic produced a nonfinite value.", expression)
    return coerce(result, session._expression_types[expression.node_id], expression)


def apply_binary(op: BinaryOp, left: ScalarValue, right: ScalarValue, node: Node) -> ScalarValue:
    """Apply a validated scalar operation, also used by augmented list writes."""
    if isinstance(left, str) or isinstance(right, str):
        assert isinstance(left, str) and isinstance(right, str)
        if op == BinaryOp.ADD:
            return left + right
        if op == BinaryOp.EQUAL:
            return left == right
        if op == BinaryOp.NOT_EQUAL:
            return left != right
        fail("operator_type", "Text supports only concatenation and equality comparisons.", node)
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
