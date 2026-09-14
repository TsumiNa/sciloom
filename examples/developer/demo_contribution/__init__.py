"""Independent example contribution; imports only SciLoom's public contracts.

This directory can live outside the SciLoom source tree. DemoTarget records IR;
it neither drives hardware nor simulates the native calibrate command.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import ConfigureProperty, Literal, Program, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.devices import Agitator, operation
from sciloom.devices.declarations import bind_device


@dataclass(frozen=True, kw_only=True)
class DemoAgitator(Agitator):
    """Test deployment with a dimensionless gain in [0, 1]."""

    device_id: str = "demo-1"
    device_type_id: ClassVar[str] = "example.demo-agitator/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ("speed", "gain")
    required_configuration: ClassVar[tuple[str, ...]] = ("speed", "gain")

    @property
    def gain(self) -> float:
        raise TypeError("Device property reads are not supported yet.")

    @gain.setter
    @operation(id="example.demo-agitator.gain/v1")
    def gain(self, value: float) -> None:
        """Save the gain to apply at the next start."""

    @operation(id="example.demo-agitator.calibrate/v1")
    def calibrate(self) -> None:
        """Record a native calibration request; no reference execution semantics."""

    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (
        Agitator.start,
        Agitator.stop,
        calibrate,
    )


class DemoTarget:
    """Recording compiler with an intentionally conservative gain proof.

    Only literal gains in [0, 1] are accepted. DSL host constants become literals;
    runtime inputs and arithmetic need a stronger proof and are rejected here.
    """

    target_id = "example.demo/v1"

    def __init__(self, *, devices: Mapping[str, DemoAgitator]) -> None:
        if any(type(device) is not DemoAgitator for device in devices.values()):
            raise TypeError("DemoTarget requires DemoAgitator deployment profiles.")
        if any(not device.device_id for device in devices.values()):
            raise ValueError("Demo device IDs must not be empty.")
        self.devices = MappingProxyType(dict(devices))

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(
            devices=tuple(
                bind_device(logical_id=name, device=device, physical_id=f"demo:{device.device_id}")
                for name, device in self.devices.items()
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        diagnostics = []
        for node, path in iter_nodes(program):
            if isinstance(node, ConfigureProperty) and node.property_id == "example.demo-agitator.gain/v1":
                value = node.value
                if not (isinstance(value, Literal) and type(value.value) in (int, float) and 0 <= value.value <= 1):
                    diagnostics.append(
                        Diagnostic(
                            code="demo_gain_range",
                            message="Demo gain must be provably within [0, 1]; this target proves literals only.",
                            path=path,
                            node_id=node.node_id,
                            source=node.source,
                        )
                    )
        return tuple(diagnostics)

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")
