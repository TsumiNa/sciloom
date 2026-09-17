"""Fixed logical thermal control using explicit generic lifecycle effects."""

from typing import Callable, ClassVar

from sciloom.core.ir import LifecycleEffect
from sciloom.units import Temperature, TemperatureRate
from .base import BaseDevice
from .declarations import operation


class Heater(BaseDevice):
    """Declare fixed thermal control as an annotated Function dependency.

    Configure both properties before starting. Values are saved at assignment;
    start applies the complete saved configuration. No measurement, arrival
    condition, dynamic controller selection or native profile is implied.
    Authors add instrument capabilities by subclassing this family.
    """

    device_type_id: ClassVar[str] = "sciloom.heater/v1"

    @property
    def temperature(self) -> Temperature:
        """Write-only absolute target; this is not a temperature measurement."""
        raise TypeError("Device property reads are not supported yet.")

    @temperature.setter
    @operation(id="sciloom.heater.temperature/v1")
    def temperature(self, value: Temperature) -> None:
        """Capture a target without changing the applied configuration."""

    @property
    def ramp_rate(self) -> TemperatureRate:
        """Write-only temperature change rate; device limits belong to profiles."""
        raise TypeError("Device property reads are not supported yet.")

    @ramp_rate.setter
    @operation(id="sciloom.heater.ramp-rate/v1")
    def ramp_rate(self, value: TemperatureRate) -> None:
        """Capture the rate for the next explicit start or reapply."""

    @operation(id="sciloom.heater.start/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE)
    def start(self) -> None:
        """Apply both saved settings and enable, or reapply while enabled."""

    @operation(id="sciloom.heater.stop/v1", lifecycle=LifecycleEffect.DISABLE)
    def stop(self) -> None:
        """Disable while retaining saved and last-applied settings."""

    writable_properties: ClassVar[tuple[str, ...]] = ("temperature", "ramp_rate")
    required_configuration: ClassVar[tuple[str, ...]] = ("temperature", "ramp_rate")
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (start, stop)
