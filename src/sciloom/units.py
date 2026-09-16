"""Finite physical quantities and explicit units, independent of the DSL."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import overload


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

    def __mul__(self, other: int | float) -> RotationalSpeed:
        return RotationalSpeed(rps=self.rps * _finite_number(other))

    def __rmul__(self, other: int | float) -> RotationalSpeed:
        return self * other

    @overload
    def __truediv__(self, other: RotationalSpeed | SpeedUnit) -> float: ...

    @overload
    def __truediv__(self, other: int | float) -> RotationalSpeed: ...

    def __truediv__(self, other: RotationalSpeed | SpeedUnit | int | float) -> RotationalSpeed | float:
        if isinstance(other, RotationalSpeed):
            return _finite_number(self.rps / other.rps)
        if isinstance(other, SpeedUnit):
            return _finite_number(self.rps / (1 * other).rps)
        return RotationalSpeed(rps=self.rps / _finite_number(other))


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


def _finite_number(value: int | float) -> float:
    """Normalize one number without implicit bool or text conversion."""
    if type(value) not in (int, float):
        raise TypeError("A quantity requires a number, excluding bool.")
    try:
        result = float(value)
    except OverflowError:
        raise ValueError("A quantity must be finite.") from None
    if not math.isfinite(result):
        raise ValueError("A quantity must be finite.")
    return result


@dataclass(frozen=True, kw_only=True)
class Volume:
    """A signed, finite volume in cubic metres.

    Args:
        m3: Canonical value; use the exported units in author programs.

    Raises:
        TypeError: A value is not numeric or has the wrong dimension.
        ValueError: A value is nonfinite or cannot be represented.
    """

    m3: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "m3", _finite_number(self.m3))

    def __add__(self, other: Volume) -> Volume:
        if not isinstance(other, Volume):
            raise TypeError("Addition requires two Volume values.")
        return Volume(m3=self.m3 + other.m3)

    def __sub__(self, other: Volume) -> Volume:
        if not isinstance(other, Volume):
            raise TypeError("Subtraction requires two Volume values.")
        return Volume(m3=self.m3 - other.m3)

    def __mul__(self, other: int | float) -> Volume:
        return Volume(m3=self.m3 * _finite_number(other))

    def __rmul__(self, other: int | float) -> Volume:
        return self * other

    @overload
    def __truediv__(self, other: Volume | VolumeUnit) -> float: ...

    @overload
    def __truediv__(self, other: int | float) -> Volume: ...

    def __truediv__(self, other: Volume | VolumeUnit | int | float) -> Volume | float:
        if isinstance(other, Volume):
            return _finite_number(self.m3 / other.m3)
        if isinstance(other, VolumeUnit):
            return _finite_number(self.m3 / other.scale)
        return Volume(m3=self.m3 / _finite_number(other))

    def __pos__(self) -> Volume:
        return self

    def __neg__(self) -> Volume:
        return Volume(m3=-self.m3)

    def __lt__(self, other: Volume) -> bool:
        if not isinstance(other, Volume):
            raise TypeError("Comparison requires two Volume values.")
        return self.m3 < other.m3

    def __le__(self, other: Volume) -> bool:
        if not isinstance(other, Volume):
            raise TypeError("Comparison requires two Volume values.")
        return self.m3 <= other.m3

    def __gt__(self, other: Volume) -> bool:
        if not isinstance(other, Volume):
            raise TypeError("Comparison requires two Volume values.")
        return self.m3 > other.m3

    def __ge__(self, other: Volume) -> bool:
        if not isinstance(other, Volume):
            raise TypeError("Comparison requires two Volume values.")
        return self.m3 >= other.m3


@dataclass(frozen=True, kw_only=True)
class Duration:
    """A signed, finite time interval in seconds.

    Args:
        seconds: Canonical value; use the exported units in author programs.

    Raises:
        TypeError: A value is not numeric or has the wrong dimension.
        ValueError: A value is nonfinite or cannot be represented.
    """

    seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "seconds", _finite_number(self.seconds))

    def __add__(self, other: Duration) -> Duration:
        if not isinstance(other, Duration):
            raise TypeError("Addition requires two Duration values.")
        return Duration(seconds=self.seconds + other.seconds)

    def __sub__(self, other: Duration) -> Duration:
        if not isinstance(other, Duration):
            raise TypeError("Subtraction requires two Duration values.")
        return Duration(seconds=self.seconds - other.seconds)

    def __mul__(self, other: int | float) -> Duration:
        return Duration(seconds=self.seconds * _finite_number(other))

    def __rmul__(self, other: int | float) -> Duration:
        return self * other

    @overload
    def __truediv__(self, other: Duration | DurationUnit) -> float: ...

    @overload
    def __truediv__(self, other: int | float) -> Duration: ...

    def __truediv__(self, other: Duration | DurationUnit | int | float) -> Duration | float:
        if isinstance(other, Duration):
            return _finite_number(self.seconds / other.seconds)
        if isinstance(other, DurationUnit):
            return _finite_number(self.seconds / other.scale)
        return Duration(seconds=self.seconds / _finite_number(other))

    def __pos__(self) -> Duration:
        return self

    def __neg__(self) -> Duration:
        return Duration(seconds=-self.seconds)

    def __lt__(self, other: Duration) -> bool:
        if not isinstance(other, Duration):
            raise TypeError("Comparison requires two Duration values.")
        return self.seconds < other.seconds

    def __le__(self, other: Duration) -> bool:
        if not isinstance(other, Duration):
            raise TypeError("Comparison requires two Duration values.")
        return self.seconds <= other.seconds

    def __gt__(self, other: Duration) -> bool:
        if not isinstance(other, Duration):
            raise TypeError("Comparison requires two Duration values.")
        return self.seconds > other.seconds

    def __ge__(self, other: Duration) -> bool:
        if not isinstance(other, Duration):
            raise TypeError("Comparison requires two Duration values.")
        return self.seconds >= other.seconds


class VolumeUnit(Enum):
    """Volume unit used in number-times-unit construction and explicit conversion."""

    UL = "uL"
    ML = "mL"
    L = "L"

    @property
    def scale(self) -> float:
        """Return cubic metres per unit."""
        return {VolumeUnit.UL: 1e-9, VolumeUnit.ML: 1e-6, VolumeUnit.L: 1e-3}[self]

    def __rmul__(self, value: int | float) -> Volume:
        return Volume(m3=_finite_number(value) * self.scale)


class DurationUnit(Enum):
    """Time unit used in number-times-unit construction and explicit conversion."""

    SECOND = "s"
    MINUTE = "minute"
    HOUR = "hour"

    @property
    def scale(self) -> float:
        """Return seconds per unit."""
        return {DurationUnit.SECOND: 1.0, DurationUnit.MINUTE: 60.0, DurationUnit.HOUR: 3600.0}[self]

    def __rmul__(self, value: int | float) -> Duration:
        return Duration(seconds=_finite_number(value) * self.scale)


uL = VolumeUnit.UL
"""Microlitres; one unit is 1e-9 cubic metres."""
mL = VolumeUnit.ML
"""Millilitres; one unit is 1e-6 cubic metres."""
L = VolumeUnit.L
"""Litres; one unit is 1e-3 cubic metres."""
s = DurationUnit.SECOND
"""Seconds; the canonical duration unit."""
minute = DurationUnit.MINUTE
"""Minutes; one unit is 60 seconds."""
hour = DurationUnit.HOUR
"""Hours; one unit is 3600 seconds."""
