"""Reject ambiguous deployment configuration before XML construction."""

import pytest

from . import AutoSuiteTarget, IndividualShakerBinding


@pytest.mark.parametrize(
    "changes",
    [
        {"logical_id": ""},
        {"zone": " "},
        {"zone": "bad\nname"},
        {"device_id": ""},
        {"device_id": "bad"},
        {"device_id": "0"},
        {"device_id": 23},
    ],
)
def test_invalid_individual_shaker_binding(changes):
    values = dict(logical_id="mixer", zone="Heater Shaker 23", device_id="23")
    values.update(changes)
    with pytest.raises(ValueError):
        IndividualShakerBinding(**values)


def test_binding_identity_and_physical_aliases_are_unambiguous():
    binding = IndividualShakerBinding(logical_id="mixer", zone="Heater Shaker 23", device_id="23")
    with pytest.raises(ValueError, match="logical"):
        AutoSuiteTarget(agitators=(binding, binding))
    other = IndividualShakerBinding(logical_id="other", zone="another zone", device_id="23")
    with pytest.raises(ValueError, match="device"):
        AutoSuiteTarget(agitators=(binding, other))
    with pytest.raises(TypeError, match="IndividualShakerBinding"):
        AutoSuiteTarget(agitators=("not a binding",))


def test_distinct_shakers_cannot_bind_the_same_zone():
    first = IndividualShakerBinding(logical_id="first", zone="Heater Shaker 23", device_id="23")
    second = IndividualShakerBinding(logical_id="second", zone="Heater Shaker 23", device_id="25")
    with pytest.raises(ValueError, match="same AutoSuite zone"):
        AutoSuiteTarget(agitators=(first, second))
