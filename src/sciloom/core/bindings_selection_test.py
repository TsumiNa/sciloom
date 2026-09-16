"""Runtime candidates share contracts while retaining distinct physical identities."""

from dataclasses import replace

import pytest

from sciloom.core.locations import Zone
from .bindings import DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from .bindings_test import binding


def selection():
    return DeviceSelectionBinding(
        logical_id="mixer",
        candidates=(
            DeviceCandidate(binding=binding(), wells=Zone(well_ids=("a",))),
            DeviceCandidate(binding=replace(binding(), physical_id="test:2"), wells=Zone(well_ids=("b",))),
        ),
    )


def test_selection_exposes_common_contract_without_inventing_one_physical_id():
    selected = selection()
    assert selected.contract == binding().contract
    assert selected.base_contracts == binding().base_contracts
    assert selected.writable_properties == binding().writable_properties
    assert selected.supported_operations == binding().supported_operations
    assert not hasattr(selected, "physical_id")
    assert DeviceBindings(devices=(selected,)).devices == (selected,)


@pytest.mark.parametrize(
    "change",
    [
        {"candidates": ()},
        {"logical_id": "wrong"},
        {"candidates": ("invalid",)},
    ],
)
def test_invalid_candidate_collection(change):
    with pytest.raises((TypeError, ValueError)):
        replace(selection(), **change)


def test_overlap_and_differing_capabilities_are_rejected():
    first, second = selection().candidates
    for altered in (
        replace(second, wells=first.wells),
        replace(second, binding=replace(second.binding, physical_id=first.binding.physical_id)),
        replace(second, binding=replace(second.binding, supported_operations=())),
    ):
        with pytest.raises(ValueError):
            DeviceSelectionBinding(logical_id="mixer", candidates=(first, altered))
    with pytest.raises(ValueError):
        DeviceCandidate(binding=binding(), wells=Zone.empty())
    with pytest.raises(ValueError, match="physical_id"):
        DeviceBindings(devices=(selection(), replace(binding(), logical_id="other")))
    other = DeviceSelectionBinding(
        logical_id="other",
        candidates=(
            DeviceCandidate(
                binding=replace(binding(), logical_id="other", physical_id="test:3"),
                wells=first.wells,
            ),
        ),
    )
    with pytest.raises(ValueError, match="wells"):
        DeviceBindings(devices=(selection(), other))
