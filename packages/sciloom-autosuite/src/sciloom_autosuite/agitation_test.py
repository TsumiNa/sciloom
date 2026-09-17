"""Reject ambiguous deployment configuration before XML construction."""

import pytest

from sciloom.core.ir import Program
from . import AutoSuiteIndividualShaker, AutoSuiteTarget


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


def test_zone_name_is_not_a_physical_actuator_identity():
    first = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")
    second = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="25")
    target = AutoSuiteTarget(devices={"first": first, "second": second})
    bindings = target.resolve_devices(Program(entry_function_id="unused"))
    assert {binding.physical_id for binding in bindings.devices} == {
        "autosuite:individual-shaker:23",
        "autosuite:individual-shaker:25",
    }
    # Offline declarations are not evidence that both profiles fit a real APP;
    # supplying a layout still checks each controller's actual well ancestry.


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
