"""Zone identity, ordering and fixed directory ownership are independent of hardware."""

from dataclasses import FrozenInstanceError

import pytest

from .locations import LocationDirectory, Well, Zone


def test_order_identity_empty_and_directory_isolation():
    zone = Zone(well_ids=("rack:27", "rack:0"))
    mapping = {"rack": zone, "single": Zone(well_ids=("rack:27",))}
    directory = LocationDirectory(
        wells=(Well(identity="rack:0", name="Rack: Well #0"), Well(identity="rack:27", name="Rack: Well #27")),
        zones=mapping,
    )
    mapping.clear()
    assert directory.find("rack").well_ids == ("rack:27", "rack:0")
    assert directory.well_name(directory.find("single")) == "Rack: Well #27"
    assert directory.find("missing") == Zone.empty() and len(Zone.empty()) == 0
    with pytest.raises(TypeError):
        directory.zones["rack"] = Zone.empty()
    with pytest.raises(FrozenInstanceError):
        zone.well_ids = ()
    for value in (zone, Zone.empty()):
        with pytest.raises(TypeError, match="truthiness"):
            bool(value)


@pytest.mark.parametrize("value", [[], "abc", (1,), (True,), ("",), ("  ",), ("a", "a")])
def test_invalid_zone_identity_structure(value):
    with pytest.raises((ValueError, TypeError)):
        Zone(well_ids=value)


def test_directory_rejects_ambiguous_or_unknown_identity_and_wrong_queries():
    well = Well(identity="a", name="A")
    for kwargs in (
        {"wells": (well, well)},
        {"wells": (well,), "zones": {"x": Zone(well_ids=("unknown",))}},
        {"wells": (well,), "zones": {"": Zone.empty()}},
        {"wells": (well,), "zones": {"x": ("a",)}},
        {"wells": [well]},
    ):
        with pytest.raises((ValueError, TypeError)):
            LocationDirectory(**kwargs)
    directory = LocationDirectory(wells=(well,))
    for zone in (Zone.empty(), Zone(well_ids=("a", "b"))):
        with pytest.raises(ValueError, match="exactly one"):
            directory.well_name(zone)
    with pytest.raises(KeyError):
        directory.well_name(Zone(well_ids=("unknown",)))
    with pytest.raises(TypeError):
        directory.well_name("a")
    with pytest.raises(TypeError):
        directory.find(1)


def test_zone_host_index_and_iteration_use_positions_not_identity_numbers():
    zone = Zone(well_ids=("rack:27", "rack:0"))
    assert zone[0] == Zone(well_ids=("rack:27",))
    assert tuple(zone) == (zone[0], zone[1])
    assert tuple(Zone.empty()) == ()
    for index in (-1, 2, 27):
        with pytest.raises(IndexError):
            zone[index]
    for index in (True, 1.0, "0", slice(None)):
        with pytest.raises(TypeError):
            zone[index]
