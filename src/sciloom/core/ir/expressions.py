"""Expression type and symbol checks shared by program validation."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .model import (
    BinaryOp,
    Expression,
    FunctionIR,
    ListGet,
    ListLength,
    ListLiteral,
    Literal,
    Node,
    Reference,
    Unary,
    UnaryOp,
    Variable,
)
from .types import ListType, ScalarType, ValueType, is_assignable

Report = Callable[[str, str, str, Node | None], None]


class ExpressionChecker:
    def __init__(self, symbols: Mapping[str, Variable], report: Report) -> None:
        self.symbols = symbols
        self.report = report

    def check(self, expr: Expression, function: FunctionIR, path: str) -> ValueType | None:
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
                ScalarType.ROTATIONAL_SPEED: type(expr.value) in (int, float) and expr.value >= 0,
            }[expr.type]
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
            if expr.op == UnaryOp.NOT:
                if operand == ScalarType.BOOLEAN:
                    return ScalarType.BOOLEAN
            elif operand in (ScalarType.INTEGER, ScalarType.REAL):
                return operand
            self.report("operator_type", f"Operator {expr.op.value!r} cannot take {operand.value}.", path, expr)
            return None
        left = self.check(expr.left, function, f"{path}.left")
        right = self.check(expr.right, function, f"{path}.right")
        return self.binary(expr.op, left, right, path, expr)

    def binary(
        self, op: BinaryOp, left: ValueType | None, right: ValueType | None, path: str, node: Node
    ) -> ScalarType | None:
        if left is None or right is None:
            return None
        if isinstance(left, ListType) or isinstance(right, ListType):
            self.report(
                "operator_type", "Lists do not support implicit arithmetic, comparisons or truthiness.", path, node
            )
            return None
        numeric = left in (ScalarType.INTEGER, ScalarType.REAL) and right in (ScalarType.INTEGER, ScalarType.REAL)
        if op in (BinaryOp.AND, BinaryOp.OR):
            if left == right == ScalarType.BOOLEAN:
                return ScalarType.BOOLEAN
        elif op in (BinaryOp.EQUAL, BinaryOp.NOT_EQUAL):
            if left == right or numeric:
                return ScalarType.BOOLEAN
        elif op in (BinaryOp.LESS, BinaryOp.LESS_EQUAL, BinaryOp.GREATER, BinaryOp.GREATER_EQUAL):
            if numeric:
                return ScalarType.BOOLEAN
        elif numeric:
            return ScalarType.REAL if op == BinaryOp.DIVIDE or ScalarType.REAL in (left, right) else ScalarType.INTEGER
        self.report(
            "operator_type", f"Operator {op.value!r} cannot combine {left.value} and {right.value}.", path, node
        )
        return None
