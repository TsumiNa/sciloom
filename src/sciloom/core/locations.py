"""Immutable well identities and a fixed, equipment-independent location directory."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, kw_only=True)
class Zone:
    """An ordered selection of unique wells, identified by opaque strings.

    Args:
        well_ids: Immutable identities in selection order; empty is valid.

    Raises:
        TypeError: The selection is not a tuple of strings.
        ValueError: An identity is empty or occurs more than once.

    Identities are not list positions, device names or measurements. Construct
    values from a trusted directory rather than guessing their spelling.
    """

    well_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.well_ids) is not tuple or any(type(item) is not str for item in self.well_ids):
            raise TypeError("Zone well_ids must be an immutable tuple of strings.")
        if any(not item.strip() for item in self.well_ids):
            raise ValueError("Well identities must be nonempty.")
        if len(set(self.well_ids)) != len(self.well_ids):
            raise ValueError("Zone well identities must be unique.")

    @classmethod
    def empty(cls) -> "Zone":
        """Return an empty selection, suitable for an explicit Var default."""
        return cls()

    def __len__(self) -> int:
        """Return the selected well count without consulting equipment."""
        return len(self.well_ids)

    def __getitem__(self, index: int) -> "Zone":
        """Select one well by nonnegative position; reject bool and slicing.

        Raises:
            TypeError: The index is not an integer (excluding bool).
            IndexError: The index is negative or outside this selection.
        """
        if type(index) is not int:
            raise TypeError("Zone indices must be integers, excluding bool.")
        if index < 0 or index >= len(self):
            raise IndexError("Zone index is outside the selection.")
        return Zone(well_ids=(self.well_ids[index],))

    def __iter__(self) -> Iterator["Zone"]:
        """Yield independent one-well selections in their stored order."""
        return (Zone(well_ids=(identity,)) for identity in self.well_ids)

    def __bool__(self) -> bool:
        """Reject implicit truthiness; compare len(zone) explicitly."""
        raise TypeError("Zone has no implicit truthiness; compare len(zone) explicitly.")


@dataclass(frozen=True, kw_only=True)
class Well:
    """A directory entry with an opaque identity and a human-readable label.

    Args:
        identity: Stable nonempty identity shared by overlapping Zones.
        name: Display label, independent of position in a particular Zone.

    Raises:
        TypeError: An attribute is not text.
        ValueError: An attribute is empty.
    """

    identity: str
    name: str

    def __post_init__(self) -> None:
        if type(self.identity) is not str or type(self.name) is not str:
            raise TypeError("Well identity and name must be text.")
        if not self.identity.strip() or not self.name.strip():
            raise ValueError("Well identity and name must be nonempty.")


@dataclass(frozen=True, kw_only=True)
class LocationDirectory:
    """Fixed named Zones and well labels, copied independently of caller mappings.

    Args:
        wells: Immutable entries; identities must be unique.
        zones: Named selections containing only wells in this directory.

    Raises:
        TypeError: Entries or selections have incorrect types.
        ValueError: Names/identities are empty, duplicated or unresolved.

    Queries perform no I/O. The same directory can be shared between reference
    sessions without sharing mutable location state.
    """

    wells: tuple[Well, ...] = ()
    zones: Mapping[str, Zone] = field(default_factory=dict)
    _names: Mapping[str, str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.wells) is not tuple or any(type(well) is not Well for well in self.wells):
            raise TypeError("Directory wells must be an immutable tuple of Well entries.")
        if not isinstance(self.zones, Mapping):
            raise TypeError("Directory zones must be a name-to-Zone mapping.")
        names = {well.identity: well.name for well in self.wells}
        if len(names) != len(self.wells):
            raise ValueError("Directory well identities must be unique.")
        zones = dict(self.zones)
        for name, zone in zones.items():
            if type(name) is not str or type(zone) is not Zone:
                raise TypeError("Zone names must be text and selections must be Zone values.")
            if not name.strip():
                raise ValueError("Zone names must be nonempty.")
            unknown = set(zone.well_ids) - names.keys()
            if unknown:
                raise ValueError(f"Zone {name!r} refers to unknown wells: {sorted(unknown)!r}.")
        object.__setattr__(self, "zones", MappingProxyType(zones))
        object.__setattr__(self, "_names", MappingProxyType(names))

    def find(self, name: str) -> Zone:
        """Return the named selection, or an empty Zone when it is absent.

        Raises:
            TypeError: The query is not text.
        """
        if type(name) is not str:
            raise TypeError("Zone lookup requires a text name.")
        return self.zones.get(name, Zone.empty())

    def well_name(self, value: Zone) -> str:
        """Return the display label of exactly one known well.

        Raises:
            TypeError: The query is not a Zone.
            ValueError: The query contains zero or multiple wells.
            KeyError: The well identity is absent from this directory.
        """
        if type(value) is not Zone:
            raise TypeError("well_name requires a Zone.")
        if len(value) != 1:
            raise ValueError("well_name requires exactly one well.")
        return self._names[value.well_ids[0]]
