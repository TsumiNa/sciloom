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

    def __abs__(self) -> Volume:
        """Return the nonnegative magnitude, retaining the volume dimension."""
        return Volume(m3=abs(self.m3))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Volume):
            raise TypeError("Comparison requires two Volume values.")
        return self.m3 == other.m3

    def __hash__(self) -> int:
        return hash((Volume, self.m3))

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

    def __abs__(self) -> Duration:
        """Return the nonnegative magnitude, retaining the duration dimension."""
        return Duration(seconds=abs(self.seconds))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            raise TypeError("Comparison requires two Duration values.")
        return self.seconds == other.seconds

    def __hash__(self) -> int:
        return hash((Duration, self.seconds))

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


@dataclass(frozen=True, kw_only=True)
class Temperature:
    """An absolute temperature in kelvin, finite and at or above absolute zero.

    Args:
        kelvin: Canonical absolute value; use 20 * degC for Celsius literals.

    Raises:
        TypeError: A value has the wrong type or dimension.
        ValueError: A value is negative or nonfinite.
    """

    kelvin: float

    def __post_init__(self) -> None:
        value = _finite_number(self.kelvin)
        if value < 0:
            raise ValueError("Absolute temperature must be nonnegative in kelvin.")
        object.__setattr__(self, "kelvin", value)

    def __add__(self, other: TemperatureDifference) -> Temperature:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("An absolute temperature can only add a temperature difference.")
        return Temperature(kelvin=self.kelvin + other.kelvin)

    @overload
    def __sub__(self, other: Temperature) -> TemperatureDifference: ...

    @overload
    def __sub__(self, other: TemperatureDifference) -> Temperature: ...

    def __sub__(self, other: Temperature | TemperatureDifference) -> Temperature | TemperatureDifference:
        if isinstance(other, Temperature):
            return TemperatureDifference(kelvin=self.kelvin - other.kelvin)
        if isinstance(other, TemperatureDifference):
            return Temperature(kelvin=self.kelvin - other.kelvin)
        raise TypeError("Temperature subtraction requires an absolute temperature or difference.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Temperature):
            raise TypeError("Comparison requires two Temperature values.")
        return self.kelvin == other.kelvin

    def __hash__(self) -> int:
        return hash((Temperature, self.kelvin))

    def __lt__(self, other: Temperature) -> bool:
        if not isinstance(other, Temperature):
            raise TypeError("Comparison requires two Temperature values.")
        return self.kelvin < other.kelvin

    def __le__(self, other: Temperature) -> bool:
        if not isinstance(other, Temperature):
            raise TypeError("Comparison requires two Temperature values.")
        return self.kelvin <= other.kelvin

    def __gt__(self, other: Temperature) -> bool:
        if not isinstance(other, Temperature):
            raise TypeError("Comparison requires two Temperature values.")
        return self.kelvin > other.kelvin

    def __ge__(self, other: Temperature) -> bool:
        if not isinstance(other, Temperature):
            raise TypeError("Comparison requires two Temperature values.")
        return self.kelvin >= other.kelvin


@dataclass(frozen=True, kw_only=True)
class TemperatureDifference:
    """A signed, finite temperature difference in kelvin.

    Args:
        kelvin: Canonical value; profile-specific limits are separate.

    Raises:
        TypeError: A value has the wrong type or dimension.
        ValueError: A value is nonfinite.
    """

    kelvin: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kelvin", _finite_number(self.kelvin))

    @overload
    def __add__(self, other: TemperatureDifference) -> TemperatureDifference: ...

    @overload
    def __add__(self, other: Temperature) -> Temperature: ...

    def __add__(self, other: TemperatureDifference | Temperature) -> TemperatureDifference | Temperature:
        if isinstance(other, Temperature):
            return other + self
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Addition requires a temperature difference or absolute temperature.")
        return TemperatureDifference(kelvin=self.kelvin + other.kelvin)

    def __sub__(self, other: TemperatureDifference) -> TemperatureDifference:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Subtraction requires two TemperatureDifference values.")
        return TemperatureDifference(kelvin=self.kelvin - other.kelvin)

    def __mul__(self, other: int | float) -> TemperatureDifference:
        return TemperatureDifference(kelvin=self.kelvin * _finite_number(other))

    def __rmul__(self, other: int | float) -> TemperatureDifference:
        return self * other

    @overload
    def __truediv__(self, other: TemperatureDifference | TemperatureDifferenceUnit) -> float: ...

    @overload
    def __truediv__(self, other: int | float) -> TemperatureDifference: ...

    def __truediv__(
        self, other: TemperatureDifference | TemperatureDifferenceUnit | int | float
    ) -> TemperatureDifference | float:
        if isinstance(other, TemperatureDifference):
            return _finite_number(self.kelvin / other.kelvin)
        if isinstance(other, TemperatureDifferenceUnit):
            return _finite_number(self.kelvin / other.scale)
        return TemperatureDifference(kelvin=self.kelvin / _finite_number(other))

    def __pos__(self) -> TemperatureDifference:
        return self

    def __neg__(self) -> TemperatureDifference:
        return TemperatureDifference(kelvin=-self.kelvin)

    def __abs__(self) -> TemperatureDifference:
        return TemperatureDifference(kelvin=abs(self.kelvin))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Comparison requires two TemperatureDifference values.")
        return self.kelvin == other.kelvin

    def __hash__(self) -> int:
        return hash((TemperatureDifference, self.kelvin))

    def __lt__(self, other: TemperatureDifference) -> bool:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Comparison requires two TemperatureDifference values.")
        return self.kelvin < other.kelvin

    def __le__(self, other: TemperatureDifference) -> bool:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Comparison requires two TemperatureDifference values.")
        return self.kelvin <= other.kelvin

    def __gt__(self, other: TemperatureDifference) -> bool:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Comparison requires two TemperatureDifference values.")
        return self.kelvin > other.kelvin

    def __ge__(self, other: TemperatureDifference) -> bool:
        if not isinstance(other, TemperatureDifference):
            raise TypeError("Comparison requires two TemperatureDifference values.")
        return self.kelvin >= other.kelvin


@dataclass(frozen=True, kw_only=True)
class TemperatureRate:
    """A signed, finite temperature change rate in kelvin per second.

    Args:
        kelvin_per_second: Canonical value; profile-specific limits are separate.

    Raises:
        TypeError: A value has the wrong type or dimension.
        ValueError: A value is nonfinite.
    """

    kelvin_per_second: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kelvin_per_second", _finite_number(self.kelvin_per_second))

    def __add__(self, other: TemperatureRate) -> TemperatureRate:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Addition requires two TemperatureRate values.")
        return TemperatureRate(kelvin_per_second=self.kelvin_per_second + other.kelvin_per_second)

    def __sub__(self, other: TemperatureRate) -> TemperatureRate:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Subtraction requires two TemperatureRate values.")
        return TemperatureRate(kelvin_per_second=self.kelvin_per_second - other.kelvin_per_second)

    def __mul__(self, other: int | float) -> TemperatureRate:
        return TemperatureRate(kelvin_per_second=self.kelvin_per_second * _finite_number(other))

    def __rmul__(self, other: int | float) -> TemperatureRate:
        return self * other

    @overload
    def __truediv__(self, other: TemperatureRate | TemperatureRateUnit) -> float: ...

    @overload
    def __truediv__(self, other: int | float) -> TemperatureRate: ...

    def __truediv__(self, other: TemperatureRate | TemperatureRateUnit | int | float) -> TemperatureRate | float:
        if isinstance(other, TemperatureRate):
            return _finite_number(self.kelvin_per_second / other.kelvin_per_second)
        if isinstance(other, TemperatureRateUnit):
            return _finite_number(self.kelvin_per_second / other.scale)
        return TemperatureRate(kelvin_per_second=self.kelvin_per_second / _finite_number(other))

    def __pos__(self) -> TemperatureRate:
        return self

    def __neg__(self) -> TemperatureRate:
        return TemperatureRate(kelvin_per_second=-self.kelvin_per_second)

    def __abs__(self) -> TemperatureRate:
        return TemperatureRate(kelvin_per_second=abs(self.kelvin_per_second))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Comparison requires two TemperatureRate values.")
        return self.kelvin_per_second == other.kelvin_per_second

    def __hash__(self) -> int:
        return hash((TemperatureRate, self.kelvin_per_second))

    def __lt__(self, other: TemperatureRate) -> bool:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Comparison requires two TemperatureRate values.")
        return self.kelvin_per_second < other.kelvin_per_second

    def __le__(self, other: TemperatureRate) -> bool:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Comparison requires two TemperatureRate values.")
        return self.kelvin_per_second <= other.kelvin_per_second

    def __gt__(self, other: TemperatureRate) -> bool:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Comparison requires two TemperatureRate values.")
        return self.kelvin_per_second > other.kelvin_per_second

    def __ge__(self, other: TemperatureRate) -> bool:
        if not isinstance(other, TemperatureRate):
            raise TypeError("Comparison requires two TemperatureRate values.")
        return self.kelvin_per_second >= other.kelvin_per_second


class TemperatureUnit(Enum):
    """Absolute units construct values; they do not scale existing temperatures."""

    CELSIUS = "degC"
    KELVIN = "kelvin"

    def __rmul__(self, value: int | float) -> Temperature:
        numeric = _finite_number(value)
        return Temperature(kelvin=numeric + 273.15 if self == TemperatureUnit.CELSIUS else numeric)


class TemperatureDifferenceUnit(Enum):
    """Difference units have equal scale and no Celsius offset."""

    CELSIUS = "delta_degC"
    KELVIN = "delta_kelvin"

    @property
    def scale(self) -> float:
        """Return kelvin per unit of temperature difference."""
        return 1.0

    def __rmul__(self, value: int | float) -> TemperatureDifference:
        return TemperatureDifference(kelvin=_finite_number(value))


class TemperatureRateUnit(Enum):
    """Units for signed temperature change rates."""

    CELSIUS_PER_MINUTE = "degC_per_min"
    KELVIN_PER_SECOND = "kelvin_per_s"

    @property
    def scale(self) -> float:
        """Return kelvin per second per unit."""
        return 1 / 60 if self == TemperatureRateUnit.CELSIUS_PER_MINUTE else 1.0

    def __rmul__(self, value: int | float) -> TemperatureRate:
        return TemperatureRate(kelvin_per_second=_finite_number(value) * self.scale)


degC = TemperatureUnit.CELSIUS
"""Absolute Celsius literal unit, using the standard 273.15 kelvin offset."""
kelvin = TemperatureUnit.KELVIN
"""Absolute kelvin literal unit."""
delta_degC = TemperatureDifferenceUnit.CELSIUS
"""Celsius temperature differences, with no absolute offset."""
delta_kelvin = TemperatureDifferenceUnit.KELVIN
"""Kelvin temperature differences."""
degC_per_min = TemperatureRateUnit.CELSIUS_PER_MINUTE
"""Celsius degrees of temperature change per minute."""
kelvin_per_s = TemperatureRateUnit.KELVIN_PER_SECOND
"""Kelvin of temperature change per second."""
