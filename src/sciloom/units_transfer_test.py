"""Flow and length preserve signed physical dimensions and finite values."""

from dataclasses import FrozenInstanceError

import pytest

from .units import FlowRate, Length, m3_per_s, metre, mL_per_min, mm


@pytest.mark.parametrize(
    "unit,canonical,kind,field,scale",
    [
        (mL_per_min, m3_per_s, FlowRate, "m3_per_second", 1e-6 / 60),
        (mm, metre, Length, "metres", 0.001),
    ],
)
def test_signed_quantity_conversion_and_arithmetic(unit, canonical, kind, field, scale):
    value = -6 * unit
    assert getattr(value, field) == pytest.approx(-6 * scale)
    assert (value + 2 * unit) / unit == pytest.approx(-4)
    assert (value - 2 * unit) / unit == pytest.approx(-8)
    assert value * 2 == 2 * value == -12 * unit
    assert value / 2 == -3 * unit
    assert value / (2 * unit) == pytest.approx(-3)
    assert abs(value) == -value == 6 * unit and +value == value
    assert value < 0 * unit and value <= 0 * unit
    assert 0 * unit > value and 0 * unit >= value
    assert hash(value) == hash(-6 * unit)
    assert 1 * canonical == kind(**{field: 1})
    with pytest.raises(FrozenInstanceError):
        setattr(value, field, 1)


@pytest.mark.parametrize("kind,field", [(FlowRate, "m3_per_second"), (Length, "metres")])
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_canonical_values(kind, field, value):
    with pytest.raises((TypeError, ValueError)):
        kind(**{field: value})


@pytest.mark.parametrize("unit", [mL_per_min, m3_per_s, mm, metre])
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_unit_values(unit, value):
    with pytest.raises((TypeError, ValueError)):
        value * unit


def test_dimensions_do_not_mix_and_arithmetic_cannot_overflow():
    flow, length = 1 * mL_per_min, 1 * mm
    for operation in (
        lambda: flow + length,
        lambda: flow == length,
        lambda: flow < length,
        lambda: flow / length,
        lambda: flow * length,
        lambda: length + 1,
        lambda: flow * True,
        lambda: length / True,
    ):
        with pytest.raises(TypeError):
            operation()
    for unit in (m3_per_s, metre):
        with pytest.raises(ValueError, match="finite"):
            (1e308 * unit) * 2
        with pytest.raises(ZeroDivisionError):
            (1 * unit) / 0
