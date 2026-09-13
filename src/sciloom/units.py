"""The initial physical quantity: rotational speed, canonicalized to revolutions/s."""

import math
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, kw_only=True)
class RotationalSpeed:
    """A nonnegative, finite rotational speed in canonical revolutions per second.

    Use unit literals such as `600 * rpm` in experiment code.

    Args:
        rps: Canonical revolutions per second; integers widen to float.

    Raises:
        TypeError: The value is not an int or float (bool is rejected).
        ValueError: The value is negative, nonfinite or cannot be represented."""
    rps: float

    def __post_init__(self) -> None:
        if type(self.rps) not in (int, float):
            raise TypeError("Rotational speed requires a numeric value.")
        try:
            value = float(self.rps)
        except OverflowError:
            raise ValueError("Rotational speed must be finite.") from None
        if not math.isfinite(value) or value < 0:
            raise ValueError("Rotational speed must be finite and nonnegative.")
        object.__setattr__(self, "rps", value)


class SpeedUnit(Enum):
    """Unit for constructing a rotational speed by multiplying a numeric literal."""
    RPM = "rpm"
    RPS = "rps"

    def __rmul__(self, value: int | float) -> RotationalSpeed:
        if type(value) not in (int, float):
            raise TypeError("A speed literal requires a number, not bool or text.")
        try:
            canonical = float(value) / 60 if self == SpeedUnit.RPM else float(value)
        except OverflowError:
            raise ValueError("Rotational speed must be finite.") from None
        return RotationalSpeed(rps=canonical)


rpm = SpeedUnit.RPM
"""Revolutions per minute; multiply a numeric literal by this unit."""
rps = SpeedUnit.RPS
"""Revolutions per second; the canonical rotational-speed unit."""
