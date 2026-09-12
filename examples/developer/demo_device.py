"""Compile an independent contribution, without AutoSuite imports or hardware I/O.

Run: uv run python -m examples.developer.demo_device

Expected output:
    demo_device.json
    ConfigureProperty, ConfigureProperty, StartAgitation, DeviceCommand, StopAgitation

The companion JSON is the recording target's output. calibrate() is a declared
native request, not an operation the reference interpreter knows how to execute.
"""

from pathlib import Path

from sciloom import Function, rpm, runtime
from .demo_contribution import DemoAgitator, DemoTarget


class DemoExperiment(Function):
    """Configure, start, request native calibration and stop a test device.

    Attributes:
        agitator: Demo device with gain and calibration support.
    """

    agitator: DemoAgitator

    @runtime
    def run(self) -> None:
        self.agitator.speed = 600 * rpm
        self.agitator.gain = 0.5
        self.agitator.start()
        self.agitator.calibrate()
        self.agitator.stop()


if __name__ == "__main__":
    result = DemoExperiment().compile(target=DemoTarget(devices={"agitator": DemoAgitator()}))
    path = result.write(Path(__file__).with_suffix(".json"))
    print(path.name)
    print(", ".join(type(node).__name__ for node in result.semantic_ir.functions[0].body))
