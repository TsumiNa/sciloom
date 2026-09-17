"""Affine temperatures stay distinct from signed differences and rates."""

from dataclasses import FrozenInstanceError

import pytest

from .units import (
    Temperature,
    TemperatureDifference,
    TemperatureRate,
    degC,
    degC_per_min,
    delta_degC,
    delta_kelvin,
    kelvin,
    kelvin_per_s,
)


def test_standard_offset_and_affine_arithmetic():
    assert (0 * degC).kelvin == pytest.approx(273.15)
    assert (-20 * degC).kelvin == pytest.approx(253.15)
    assert 0 * kelvin == Temperature(kelvin=0)
    initial = 20 * degC
    target = initial + 5 * delta_degC
    assert target == Temperature(kelvin=298.15)
    assert target - initial == 5 * delta_kelvin
    assert target - 5 * delta_degC == initial
    assert 5 * delta_kelvin + initial == target
    assert initial < target and initial <= target and target > initial and target >= initial
    assert initial != target
    assert hash(initial) == hash(Temperature(kelvin=293.15))
    with pytest.raises(FrozenInstanceError):
        initial.kelvin = 100


@pytest.mark.parametrize("unit,other", [(delta_degC, delta_kelvin), (degC_per_min, kelvin_per_s)])
def test_signed_values_scaling_comparison_and_conversion(unit, other):
    value = -6 * unit
    assert (value + 2 * unit) / unit == pytest.approx(-4)
    assert (value - 2 * unit) / unit == pytest.approx(-8)
    assert value * 2 == 2 * value == -12 * unit
    assert value / 2 == -3 * unit
    assert value / (2 * unit) == pytest.approx(-3)
    assert value / unit == pytest.approx(-6)
    assert abs(value) == -value == 6 * unit
    assert +value == value
    assert value < 0 * unit and value <= 0 * unit
    assert 0 * unit > value and 0 * unit >= value
    assert hash(value) == hash(-6 * unit)
    assert (60 * degC_per_min).kelvin_per_second == pytest.approx(1)


@pytest.mark.parametrize(
    "kind,field",
    [
        (Temperature, "kelvin"),
        (TemperatureDifference, "kelvin"),
        (TemperatureRate, "kelvin_per_second"),
    ],
)
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_canonical_values(kind, field, value):
    with pytest.raises((TypeError, ValueError)):
        kind(**{field: value})


@pytest.mark.parametrize("unit", [degC, kelvin, delta_degC, delta_kelvin, degC_per_min, kelvin_per_s])
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_unit_values(unit, value):
    with pytest.raises((TypeError, ValueError)):
        value * unit


def test_invalid_absolute_arithmetic_and_dimensions():
    value = 20 * degC
    for operation in (
        lambda: value + value,
        lambda: value * 2,
        lambda: 2 * value,
        lambda: value / 2,
        lambda: value / kelvin,
        lambda: value / value,
        lambda: -value,
        lambda: abs(value),
        lambda: value + 1,
        lambda: value == 20,
        lambda: value < 1 * delta_degC,
        lambda: 1 * delta_degC - value,
        lambda: 1 * delta_degC + 1 * degC_per_min,
        lambda: 1 * delta_degC == 1 * degC_per_min,
    ):
        with pytest.raises(TypeError):
            operation()
    for operation in (lambda: -0.1 * kelvin, lambda: -274 * degC, lambda: 0 * kelvin - 1 * delta_degC):
        with pytest.raises(ValueError, match="nonnegative"):
            operation()
