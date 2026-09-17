"""For contributors: fixed reference transfer, direct IR and JSON v4.

Run: ``uv run python -m examples.developer.transfer_sample_ir``
Expected output:
    transfer_sample_ir.json
    Transfer: well:source -> well:destination; 0.25 mL
    Reference intent only; native transfer remains gated.

The complete direct-IR companion is transfer_sample_ir.json. The author flow
has the same ordered configuration, transfer and log effects. BenchLiquidHandler
is a reference contributor, not an AutoSuite tool/channel/calibration profile.
"""

from pathlib import Path
from typing import ClassVar

from examples.transfer_sample import TransferSample
from sciloom import LiquidHandler, mL
from sciloom.core.bindings import DeviceBindings, TransferDeviceBinding
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, TransferEvent
from sciloom.core.ir import (
    CommandArgument,
    ConfigureProperty,
    DeviceCommand,
    DeviceResource,
    FunctionIR,
    Literal,
    LogValue,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.ir.device_contracts import (
    AIR_GAP_ID,
    ASPIRATE_FLOW_ID,
    BASE_DEVICE_CONTRACT,
    DISPENSE_FLOW_ID,
    LIQUID_HANDLER_CONTRACT,
    TRANSFER_ID,
)
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom.devices.declarations import bind_device


class BenchLiquidHandler(LiquidHandler):
    """Explicit reference tool, with no guessed vendor connections."""

    device_type_id: ClassVar[str] = "example.bench-liquid-handler/v1"
    writable_properties = ("aspirate_flow", "dispense_flow", "air_gap")
    required_configuration = ("aspirate_flow", "dispense_flow", "air_gap")
    supported_operations = (LiquidHandler.transfer,)


SOURCE = Zone(well_ids=("well:source",))
DESTINATION = Zone(well_ids=("well:destination",))
LOCATIONS = LocationDirectory(
    wells=(Well(identity="well:source", name="Source"), Well(identity="well:destination", name="Destination"))
)


class TransferRecordingTarget:
    """Record JSON with fixed, typed reference facts, never hardware XML."""

    target_id = "example.transfer-recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Bind one logical tool to known source/destination wells and capacity."""
        return DeviceBindings(
            devices=(
                TransferDeviceBinding(
                    binding=bind_device(
                        logical_id="liquid", device=BenchLiquidHandler(), physical_id="reference:liquid-1"
                    ),
                    source_wells=SOURCE,
                    destination_wells=DESTINATION,
                    usable_capacity=1 * mL,
                ),
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """Reference recording adds no native encoding claims."""
        return ()

    def emit(self, program: Program) -> Artifact:
        """Emit the shared typed semantic contract."""
        return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")


def build_program() -> Program:
    """Express TransferSample directly, retaining locations as typed inputs."""
    return Program(
        entry_function_id="transfer",
        device_types=(BASE_DEVICE_CONTRACT, LIQUID_HANDLER_CONTRACT),
        resources=(
            DeviceResource(node_id="liquid", logical_id="liquid", device_type_id=LIQUID_HANDLER_CONTRACT.type_id),
        ),
        functions=(
            FunctionIR(
                node_id="transfer",
                name="TransferSample",
                variables=(
                    Variable(
                        node_id="source", owner_id="transfer", name="source", type=ZoneType(), role=VariableRole.INPUT
                    ),
                    Variable(
                        node_id="destination",
                        owner_id="transfer",
                        name="destination",
                        type=ZoneType(),
                        role=VariableRole.INPUT,
                    ),
                ),
                body=(
                    ConfigureProperty(
                        node_id="set-aspirate",
                        resource_id="liquid",
                        property_id=ASPIRATE_FLOW_ID,
                        value=Literal(node_id="aspirate", type=ScalarType.FLOW_RATE, value=1e-6 / 60),
                    ),
                    ConfigureProperty(
                        node_id="set-dispense",
                        resource_id="liquid",
                        property_id=DISPENSE_FLOW_ID,
                        value=Literal(node_id="dispense", type=ScalarType.FLOW_RATE, value=2e-6 / 60),
                    ),
                    ConfigureProperty(
                        node_id="set-gap",
                        resource_id="liquid",
                        property_id=AIR_GAP_ID,
                        value=Literal(node_id="gap", type=ScalarType.VOLUME, value=0.05e-6),
                    ),
                    DeviceCommand(
                        node_id="move",
                        resource_id="liquid",
                        operation_id=TRANSFER_ID,
                        arguments=(
                            CommandArgument(name="source", value=Reference(node_id="source-ref", symbol_id="source")),
                            CommandArgument(
                                name="destination", value=Reference(node_id="destination-ref", symbol_id="destination")
                            ),
                            CommandArgument(
                                name="volume", value=Literal(node_id="volume", type=ScalarType.VOLUME, value=0.25e-6)
                            ),
                        ),
                    ),
                    LogValue(
                        node_id="log",
                        value=Literal(node_id="message", type=ScalarType.TEXT, value="transfer complete"),
                        category=Literal(node_id="category", type=ScalarType.TEXT, value="liquid"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="experiment"),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    target = TransferRecordingTarget()
    compiled = TransferSample().compile(target=target)
    program = build_program()
    output = Path(__file__).with_suffix(".json")
    output.write_text(to_json(program), encoding="utf-8")
    restored = from_json(output.read_text(encoding="utf-8"))
    assert restored == program
    snapshots = []
    for candidate in (compiled.semantic_ir, compiled.specialized_ir, restored):
        result = Interpreter(
            candidate,
            environment=ReferenceEnvironment(
                locations=LOCATIONS,
                device_bindings=target.resolve_devices(candidate),
            ),
        ).run(inputs={"source": SOURCE, "destination": DESTINATION})
        transfer = next(event for event in result.events if isinstance(event, TransferEvent))
        snapshots.append((transfer.source, transfer.destination, transfer.volume, transfer.configuration))
        assert not next(iter(result.resources.values())).enabled
    assert snapshots[0] == snapshots[1] == snapshots[2]
    print(output.name)
    print(f"Transfer: {SOURCE.well_ids[0]} -> {DESTINATION.well_ids[0]}; {transfer.volume / mL:g} mL")
    print("Reference intent only; native transfer remains gated.")
