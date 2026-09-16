"""Explicit wall time is independent of host clocks and rejects naive values."""

from datetime import datetime, timedelta, timezone

import pytest

from .clocks import VirtualWallClock, format_wall_time


def test_virtual_wall_clock_changes_only_when_set_and_validates_before_change():
    first = datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone(timedelta(hours=9)))
    second = datetime(2026, 9, 17, tzinfo=timezone.utc)
    clock = VirtualWallClock(first)
    assert clock.now() == first
    assert clock.now() == first
    for bad in (datetime(2026, 9, 16), None, 123):
        with pytest.raises((ValueError, TypeError)):
            clock.set(bad)
        assert clock.now() == first
    clock.set(second)
    assert clock.now() == second


@pytest.mark.parametrize("value", [datetime(2026, 9, 16), None, "2026-09-16"])
def test_virtual_clock_requires_explicit_aware_datetime(value):
    with pytest.raises((ValueError, TypeError)):
        VirtualWallClock(value)


def test_format_uses_numeric_fields_and_supplied_timezone():
    instant = datetime(1, 2, 3, 4, 5, 6, tzinfo=timezone(timedelta(hours=9)))
    assert format_wall_time(instant, "%Y-%m-%d_%H%M%S %%") == "0001-02-03_040506 %"
    assert format_wall_time(instant, "試料 ' \\ \n%%%Y") == "試料 ' \\ \n%0001"
    assert format_wall_time(instant, "") == ""
