"""The initial physical quantity: rotational speed, canonicalized to revolutions/s."""

import math
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, kw_only=True)
class RotationalSpeed:
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
rps = SpeedUnit.RPS
