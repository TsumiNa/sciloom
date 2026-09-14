"""Test-only deployment profile and target shared by the colocated SciLoom tests.

StubShaker needs only a speed, like a vendor shaker; RecordingTarget binds it and
records the selected program as JSON without platform rules. Together they let
the core, flow, dsl and devices tests compile device programs without any
equipment package installed.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from .core.bindings import DeviceBindings
from .core.compiler import Artifact
from .core.diagnostics import Diagnostic
from .core.ir import Program, to_json
from .devices import Agitator
from .devices.declarations import bind_device


@dataclass(frozen=True, kw_only=True)
class StubShaker(Agitator):
    """Deployment profile that requires only a speed; a stand-in for a vendor shaker."""

    device_type_id: ClassVar[str] = "sciloom.test.stub-shaker/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ("speed",)
    required_configuration: ClassVar[tuple[str, ...]] = ("speed",)
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (Agitator.start, Agitator.stop)
    device_id: str = "stub-1"


class RecordingTarget:
    """Bind stub shakers and record the selected program as JSON; no platform rules."""

    target_id = "sciloom.test.recording/v1"

    def __init__(self, *, devices: Mapping[str, StubShaker]) -> None:
        self.devices = MappingProxyType(dict(devices))

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(
            devices=tuple(
                bind_device(logical_id=name, device=device, physical_id=f"stub:{device.device_id}")
                for name, device in self.devices.items()
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")
