"""Normalize runtime values and report execution failures."""

from __future__ import annotations

import math
from typing import NoReturn
from ...units import RotationalSpeed
from ..diagnostics import Diagnostic, ExecutionError
from ..ir.model import Literal, ListLiteral, Node
from ..ir.types import ListType, ScalarType, ValueType


ScalarValue = bool | int | float
RuntimeValue = ScalarValue | tuple[ScalarValue, ...]
InputScalar = ScalarValue | RotationalSpeed
InputValue = InputScalar | list[InputScalar] | tuple[InputScalar, ...]
OutputValue = InputScalar | tuple[InputScalar, ...]


def fail(code: str, message: str, node: Node | None = None) -> NoReturn:
    raise ExecutionError(
        (
            Diagnostic(
                code=code,
                message=message,
                path="$.execution",
                node_id=node.node_id if node else None,
                source=node.source if node else None,
            ),
        )
    )


def coerce(value: RuntimeValue, scalar: ValueType, node: Node) -> RuntimeValue:
    if isinstance(scalar, ListType):
        if type(value) is not tuple:
            fail("runtime_type", f"Expected {scalar.value}.", node)
        return tuple(coerce(item, scalar.element_type, node) for item in value)
    allowed = {
        ScalarType.INTEGER: (int,),
        ScalarType.REAL: (int, float),
        ScalarType.BOOLEAN: (bool,),
        ScalarType.ROTATIONAL_SPEED: (int, float),
    }[scalar]
    if type(value) not in allowed:
        fail("runtime_type", f"Expected {scalar.value}, received {type(value).__name__}.", node)
    try:
        result = float(value) if scalar in (ScalarType.REAL, ScalarType.ROTATIONAL_SPEED) else value
    except OverflowError:
        fail("numeric_error", "Value cannot be represented as a finite real.", node)
    if isinstance(result, float) and not math.isfinite(result):
        fail("numeric_error", "Nonfinite real value.", node)
    if scalar == ScalarType.ROTATIONAL_SPEED and result < 0:
        fail("invalid_speed", "Rotational speed must be nonnegative.", node)
    return result


def initial_value(literal: Literal | ListLiteral) -> RuntimeValue:
    if isinstance(literal, ListLiteral):
        values = []
        for element in literal.elements:
            assert isinstance(element, Literal)  # Shared validation requires constant initializers.
            values.append(element.value)
        return coerce(tuple(values), literal.type, literal)
    return coerce(literal.value, literal.type, literal)


def input_value(value: InputValue, value_type: ValueType, node: Node) -> RuntimeValue:
    if isinstance(value_type, ListType):
        if type(value) not in (list, tuple):
            fail("runtime_type", f"Expected {value_type.value} input.", node)
        return tuple(input_value(item, value_type.element_type, node) for item in value)
    if value_type == ScalarType.ROTATIONAL_SPEED:
        if not isinstance(value, RotationalSpeed):
            fail("runtime_type", "A rotational-speed input requires a quantity such as 600 * rpm.", node)
        value = value.rps
    elif isinstance(value, RotationalSpeed):
        fail("runtime_type", "A quantity cannot be passed to a scalar input.", node)
    return coerce(value, value_type, node)


def output_value(value: RuntimeValue, value_type: ValueType) -> OutputValue:
    if isinstance(value_type, ListType):
        assert isinstance(value, tuple)
        return tuple(output_value(item, value_type.element_type) for item in value)
    return RotationalSpeed(rps=value) if value_type == ScalarType.ROTATIONAL_SPEED else value


def checked_index(value: RuntimeValue, index: RuntimeValue, node: Node) -> int:
    if not isinstance(value, tuple):
        fail("runtime_type", "Indexed access requires a list.", node)
    if type(index) is not int:
        fail("index_type", "List indices must be integers, excluding bool.", node)
    if index < 0 or index >= len(value):
        fail("index_bounds", f"Index {index} is outside a list of length {len(value)}.", node)
    return index
