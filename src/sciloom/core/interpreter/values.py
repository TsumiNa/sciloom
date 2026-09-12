"""Normalize runtime values and report execution failures."""

from __future__ import annotations

import math
from typing import NoReturn
from ...units import RotationalSpeed
from ..diagnostics import Diagnostic, ExecutionError
from ..ir.model import Node
from ..ir.types import ScalarType


ScalarValue = bool | int | float
InputValue = ScalarValue | RotationalSpeed


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


def coerce(value: ScalarValue, scalar: ScalarType, node: Node) -> ScalarValue:
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
