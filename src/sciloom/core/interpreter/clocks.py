"""Explicit wall-clock input for deterministic reference execution."""

import re
from datetime import datetime
from typing import Protocol

from sciloom.core.ir.time_format import validate_wall_time_format


class WallClock(Protocol):
    """Provide an aware wall instant; the interpreter never selects a host clock."""

    def now(self) -> datetime:
        """Return one timezone-aware instant for a runtime read."""
        ...


class VirtualWallClock:
    """Return an explicitly supplied wall instant until it is changed.

    Args:
        instant: Aware datetime, interpreted in its own timezone.

    Raises:
        TypeError: The value is not a datetime.
        ValueError: The value has no usable UTC offset.

    No host clock is sampled. Sharing this object explicitly shares its current
    instant; it is independent of elapsed-time services.
    """

    def __init__(self, instant: datetime) -> None:
        self.set(instant)

    def now(self) -> datetime:
        """Return the supplied instant without advancing it."""
        return self._instant

    def set(self, instant: datetime) -> None:
        """Replace the instant after validation, retaining the old value on failure.

        Args:
            instant: New aware datetime.

        Raises:
            TypeError: The value is not a datetime.
            ValueError: The value has no usable UTC offset.
        """
        _require_aware(instant)
        self._instant = instant


def _require_aware(instant: datetime) -> None:
    if not isinstance(instant, datetime):
        raise TypeError("Wall clocks must return datetime values.")
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Wall time must be timezone-aware.")


def format_wall_time(instant: datetime, format: str) -> str:
    """Format one captured aware instant without locale/platform strftime rules."""
    _require_aware(instant)
    validate_wall_time_format(format)
    values = {
        "Y": f"{instant.year:04d}",
        "m": f"{instant.month:02d}",
        "d": f"{instant.day:02d}",
        "H": f"{instant.hour:02d}",
        "M": f"{instant.minute:02d}",
        "S": f"{instant.second:02d}",
        "%": "%",
    }
    return re.sub(r"%(.)", lambda match: values[match.group(1)], format, flags=re.DOTALL)
