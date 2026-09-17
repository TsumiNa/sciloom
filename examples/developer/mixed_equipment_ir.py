"""For contributors: one shared child, three fixed families and explicit services.

Run: ``uv run python -m examples.developer.mixed_equipment_ir``
Expected output:
    mixed_equipment_ir.json
    Barcode: S-001; transfers: 2; elapsed: 20.0 s
    Aspirate flows: 1, 3 mL/min; all actuators stopped: True
    Native AutoSuite generation and Executor acceptance remain gated/pending.

The complete companion is source-derived JSON v4 with relative source paths.
The recording target emits JSON only and is not an AutoSuite profile. Transfers
record intent, and virtual time does not simulate temperature or liquid motion.
"""

from pathlib import Path
from typing import ClassVar

from examples.mixed_equipment import MixedEquipment
from sciloom import Agitator, FlowRate, mL_per_min
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.interpreter import (
    DialogOutcome,
    DialogResponse,
    Interpreter,
    QueuedDialogResponses,
    ReferenceEnvironment,
    TransferEvent,
    VirtualClock,
    WellProperties,
)
from sciloom.core.ir import Program, from_json, to_json
from sciloom.devices.declarations import bind_device
from .source_paths import repository_relative
from .transfer_sample_ir import DESTINATION, LOCATIONS, SOURCE, TransferRecordingTarget
from .warm_sample_ir import BenchHeater


class ReferenceShaker(Agitator):
    """Reference actuator with explicit capabilities, independent of vendor IDs."""

    device_type_id: ClassVar[str] = "example.integration-shaker/v1"
    writable_properties = ("speed",)
    required_configuration = ("speed",)
    supported_operations = (Agitator.start, Agitator.stop)


class MixedRecordingTarget:
    """Bind three distinct physical actuators and archive semantic JSON."""

    target_id = "example.mixed-recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Share logical resources across child calls, with fixed transfer facts."""
        liquid = TransferRecordingTarget().resolve_devices(program).devices[0]
        return DeviceBindings(
            devices=(
                bind_device(logical_id="heater", device=BenchHeater(), physical_id="reference:heater-1"),
                bind_device(logical_id="shaker", device=ReferenceShaker(), physical_id="reference:shaker-1"),
                liquid,
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """Reference archive has no native serialization claim."""
        return ()

    def emit(self, program: Program) -> Artifact:
        """Emit JSON, without relabelling it as hardware XML."""
        return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")


def reference_environment(program: Program, *, responses: tuple[DialogResponse, ...]) -> ReferenceEnvironment:
    """Supply all external services explicitly, including caller-owned responses."""
    return ReferenceEnvironment(
        device_bindings=MixedRecordingTarget().resolve_devices(program),
        locations=LOCATIONS,
        clock=VirtualClock(),
        properties=WellProperties(),
        dialogs=QueuedDialogResponses(responses),
    )


if __name__ == "__main__":
    program = repository_relative(MixedEquipment().to_ir())
    compiled = compile_ir(program, target=MixedRecordingTarget())
    path = Path(__file__).with_suffix(".json")
    path.write_bytes(compiled.artifact.content)
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == compiled.specialized_ir
    environment = reference_environment(
        restored, responses=(DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"),)
    )
    result = Interpreter(restored, environment=environment).run(inputs={"source": SOURCE, "destination": DESTINATION})
    transfers = [event for event in result.events if isinstance(event, TransferEvent)]
    assert result.outputs == {"barcode": "S-001"}
    assert environment.properties is not None and environment.clock is not None
    assert environment.properties.snapshot() == {("well:destination", "sample_ID"): "S-001"}
    flows = []
    for event in transfers:
        flow = event.configuration["aspirate_flow"]
        assert isinstance(flow, FlowRate)
        flows.append(flow / mL_per_min)
    stopped = all(not state.enabled for state in result.physical_devices.values())
    assert flows == [1.0, 3.0] and stopped and environment.clock.monotonic() == 20
    print(path.name)
    print(
        f"Barcode: {result.outputs['barcode']}; transfers: {len(transfers)}; elapsed: {environment.clock.monotonic():.1f} s"
    )
    print(f"Aspirate flows: {flows[0]:g}, {flows[1]:g} mL/min; all actuators stopped: {stopped}")
    print("Native AutoSuite generation and Executor acceptance remain gated/pending.")
