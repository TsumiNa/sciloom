"""Logical agitation contract, independent of Python source conversion."""

from typing import ClassVar

from ..units import RotationalSpeed
from .base import BaseDevice


class Agitator(BaseDevice):
    """Declare a logical device using an annotated Function field."""

    device_type_id: ClassVar[str] = "sciloom.agitator/v1"

    def set_speed(self, speed: RotationalSpeed) -> None:
        """Declare a runtime command; host invocation is prohibited."""
        raise TypeError("Agitator operations belong in compiled @runtime methods.")

    def stop(self) -> None:
        """Declare a runtime command; following DSL statements remain reachable."""
        raise TypeError("Agitator operations belong in compiled @runtime methods.")
