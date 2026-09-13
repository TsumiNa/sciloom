import pytest

from .units import RotationalSpeed, SpeedUnit, rpm, rps


def test_speed_units_have_one_canonical_value():
    assert 600 * rpm == 10 * rps == RotationalSpeed(rps=10)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), 10**1000])
def test_invalid_speeds(value):
    with pytest.raises(ValueError):
        value * rpm


@pytest.mark.parametrize("value", [True, "600"])
def test_speed_is_not_an_untyped_number(value):
    with pytest.raises(TypeError):
        RotationalSpeed(rps=value)


def test_unknown_units():
    with pytest.raises(ValueError):
        SpeedUnit("ml")
