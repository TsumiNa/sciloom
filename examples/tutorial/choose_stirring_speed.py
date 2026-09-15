"""For experiment authors: reuse a Function that chooses a speed.

Run from the repository root:
    uv run python examples/tutorial/choose_stirring_speed.py

Expected terminal output:
    choose_stirring_speed.asfp

Compilation writes the function package; it does not run equipment.
Speeds and volume thresholds illustrate programming, not experimental guidance.
Full generated output: choose_stirring_speed.asfp, beside this source file.
"""

from pathlib import Path

from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class ChooseSpeed(Function):
    """Choose a stirring speed from an input volume.

    Attributes:
        volume: Sample volume in millilitres.
        speed: Speed selected for that volume.
    """

    volume: Input[float]
    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if self.volume < 2.0:
            self.speed = 300 * rpm
        else:
            self.speed = 600 * rpm


class StirRack(Function):
    """Choose a speed from the supplied volume, then start or stop.

    Attributes:
        volume: Sample volume in millilitres.
        enabled: Whether to start or stop.
        shaker: Shaker used for the samples.
        speed: Working value returned by ChooseSpeed.
    """

    volume: Input[float]
    enabled: Input[bool]
    shaker: Agitator
    speed: Var[RotationalSpeed] = 0 * rpm

    def __init__(self) -> None:
        self.choose = ChooseSpeed()

    @runtime
    def run(self) -> None:
        self.speed = self.choose(volume=self.volume)
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
