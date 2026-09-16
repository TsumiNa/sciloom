"""Explicit, per-well text metadata for reference execution."""

from collections.abc import Mapping
from types import MappingProxyType


class WellProperties:
    """Own mutable text metadata keyed by well identity and property name.

    Args:
        initial: Optional text mapping copied before use.

    Raises:
        TypeError: A key is not a pair of strings or a value is not text.
        ValueError: A well identity or property name is empty.

    This store does not infer a location directory. The interpreter checks well
    membership before reads/writes. Sharing the store is an explicit host choice.
    """

    def __init__(self, initial: Mapping[tuple[str, str], str] | None = None) -> None:
        self._values: dict[tuple[str, str], str] = {}
        for key, value in ({} if initial is None else initial).items():
            if type(key) is not tuple or len(key) != 2:
                raise TypeError("Well-property keys must be (well identity, property name) pairs.")
            self.set((key[0],), key[1], value)

    def get(self, well_id: str, name: str) -> str:
        """Return stored text; raise KeyError when this well has no named property.

        Custom adapters may raise TypeError for stored data of an incompatible
        type. Other adapter errors are not handled by runtime default values.
        """
        return self._values[(well_id, name)]

    def set(self, well_ids: tuple[str, ...], name: str, value: str) -> None:
        """Validate the whole selection, then store one text value for all wells.

        Args:
            well_ids: Opaque well identities; empty selections make no changes.
            name: Nonempty property name.
            value: Text copied by value into every selected entry.

        Raises:
            TypeError: Identities/name/value have invalid types.
            ValueError: An identity or name is empty.
        """
        if type(well_ids) is not tuple or any(type(well) is not str for well in well_ids):
            raise TypeError("Well identities must be a tuple of strings.")
        if type(name) is not str or type(value) is not str:
            raise TypeError("Well-property names and values must be text.")
        if not name or any(not well for well in well_ids):
            raise ValueError("Well identities and property names must not be empty.")
        self._values.update(((well, name), value) for well in well_ids)

    def snapshot(self) -> Mapping[tuple[str, str], str]:
        """Return a detached, read-only copy unaffected by later writes."""
        return MappingProxyType(dict(self._values))
