"""For experiment authors: choose a stirring speed from a list of volumes.

Run from the repository root:
    uv run python examples/tutorial/stir_sample_rack.py

Expected terminal output:
    stir_sample_rack.asfp

The largest supplied volume selects the speed. No volume is measured.
Compiling writes a package without running equipment; the thresholds and speeds
are programming examples.
Full generated output: stir_sample_rack.asfp, beside this source file.
"""

from pathlib import Path

from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class ChooseSpeed(Function):
    """Choose a stirring speed from a sample volume.

    Attributes:
        volume: Sample volume in millilitres.
        speed: A gentle speed for small volumes, a faster one otherwise.
    """

    volume: Input[float]
    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if self.volume < 2.0:
            self.speed = 300 * rpm
        else:
            self.speed = 600 * rpm


class LargestVolume(Function):
    """Find the largest volume in a rack.

    Attributes:
        volumes: Volume of every vial in the rack.
        largest: The largest volume, or 0.0 for an empty rack.
        index: Loop position, reset on every call.
    """

    volumes: Input[list[float]]
    largest: Output[float]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.largest = 0.0
        self.index = 0
        while self.index < len(self.volumes):
            if self.volumes[self.index] > self.largest:
                self.largest = self.volumes[self.index]
            self.index += 1


class StirRack(Function):
    """Stir a rack at a speed chosen from its largest sample, or stop.

    Attributes:
        volumes: Volume of every vial in the rack.
        enabled: Whether the rack should be stirring after this call.
        shaker: Logical agitator; the target binds the hardware.
        largest: Largest volume calculated from the input list.
        speed: Speed chosen for that volume.
    """

    volumes: Input[list[float]]
    enabled: Input[bool]
    shaker: Agitator
    largest: Var[float] = 0.0
    speed: Var[RotationalSpeed] = 0 * rpm

    def __init__(self) -> None:
        self.measure = LargestVolume()
        self.choose = ChooseSpeed()

    @runtime
    def run(self) -> None:
        self.largest = self.measure(volumes=self.volumes)
        self.speed = self.choose(volume=self.largest)
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
