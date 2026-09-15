"""For experiment authors: supply the speed and choose whether to stir.

Run from the repository root:
    uv run python examples/tutorial/control_shaker.py

Expected terminal output:
    control_shaker.asfp

Compilation writes the function package; it does not run equipment.
Speeds and volume thresholds illustrate programming, not experimental guidance.
Full generated output: control_shaker.asfp, beside this source file.
"""

from pathlib import Path

from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class StirRack(Function):
    """Start at the supplied speed, or stop the shaker.

    Attributes:
        shaker: Shaker used for the samples.
        speed: Requested speed when enabled.
        enabled: Whether to start or stop.
    """

    shaker: Agitator
    speed: Input[RotationalSpeed]
    enabled: Input[bool]

    @runtime
    def run(self) -> None:
        if self.enabled:
            self.shaker.speed = self.speed
            self.shaker.start()
        else:
            self.shaker.stop()


if __name__ == "__main__":
    target = AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
    )
    path = StirRack().compile(target=target).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
