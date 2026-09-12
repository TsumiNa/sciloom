"""Logical agitation contract, independent of Python source conversion."""

from typing import Callable, ClassVar

from ..units import RotationalSpeed
from .base import BaseDevice
from .declarations import operation


class Agitator(BaseDevice):
    """Declare a logical device using an annotated Function field."""

    device_type_id: ClassVar[str] = "sciloom.agitator/v1"

    @property
    def speed(self) -> RotationalSpeed:
        """Rotational speed to apply on the next start; reading is not supported."""
        raise TypeError("Device property reads are not supported yet.")

    @speed.setter
    @operation(id="sciloom.agitator.speed/v1")
    def speed(self, value: RotationalSpeed) -> None:
        """Capture the configuration without changing running equipment."""

    @operation(id="sciloom.agitator.start/v1")
    def start(self) -> None:
        """Apply the complete saved configuration and enable or reapply agitation."""

    @operation(id="sciloom.agitator.stop/v1")
    def stop(self) -> None:
        """Stop while retaining saved and last-applied configurations."""

    writable_properties: ClassVar[tuple[str, ...]] = ("speed",)
    required_configuration: ClassVar[tuple[str, ...]] = ("speed",)
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (start, stop)
