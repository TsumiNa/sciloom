"""Typed runtime logging vocabulary for experiment authors."""

from sciloom.units import Duration, RotationalSpeed, Temperature, TemperatureDifference, TemperatureRate, Volume


def log(
    value: bool
    | int
    | float
    | str
    | RotationalSpeed
    | Volume
    | Duration
    | Temperature
    | TemperatureDifference
    | TemperatureRate,
    *,
    category: str,
    stream: str,
) -> None:
    """Record a value in the generated program's log.

    Args:
        value: Scalar or quantity to capture; no implicit list/object formatting.
        category: Runtime text identifying the log category.
        stream: Runtime text identifying the stream within that category.

    Value, category and stream are evaluated once in that order. The operation
    does not measure hardware or configure application-level log storage.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.
    """
    raise TypeError("Logging belongs in compiled @runtime methods.")
