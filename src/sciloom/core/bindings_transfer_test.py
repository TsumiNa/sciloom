"""Trusted transfer facts remain fixed, typed, immutable and conflict checked."""

from dataclasses import FrozenInstanceError, replace

import pytest

from sciloom import Agitator, LiquidHandler, Zone, mL
from sciloom.devices.declarations import bind_device
from .bindings import DeviceBindings, DeviceCandidate, DeviceSelectionBinding, TransferDeviceBinding


def transfer_binding(**changes):
    options = dict(
        binding=bind_device(logical_id="liquid", device=LiquidHandler(), physical_id="tool:1"),
        source_wells=Zone(well_ids=("source",)),
        destination_wells=Zone(well_ids=("destination",)),
        usable_capacity=1 * mL,
    )
    options.update(changes)
    return TransferDeviceBinding(**options)


def test_facts_preserve_identity_contracts_and_immutability():
    facts = transfer_binding()
    assert facts.logical_id == "liquid" and facts.physical_id == "tool:1"
    assert facts.contract is facts.binding.contract
    assert facts.base_contracts == facts.binding.base_contracts
    assert facts.supported_operations == facts.binding.supported_operations
    assert facts.writable_properties == facts.binding.writable_properties
    assert DeviceBindings(devices=(facts,)).devices == (facts,)
    with pytest.raises(FrozenInstanceError):
        facts.usable_capacity = 2 * mL


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_wells", Zone.empty()),
        ("destination_wells", Zone.empty()),
        ("source_wells", "source"),
        ("destination_wells", ["destination"]),
        ("usable_capacity", 0 * mL),
        ("usable_capacity", -1 * mL),
        ("usable_capacity", 1.0),
        ("binding", object()),
    ],
)
def test_invalid_facts_cannot_be_constructed(field, value):
    with pytest.raises((TypeError, ValueError)):
        transfer_binding(**{field: value})


def test_unrelated_or_unsupported_profile_does_not_gain_transfer_authority():
    shaker = bind_device(logical_id="liquid", device=Agitator(), physical_id="tool:1")
    with pytest.raises(ValueError, match="LiquidHandler"):
        transfer_binding(binding=shaker)
    liquid = transfer_binding().binding
    with pytest.raises(ValueError, match="transfer"):
        transfer_binding(binding=replace(liquid, supported_operations=()))
    weakened = replace(
        liquid.contract,
        type_id="example.weak-liquid/v1",
        base_type_ids=(liquid.contract.type_id, *liquid.contract.base_type_ids),
        required_configuration=(),
    )
    weak_binding = replace(
        liquid, contract=weakened, base_contracts=(*liquid.base_contracts, liquid.contract), writable_properties=()
    )
    with pytest.raises(ValueError, match="configuration"):
        transfer_binding(binding=weak_binding)


def test_same_actuator_conflicts_across_fixed_selection_and_transfer_bindings():
    facts = transfer_binding()
    shaker = bind_device(logical_id="shaker", device=Agitator(), physical_id="tool:1")
    for other in (
        shaker,
        DeviceSelectionBinding(
            logical_id="shaker",
            candidates=(
                DeviceCandidate(
                    binding=shaker,
                    wells=Zone(well_ids=("source",)),
                ),
            ),
        ),
    ):
        with pytest.raises(ValueError, match="physical_id"):
            DeviceBindings(devices=(facts, other))
    with pytest.raises(ValueError, match="logical_id"):
        DeviceBindings(devices=(facts, replace(facts, binding=replace(facts.binding, physical_id="tool:2"))))
    # Shared wells do not imply a collision between distinct physical actuators.
    other = replace(shaker, physical_id="shaker:1")
    assert len(DeviceBindings(devices=(facts, other)).devices) == 2
