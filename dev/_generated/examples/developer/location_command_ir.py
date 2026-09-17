"""Contributor example: Zone command arguments retain types and declared order.

Run: uv run python -m examples.developer.location_command_ir
Output:
    location_command_ir.json
    Parameters: source, destination, flow
    Reference execution rejects the unknown inspect command.

The complete companion is location_command_ir.json. The recording target emits
JSON only, never hardware XML. This example extends Agitator by subclassing;
the extra command's unknown semantics are deliberately not executable.
"""

from pathlib import Path
from typing import ClassVar

from sciloom import Agitator, FlowRate, Function, Input, Zone, mL_per_min, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.diagnostics import Diagnostic, ExecutionError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import DeviceCommand, Program, from_json, to_json
from sciloom.devices import operation
from sciloom.devices.declarations import bind_device
from .source_paths import repository_relative


class LocatedAgitator(Agitator):
    device_type_id: ClassVar[str] = "example.located-agitator/v1"

    @operation(id="example.located-agitator.inspect/v1")
    def inspect(self, source: Zone, destination: Zone, flow: FlowRate) -> None:
        raise AssertionError("Source analysis must never execute a device method.")


class InspectLocations(Function):
    device: LocatedAgitator
    source: Input[Zone]
    destination: Input[Zone]

    @runtime
    def run(self) -> None:
        self.device.inspect(destination=self.destination, flow=1 * mL_per_min, source=self.source)


class RecordingProfile(LocatedAgitator):
    device_type_id: ClassVar[str] = "example.located-recording/v1"
    writable_properties = ("speed",)
    required_configuration = ("speed",)
    supported_operations = (LocatedAgitator.inspect,)


class RecordingTarget:
    target_id = "example.located-recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(
            devices=(
                bind_device(
                    logical_id="device",
                    device=RecordingProfile(),
                    physical_id="reference:located-1",
                ),
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")


if __name__ == "__main__":
    program = repository_relative(InspectLocations().to_ir())
    result = compile_ir(program, target=RecordingTarget())
    output = Path(__file__).with_suffix(".json")
    output.write_bytes(result.artifact.content)
    restored = from_json(output.read_text())
    command = restored.functions[0].body[0]
    assert isinstance(command, DeviceCommand)
    print(output.name)
    print("Parameters: " + ", ".join(argument.name for argument in command.arguments))
    try:
        Interpreter(restored).run(inputs={"source": Zone.empty(), "destination": Zone.empty()})
    except ExecutionError as error:
        if not all(d.code == "unsupported_operation" for d in error.diagnostics):
            raise
        print("Reference execution rejects the unknown inspect command.")
