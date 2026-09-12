"""Logical agitation contract, independent of Python source conversion."""

from dataclasses import dataclass

from ..units import RotationalSpeed


@dataclass(frozen=True)
class Agitator:
    """A named logical component, bound to hardware only by the selected target."""

    resource_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise ValueError("Agitator requires a nonempty logical resource ID.")

    def set_speed(self, speed: RotationalSpeed) -> None:
        """Declare a runtime command; host invocation is prohibited."""
        raise TypeError("Agitator operations belong in compiled @runtime methods.")

    def stop(self) -> None:
        """Declare a runtime command; following DSL statements remain reachable."""
        raise TypeError("Agitator operations belong in compiled @runtime methods.")
