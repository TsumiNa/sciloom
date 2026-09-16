"""Expression type and symbol checks shared by program validation."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import assert_never

from .model import (
    Binary,
    BinaryOp,
    Expression,
    FunctionIR,
    ListGet,
    ListLength,
    ListLiteral,
    Literal,
    Node,
    Reference,
    TextLength,
    TextSplitPart,
    TextTrim,
    Unary,
    UnaryOp,
    Variable,
    WellName,
    ZoneCombine,
    ZoneFind,
    ZoneGet,
    ZoneLength,
    ZoneLiteral,
)
from .types import QUANTITIES, SIGNED_QUANTITIES, ListType, ScalarType, ValueType, ZoneType, is_assignable

Report = Callable[[str, str, str, Node | None], None]


class ExpressionChecker:
    def __init__(self, symbols: Mapping[str, Variable], report: Report) -> None:
        self.symbols = symbols
        self.report = report

    def check(self, expr: Expression, function: FunctionIR, path: str) -> ValueType | None:
        if isinstance(expr, ZoneLiteral):
            if any(not identity.strip() for identity in expr.well_ids) or len(set(expr.well_ids)) != len(expr.well_ids):
                self.report("zone_literal", "Zone well identities must be nonempty and unique.", path, expr)
            return ZoneType()
        if isinstance(expr, ZoneFind):
            name_type = self.check(expr.name, function, f"{path}.name")
            if name_type is not None and name_type != ScalarType.TEXT:
                self.report("text_type", "Zone names must be text.", path, expr)
            return ZoneType()
        if isinstance(expr, (ZoneCombine, ZoneLength, ZoneGet, WellName)):
            operands = (
                (("left", expr.left), ("right", expr.right))
                if isinstance(expr, ZoneCombine)
                else (("value", expr.value),)
            )
            for name, value in operands:
                value_type = self.check(value, function, f"{path}.{name}")
                if value_type is not None and not isinstance(value_type, ZoneType):
                    self.report("zone_type", "Operation requires a Zone value.", f"{path}.{name}", value)
            if isinstance(expr, ZoneGet):
                index = self.check(expr.index, function, f"{path}.index")
                if index is not None and index != ScalarType.INTEGER:
                    self.report(
                        "index_type", "Zone indices must be integers, excluding bool.", f"{path}.index", expr.index
                    )
            if isinstance(expr, WellName):
                if isinstance(expr.value, ZoneLiteral) and len(expr.value.well_ids) != 1:
                    self.report("zone_cardinality", "well_name requires exactly one well.", path, expr)
                return ScalarType.TEXT
            return ScalarType.INTEGER if isinstance(expr, ZoneLength) else ZoneType()
        if isinstance(expr, (TextLength, TextTrim, TextSplitPart)):
            value_type = self.check(expr.value, function, f"{path}.value")
            if value_type is not None and value_type != ScalarType.TEXT:
                self.report("text_type", "Operation requires text.", f"{path}.value", expr.value)
            if isinstance(expr, TextSplitPart):
                delimiter = self.check(expr.delimiter, function, f"{path}.delimiter")
                index = self.check(expr.index, function, f"{path}.index")
                if delimiter is not None and delimiter != ScalarType.TEXT:
                    self.report("text_type", "Delimiter must be text.", f"{path}.delimiter", expr.delimiter)
                if index is not None and index != ScalarType.INTEGER:
                    self.report(
                        "index_type", "Part indices must be integers, excluding bool.", f"{path}.index", expr.index
                    )
            return ScalarType.INTEGER if isinstance(expr, TextLength) else ScalarType.TEXT
        if isinstance(expr, ListLiteral):
            for i, element in enumerate(expr.elements):
                element_type = self.check(element, function, f"{path}.elements[{i}]")
                if element_type is not None and not is_assignable(element_type, expr.type.element_type):
                    self.report(
                        "list_element_type",
                        f"Expected {expr.type.element_type.value} elements.",
                        f"{path}.elements[{i}]",
                        element,
                    )
            return expr.type
        if isinstance(expr, (ListLength, ListGet)):
            container = self.check(expr.value, function, f"{path}.value")
            if isinstance(expr, ListGet):
                index = self.check(expr.index, function, f"{path}.index")
                if index is not None and index != ScalarType.INTEGER:
                    self.report(
                        "index_type", "List indices must be integers, excluding bool.", f"{path}.index", expr.index
                    )
            if container is not None and not isinstance(container, ListType):
                self.report("list_type", "Operation requires a list value.", path, expr)
                return None
            if isinstance(container, ListType):
                return ScalarType.INTEGER if isinstance(expr, ListLength) else container.element_type
            return None
        if isinstance(expr, Literal):
            valid = {
                ScalarType.INTEGER: type(expr.value) is int,
                ScalarType.REAL: type(expr.value) in (int, float),
                ScalarType.BOOLEAN: type(expr.value) is bool,
                ScalarType.TEXT: type(expr.value) is str,
                ScalarType.VOLUME: type(expr.value) in (int, float),
                ScalarType.DURATION: type(expr.value) in (int, float),
                ScalarType.ROTATIONAL_SPEED: type(expr.value) in (int, float)
                and isinstance(expr.value, (int, float))
                and expr.value >= 0,
            }[expr.type]
            if valid and expr.type in SIGNED_QUANTITIES:
                assert isinstance(expr.value, (int, float))
                try:
                    valid = math.isfinite(expr.value)
                except OverflowError:
                    valid = False
            if not valid:
                self.report("literal_type", f"Value does not represent {expr.type.value}.", path, expr)
                return None
            return expr.type
        if isinstance(expr, Reference):
            variable = self.symbols.get(expr.symbol_id)
            if variable is None:
                self.report("unknown_symbol", f"Unknown variable {expr.symbol_id!r}.", path, expr)
                return None
            if variable.owner_id != function.node_id or variable not in function.variables:
                self.report(
                    "symbol_scope", "Variable belongs to a different function; globals are not implicit.", path, expr
                )
                return None
            return variable.type
        if isinstance(expr, Unary):
            operand = self.check(expr.operand, function, f"{path}.operand")
            if operand is None:
                return None
            op = expr.op
            if op == UnaryOp.NOT:
                if operand == ScalarType.BOOLEAN:
                    return ScalarType.BOOLEAN
            elif op in (UnaryOp.POSITIVE, UnaryOp.NEGATIVE, UnaryOp.ABSOLUTE):
                if operand in (ScalarType.INTEGER, ScalarType.REAL, *SIGNED_QUANTITIES):
                    return operand
            elif op in (UnaryOp.FLOOR, UnaryOp.ROUND):
                if operand in (ScalarType.INTEGER, ScalarType.REAL):
                    return ScalarType.INTEGER
            else:
                assert_never(op)
            self.report("operator_type", f"Operator {expr.op.value!r} cannot take {operand.value}.", path, expr)
            return None
        if not isinstance(expr, Binary):
            assert_never(expr)
        left = self.check(expr.left, function, f"{path}.left")
        right = self.check(expr.right, function, f"{path}.right")
        return self.binary(expr.op, left, right, path, expr)

    def binary(
        self, op: BinaryOp, left: ValueType | None, right: ValueType | None, path: str, node: Node
    ) -> ScalarType | None:
        if left is None or right is None:
            return None
        if isinstance(left, (ListType, ZoneType)) or isinstance(right, (ListType, ZoneType)):
            self.report(
                "operator_type",
                "Lists and Zones do not support implicit arithmetic, comparisons or truthiness.",
                path,
                node,
            )
            return None
        numeric = left in (ScalarType.INTEGER, ScalarType.REAL) and right in (ScalarType.INTEGER, ScalarType.REAL)
        if op == BinaryOp.ADD and left == right == ScalarType.TEXT:
            return ScalarType.TEXT
        if op in (BinaryOp.AND, BinaryOp.OR):
            if left == right == ScalarType.BOOLEAN:
                return ScalarType.BOOLEAN
        elif op in (BinaryOp.EQUAL, BinaryOp.NOT_EQUAL):
            if left == right or numeric:
                return ScalarType.BOOLEAN
        elif op in (BinaryOp.LESS, BinaryOp.LESS_EQUAL, BinaryOp.GREATER, BinaryOp.GREATER_EQUAL):
            if numeric or left == right and left in SIGNED_QUANTITIES:
                return ScalarType.BOOLEAN
        elif op in (BinaryOp.ADD, BinaryOp.SUBTRACT) and left == right and left in SIGNED_QUANTITIES:
            return left
        elif op == BinaryOp.DIVIDE and left == right and left in QUANTITIES:
            return ScalarType.REAL
        elif (
            op in (BinaryOp.MULTIPLY, BinaryOp.DIVIDE)
            and left in QUANTITIES
            and right in (ScalarType.INTEGER, ScalarType.REAL)
        ):
            return left
        elif op == BinaryOp.MULTIPLY and right in QUANTITIES and left in (ScalarType.INTEGER, ScalarType.REAL):
            return right
        elif numeric:
            return ScalarType.REAL if op == BinaryOp.DIVIDE or ScalarType.REAL in (left, right) else ScalarType.INTEGER
        self.report(
            "operator_type", f"Operator {op.value!r} cannot combine {left.value} and {right.value}.", path, node
        )
        return None
