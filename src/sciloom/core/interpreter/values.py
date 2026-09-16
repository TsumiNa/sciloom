"""Normalize runtime values and report execution failures."""

from __future__ import annotations

import math
from typing import NoReturn, assert_never, overload

from sciloom.core.diagnostics import Diagnostic, ExecutionError
from sciloom.core.ir.model import ListLiteral, Literal, Node
from sciloom.core.ir.types import QUANTITIES, ListType, ScalarType, ValueType
from sciloom.units import Duration, RotationalSpeed, Volume

ScalarValue = bool | int | float | str
RuntimeValue = ScalarValue | tuple[ScalarValue, ...]
InputScalar = ScalarValue | RotationalSpeed | Volume | Duration
# Lists are invariant: spell out homogeneous alternatives so list[float] etc.
# remain accepted without widening the public API to arbitrary sequences.
InputValue = (
    InputScalar
    | list[bool]
    | list[int]
    | list[float]
    | list[str]
    | list[RotationalSpeed]
    | list[Volume]
    | list[Duration]
    | list[InputScalar]
    | tuple[InputScalar, ...]
)
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


@overload
def coerce(value: RuntimeValue, scalar: ScalarType, node: Node) -> ScalarValue: ...


@overload
def coerce(value: RuntimeValue, scalar: ListType, node: Node) -> tuple[ScalarValue, ...]: ...


def coerce(value: RuntimeValue, scalar: ValueType, node: Node) -> RuntimeValue:
    if isinstance(scalar, ListType):
        if type(value) is not tuple:
            fail("runtime_type", f"Expected {scalar.value}.", node)
        return tuple(coerce(item, scalar.element_type, node) for item in value)
    allowed = {
        ScalarType.INTEGER: (int,),
        ScalarType.REAL: (int, float),
        ScalarType.BOOLEAN: (bool,),
        ScalarType.TEXT: (str,),
        ScalarType.ROTATIONAL_SPEED: (int, float),
        ScalarType.VOLUME: (int, float),
        ScalarType.DURATION: (int, float),
    }[scalar]
    if type(value) not in allowed:
        fail("runtime_type", f"Expected {scalar.value}, received {type(value).__name__}.", node)
    assert not isinstance(value, tuple)
    if scalar == ScalarType.TEXT:
        assert isinstance(value, str)
        return value
    assert not isinstance(value, str)
    try:
        result = float(value) if scalar in (ScalarType.REAL, *QUANTITIES) else value
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
    if isinstance(literal, Literal):
        return coerce(literal.value, literal.type, literal)
    assert_never(literal)


@overload
def input_value(value: InputValue, value_type: ScalarType, node: Node) -> ScalarValue: ...


@overload
def input_value(value: InputValue, value_type: ListType, node: Node) -> tuple[ScalarValue, ...]: ...


def input_value(value: InputValue, value_type: ValueType, node: Node) -> RuntimeValue:
    if isinstance(value_type, ListType):
        if type(value) not in (list, tuple):
            fail("runtime_type", f"Expected {value_type.value} input.", node)
        assert isinstance(value, (list, tuple))
        return tuple(input_value(item, value_type.element_type, node) for item in value)
    if value_type == ScalarType.VOLUME:
        if not isinstance(value, Volume):
            fail("runtime_type", "A volume input requires a Volume such as 1 * mL.", node)
        value = value.m3
    elif value_type == ScalarType.DURATION:
        if not isinstance(value, Duration):
            fail("runtime_type", "A duration input requires a Duration such as 1 * s.", node)
        value = value.seconds
    elif value_type == ScalarType.ROTATIONAL_SPEED:
        if not isinstance(value, RotationalSpeed):
            fail("runtime_type", "A rotational-speed input requires a quantity such as 600 * rpm.", node)
        value = value.rps
    elif isinstance(value, (RotationalSpeed, Volume, Duration)):
        fail("runtime_type", "A quantity cannot be passed to a scalar input.", node)
    if isinstance(value, (list, tuple)):
        fail("runtime_type", f"Expected {value_type.value}, received {type(value).__name__}.", node)
    return coerce(value, value_type, node)


@overload
def output_value(value: RuntimeValue, value_type: ScalarType) -> InputScalar: ...


@overload
def output_value(value: RuntimeValue, value_type: ListType) -> tuple[InputScalar, ...]: ...


def output_value(value: RuntimeValue, value_type: ValueType) -> OutputValue:
    if isinstance(value_type, ListType):
        assert isinstance(value, tuple)
        return tuple(output_value(item, value_type.element_type) for item in value)
    assert not isinstance(value, tuple)
    if value_type == ScalarType.VOLUME:
        assert not isinstance(value, str)
        return Volume(m3=value)
    if value_type == ScalarType.DURATION:
        assert not isinstance(value, str)
        return Duration(seconds=value)
    if value_type == ScalarType.ROTATIONAL_SPEED:
        assert not isinstance(value, str)
        return RotationalSpeed(rps=value)
    return value


def checked_index(value: RuntimeValue, index: RuntimeValue, node: Node) -> int:
    if not isinstance(value, tuple):
        fail("runtime_type", "Indexed access requires a list.", node)
    if type(index) is not int:
        fail("index_type", "List indices must be integers, excluding bool.", node)
    if index < 0 or index >= len(value):
        fail("index_bounds", f"Index {index} is outside a list of length {len(value)}.", node)
    return index
