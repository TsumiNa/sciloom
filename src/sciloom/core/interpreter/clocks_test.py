"""Explicit wall time is independent of host clocks and rejects naive values."""

from datetime import datetime, timedelta, timezone

import pytest

from .clocks import VirtualClock, VirtualWallClock, format_wall_time


@pytest.mark.parametrize("value", [True, None, "1", -1, float("nan"), float("inf"), 10**400])
def test_virtual_elapsed_clock_rejects_invalid_start_and_wait_before_mutation(value):
    with pytest.raises((TypeError, ValueError)):
        VirtualClock(start=value)
    clock = VirtualClock(start=2)
    with pytest.raises((TypeError, ValueError)):
        clock.wait(value)
    assert clock.monotonic() == 2


def test_virtual_wait_overflow_and_wall_clock_independence():
    elapsed = VirtualClock(start=1e308)
    with pytest.raises(ValueError):
        elapsed.wait(1e308)
    assert elapsed.monotonic() == 1e308
    wall = VirtualWallClock(datetime(2026, 9, 16, tzinfo=timezone.utc))
    before = wall.now()
    elapsed = VirtualClock()
    elapsed.wait(2)
    elapsed.wait(0)
    assert elapsed.monotonic() == 2
    assert wall.now() == before


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
