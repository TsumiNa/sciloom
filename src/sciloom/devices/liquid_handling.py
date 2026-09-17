"""Explicit single-pair liquid transfer with typed configuration and locations."""

from typing import Callable, ClassVar

from sciloom.core.locations import Zone
from sciloom.units import FlowRate, Volume
from .base import BaseDevice
from .declarations import operation


class LiquidHandler(BaseDevice):
    """Declare a fixed liquid-handling dependency on a Function.

    Configure both flows and the air gap explicitly before transfer. Writes save
    values without moving liquid. A transfer captures two single-well locations
    and a positive volume, then checks trusted deployment limits before acting.
    There is no implicit tool, channel, rinse policy, capacity splitting or
    start/stop lifecycle. Authors extend this family by subclassing it.
    """

    device_type_id: ClassVar[str] = "sciloom.liquid-handler/v1"

    @property
    def aspirate_flow(self) -> FlowRate:
        """Write-only aspiration flow; transfer requires a positive value."""
        raise TypeError("Device property reads are not supported yet.")

    @aspirate_flow.setter
    @operation(id="sciloom.liquid-handler.aspirate-flow/v1")
    def aspirate_flow(self, value: FlowRate) -> None:
        """Save the flow for later explicit transfers."""

    @property
    def dispense_flow(self) -> FlowRate:
        """Write-only dispensing flow; transfer requires a positive value."""
        raise TypeError("Device property reads are not supported yet.")

    @dispense_flow.setter
    @operation(id="sciloom.liquid-handler.dispense-flow/v1")
    def dispense_flow(self, value: FlowRate) -> None:
        """Save the flow without producing a device action."""

    @property
    def air_gap(self) -> Volume:
        """Write-only nonnegative gap, included in the tool's usable capacity."""
        raise TypeError("Device property reads are not supported yet.")

    @air_gap.setter
    @operation(id="sciloom.liquid-handler.air-gap/v1")
    def air_gap(self, value: Volume) -> None:
        """Save the gap explicitly; no default or implicit rinse behavior."""

    @operation(id="sciloom.liquid-handler.transfer/v1")
    def transfer(self, source: Zone, destination: Zone, volume: Volume) -> None:
        """Transfer one positive volume between distinct single wells.

        Args:
            source: One known well allowed by the fixed deployment.
            destination: One different known well allowed by the deployment.
            volume: Positive volume; volume plus saved air gap must fit capacity.

        Reference execution records intent only and needs explicit locations and
        TransferDeviceBinding facts. Unsupported native profiles remain gated.
        """

    writable_properties: ClassVar[tuple[str, ...]] = ("aspirate_flow", "dispense_flow", "air_gap")
    required_configuration: ClassVar[tuple[str, ...]] = ("aspirate_flow", "dispense_flow", "air_gap")
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (transfer,)
