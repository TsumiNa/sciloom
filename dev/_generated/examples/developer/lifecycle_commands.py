"""For contributors: declare effects and record them with an independent target.

Run: ``uv run python -m examples.developer.lifecycle_commands``
Expected output:
    lifecycle_commands.json
    Applied gain: 2.0
    Saved gain: 3.0
    Enabled: False

The complete JSON v4 companion is generated beside this module. The recording
target validates device contracts without hardware I/O. Reference execution
applies captured configuration, reapplies changed values, then disables while
retaining both snapshots. It does not prove AutoSuite or hardware acceptance.
"""

from pathlib import Path
from typing import ClassVar

from sciloom import Function, Var, rpm, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import LifecycleEffect, Program, from_json, to_json
from sciloom.devices import Agitator, operation
from sciloom.devices.declarations import bind_device
from .source_paths import repository_relative


class AdjustableAgitator(Agitator):
    """An author's extension, leaving the generic family unchanged."""

    device_type_id: ClassVar[str] = "example.adjustable-agitator/v1"
    required_configuration: ClassVar[tuple[str, ...]] = ("speed", "gain")

    @property
    def gain(self) -> float:
        """Write-only logical configuration."""
        raise TypeError("Runtime configuration is write-only.")

    @gain.setter
    @operation(id="example.adjustable-agitator.gain/v1")
    def gain(self, value: float) -> None:
        """Capture gain without applying it."""

    @operation(id="example.adjustable-agitator.apply/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE)
    def apply(self) -> None:
        """Apply the complete saved configuration and enable."""

    @operation(id="example.adjustable-agitator.halt/v1", lifecycle=LifecycleEffect.DISABLE)
    def halt(self) -> None:
        """Disable while retaining saved and applied configuration."""


class BenchAgitator(AdjustableAgitator):
    """An explicit reference deployment, not an AutoSuite profile."""

    device_type_id: ClassVar[str] = "example.bench-agitator/v1"
    writable_properties = ("speed", "gain")
    required_configuration = ("speed", "gain")
    supported_operations = (Agitator.start, Agitator.stop, AdjustableAgitator.apply, AdjustableAgitator.halt)


class RecordingTarget:
    """Record validated device intent using only contributor-facing interfaces."""

    target_id = "example.recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Bind the declared logical dependency to a trusted contract."""
        return DeviceBindings(
            devices=(bind_device(logical_id="agitator", device=BenchAgitator(), physical_id="bench-actuator-1"),)
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """No additional target restrictions on validated core semantics."""
        return ()

    def emit(self, program: Program) -> Artifact:
        """Record semantic JSON without transforming it into target tasks."""
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")


class Reconfigure(Function):
    """Capture, apply, reapply and disable using explicit effects."""

    agitator: AdjustableAgitator
    gain: Var[float] = 1.0

    @runtime
    def run(self) -> None:
        self.gain = 1.0
        self.agitator.speed = 600 * rpm
        self.agitator.gain = self.gain
        self.gain = 2.0
        self.agitator.apply()
        self.agitator.gain = self.gain
        self.agitator.apply()
        self.agitator.gain = 3.0
        self.agitator.halt()


if __name__ == "__main__":
    target = RecordingTarget()
    compiled = Reconfigure().compile(target=target)
    program = repository_relative(compiled.specialized_ir)
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(program), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == program
    result = Interpreter(
        restored, environment=ReferenceEnvironment(device_bindings=target.resolve_devices(restored))
    ).run()
    state = result.resources["resource:agitator"]
    assert state.configuration == {"speed": 600 * rpm, "gain": 3.0}
    assert state.applied_configuration == {"speed": 600 * rpm, "gain": 2.0}
    assert not state.enabled
    print(path.name)
    print(f"Applied gain: {state.applied_configuration['gain']}")
    print(f"Saved gain: {state.configuration['gain']}")
    print(f"Enabled: {state.enabled}")
