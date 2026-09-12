"""Reject ambiguous deployment configuration before XML construction."""

import pytest

from . import AutoSuiteTarget, AutoSuiteIndividualShaker


@pytest.mark.parametrize(
    "changes",
    [
        {"zone": " "},
        {"zone": "bad\nname"},
        {"device_id": ""},
        {"device_id": "bad"},
        {"device_id": "0"},
        {"device_id": 23},
    ],
)
def test_invalid_individual_shaker_binding(changes):
    values = dict(zone="Heater Shaker 23", device_id="23")
    values.update(changes)
    with pytest.raises(ValueError):
        AutoSuiteIndividualShaker(**values)


def test_binding_identity_and_physical_aliases_are_unambiguous():
    binding = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")
    with pytest.raises(ValueError, match="logical"):
        AutoSuiteTarget(devices={"": binding})
    other = AutoSuiteIndividualShaker(zone="another zone", device_id="23")
    with pytest.raises(ValueError, match="device"):
        AutoSuiteTarget(devices={"mixer": binding, "other": other})
    with pytest.raises(TypeError, match="AutoSuiteIndividualShaker"):
        AutoSuiteTarget(devices={"mixer": "not a binding"})


def test_distinct_shakers_cannot_bind_the_same_zone():
    first = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")
    second = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="25")
    with pytest.raises(ValueError, match="same AutoSuite zone"):
        AutoSuiteTarget(devices={"first": first, "second": second})


def test_deployment_records_and_mapping_are_frozen():
    from dataclasses import FrozenInstanceError

    binding = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")
    supplied = {"agitator": binding}
    target = AutoSuiteTarget(devices=supplied)
    supplied.clear()
    assert target.devices == {"agitator": binding}
    with pytest.raises(TypeError):
        target.devices["other"] = binding
    with pytest.raises(FrozenInstanceError):
        binding.zone = "elsewhere"


def test_shared_pipeline_resolves_devices_once(monkeypatch):
    from .codegen_agitation_test import ConfigureAgitation, target

    original = AutoSuiteTarget.resolve_devices
    calls = []

    def resolve(self, program):
        calls.append(program)
        return original(self, program)

    monkeypatch.setattr(AutoSuiteTarget, "resolve_devices", resolve)
    ConfigureAgitation().compile(target=target())
    assert len(calls) == 1
