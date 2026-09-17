"""For contributors: fixed heater binding, direct IR and explicit reference time.

Run: ``uv run python -m examples.developer.warm_sample_ir``
Expected output:
    warm_sample_ir.json
    Elapsed: 10.0 s; enabled: False; saved target: 293.15 K

The complete JSON companion comes from direct IR. The author WarmSample produces
the same ordered effects. BenchHeater is an explicit reference contributor, not
an AutoSuite profile or a simulation of temperature/heat transfer.
"""

from pathlib import Path
from typing import ClassVar

from examples.warm_sample import WarmSample
from sciloom import Heater, Temperature
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualClock
from sciloom.core.ir import (
    ConfigureProperty,
    DeviceCommand,
    DeviceResource,
    FunctionIR,
    Literal,
    Program,
    ScalarType,
    Wait,
    from_json,
    to_json,
)
from sciloom.core.ir.device_contracts import (
    BASE_DEVICE_CONTRACT,
    HEATER_CONTRACT,
    HEATER_RAMP_RATE_ID,
    HEATER_TEMPERATURE_ID,
    START_HEATER_ID,
    STOP_HEATER_ID,
)
from sciloom.devices.declarations import bind_device


class BenchHeater(Heater):
    """Explicit fixed reference profile, carrying no instrument identity guesses."""

    device_type_id: ClassVar[str] = "example.bench-heater/v1"
    writable_properties = ("temperature", "ramp_rate")
    required_configuration = ("temperature", "ramp_rate")
    supported_operations = (Heater.start, Heater.stop)


class ThermalRecordingTarget:
    """Compile to semantic JSON with an explicit trusted fixed reference binding."""

    target_id = "example.thermal-recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Bind the logical heater to one reference actuator."""
        return DeviceBindings(
            devices=(bind_device(logical_id="heater", device=BenchHeater(), physical_id="reference:heater-1"),)
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """Reference recording adds no native target restrictions."""
        return ()

    def emit(self, program: Program) -> Artifact:
        """Produce JSON, never label this recording as ASFP."""
        return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")


def build_program() -> Program:
    """Build the same fixed heater flow without source analysis."""
    return Program(
        entry_function_id="warm",
        device_types=(BASE_DEVICE_CONTRACT, HEATER_CONTRACT),
        resources=(DeviceResource(node_id="heater", logical_id="heater", device_type_id=HEATER_CONTRACT.type_id),),
        functions=(
            FunctionIR(
                node_id="warm",
                name="WarmSample",
                body=(
                    ConfigureProperty(
                        node_id="set-temperature",
                        resource_id="heater",
                        property_id=HEATER_TEMPERATURE_ID,
                        value=Literal(node_id="temperature", type=ScalarType.TEMPERATURE, value=293.15),
                    ),
                    ConfigureProperty(
                        node_id="set-rate",
                        resource_id="heater",
                        property_id=HEATER_RAMP_RATE_ID,
                        value=Literal(node_id="rate", type=ScalarType.TEMPERATURE_RATE, value=1 / 60),
                    ),
                    DeviceCommand(node_id="start", resource_id="heater", operation_id=START_HEATER_ID),
                    Wait(node_id="wait", duration=Literal(node_id="duration", type=ScalarType.DURATION, value=10.0)),
                    DeviceCommand(node_id="stop", resource_id="heater", operation_id=STOP_HEATER_ID),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    target = ThermalRecordingTarget()
    authored = WarmSample().compile(target=target)
    program = build_program()
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(program), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == program
    states = []
    for candidate in (authored.semantic_ir, authored.specialized_ir, restored):
        clock = VirtualClock()
        result = Interpreter(
            candidate, environment=ReferenceEnvironment(clock=clock, device_bindings=target.resolve_devices(candidate))
        ).run()
        state = next(iter(result.resources.values()))
        states.append(state)
        assert clock.monotonic() == 10.0
    assert states[0] == states[1] == states[2]
    saved = states[0].configuration["temperature"]
    assert isinstance(saved, Temperature)
    assert not states[0].enabled
    print(path.name)
    print(f"Elapsed: {clock.monotonic():.1f} s; enabled: {states[0].enabled}; saved target: {saved.kelvin:.2f} K")
