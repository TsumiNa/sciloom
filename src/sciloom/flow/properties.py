"""Host declarations for stored well metadata, separate from device properties."""

from dataclasses import dataclass
from enum import Enum

from sciloom.core.locations import Zone


class _Omitted(Enum):
    DEFAULT = "omitted"


@dataclass(frozen=True)
class WellProperty:
    """Declare a named text attribute stored on wells.

    Args:
        name: Nonempty, fixed user-property name on the target platform.
        value_type: The Python str type; other property types are not supported.

    Raises:
        TypeError: The name is not text or value_type is not str.
        ValueError: The name is empty.

    Create this declaration during host composition, usually in __init__. Inside
    a runtime method, assign with ``self.label[zone] = value`` or read one well
    with ``self.label.get(zone, default="")``. These operations store metadata;
    they neither measure a sample nor read a device configuration.
    """

    name: str
    value_type: type[str]

    def __post_init__(self) -> None:
        if type(self.name) is not str or self.value_type is not str:
            raise TypeError("WellProperty requires a text name and the str value type.")
        if not self.name:
            raise ValueError("WellProperty names must not be empty.")

    def __setitem__(self, zone: Zone, value: str) -> None:
        """Write the captured text to every selected well; an empty Zone is a no-op.

        Args:
            zone: Runtime selection of known wells.
            value: Text captured before evaluating the selection.

        Raises:
            TypeError: Called by host Python rather than compiled runtime code.
        """
        raise TypeError("Well-property writes belong in compiled @runtime methods.")

    def get(self, zone: Zone, *, default: str | _Omitted = _Omitted.DEFAULT) -> str:
        """Read one well's text into a declared runtime field.

        Args:
            zone: Exactly one known well.
            default: Optional text for a missing or incompatible property. It is
                captured eagerly and does not recover selection or service errors.

        Returns:
            Stored text or the explicitly supplied fallback.

        Raises:
            TypeError: Called from host Python.
            sciloom.core.diagnostics.ExecutionError: The selection is invalid or
                a strict read finds no compatible text property.
        """
        raise TypeError("Well-property reads belong in compiled @runtime methods.")
