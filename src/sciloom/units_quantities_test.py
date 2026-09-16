"""Finite quantity construction, dimensional arithmetic and unit conversion."""

import pytest

from .units import Duration, L, Volume, hour, minute, mL, rpm, rps, s, uL


def test_canonical_units_and_arithmetic():
    assert (1000 * uL).m3 == pytest.approx((1 * mL).m3)
    assert (1000 * mL).m3 == pytest.approx((1 * L).m3)
    assert 1 * hour == 60 * minute == Duration(seconds=3600)
    assert 1 * minute - 90 * s == -30 * s
    assert (2 * mL + 3 * mL).m3 == pytest.approx(5e-6)
    assert (-2 * mL / mL) == -2
    assert (2 * mL) / (1 * mL) == 2
    assert (2 * mL * 3).m3 == pytest.approx(6e-6)
    assert (3 * (2 * s)) == 6 * s
    assert (6 * s) / 2 == 3 * s
    assert -(-2 * s) == +(2 * s)
    assert 1 * mL < 2 * mL <= 3 * mL
    assert 1 * minute >= 30 * s > 0 * s


@pytest.mark.parametrize("quantity,field", [(Volume, "m3"), (Duration, "seconds")])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), 10**1000])
def test_quantities_require_finite_values(quantity, field, value):
    with pytest.raises(ValueError):
        quantity(**{field: value})


@pytest.mark.parametrize("unit", [mL, uL, L, s, minute, hour])
@pytest.mark.parametrize("value", [True, "1"])
def test_unit_construction_rejects_coercion(unit, value):
    with pytest.raises(TypeError):
        value * unit


def test_wrong_dimensions_and_numeric_arguments():
    with pytest.raises(TypeError):
        1 * mL + 1 * s
    with pytest.raises(TypeError):
        (1 * mL) / s
    with pytest.raises(TypeError):
        (1 * s) * True
    with pytest.raises(TypeError):
        1 * s < 1 * mL
    with pytest.raises(ZeroDivisionError):
        (1 * s) / (0 * s)
    with pytest.raises(ValueError):
        (1e308 * s) * 2


def test_speed_scaling_and_conversion_keep_nonnegative_values():
    assert (600 * rpm) * 2 == 1200 * rpm
    assert (600 * rpm) / 2 == 300 * rpm
    assert (600 * rpm) / rpm == 600
    assert (600 * rpm) / (5 * rps) == 2
    with pytest.raises(ValueError):
        (600 * rpm) * -1
    with pytest.raises(TypeError):
        (600 * rpm) * True
