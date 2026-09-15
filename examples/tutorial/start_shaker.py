"""For experiment authors: compile a fixed-speed stirring procedure.

Run from the repository root:
    uv run python examples/tutorial/start_shaker.py

Expected terminal output:
    start_shaker.asfp

When AutoSuite calls the generated function, it saves 300 rpm and starts the
bound shaker. Compiling this file does not run the experiment. The speed is a
programming example, not a recommendation for a particular sample.

Full generated output: start_shaker.asfp, beside this source file.
"""

from pathlib import Path

from sciloom import Agitator, Function, rpm, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class StirRack(Function):
    """Start the shaker at 300 rpm.

    Attributes:
        shaker: Shaker used for the samples.
    """

    shaker: Agitator

    @runtime
    def run(self) -> None:
        self.shaker.speed = 300 * rpm
        self.shaker.start()


if __name__ == "__main__":
    target = AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
    )
    path = StirRack().compile(target=target).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
