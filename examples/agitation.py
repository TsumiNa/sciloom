"""For experiment authors: define conditional agitation and export an ASFP.

Run from the repository root:
    uv run python examples/agitation.py

Expected terminal output:
    agitation.asfp

The package contains ConfigureAgitation with two runtime inputs:
shaker_speed (angularspeed) and enabled (bool). When enabled is true, it saves
the supplied speed and explicitly starts Heater Shaker 23; otherwise it stops.
The speed stays an input parameter; compiling does not choose a speed or send
commands to hardware.

Full generated output: agitation.asfp, beside this source file.

"""

from pathlib import Path

from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class ConfigureAgitation(Function):
    """Save configuration and explicitly start or stop a logical agitator.

    Attributes:
        agitator: Logical device; the compilation target selects hardware.
        shaker_speed: Commanded rotational speed when enabled.
        enabled: Whether agitation should be enabled.
    """

    shaker_speed: Input[RotationalSpeed]
    enabled: Input[bool]

    agitator: Agitator

    @runtime
    def run(self) -> None:
        if self.enabled:
            self.agitator.speed = self.shaker_speed
            self.agitator.start()
        else:
            self.agitator.stop()


if __name__ == "__main__":
    function = ConfigureAgitation()
    target = AutoSuiteTarget(
        devices={
            "agitator": AutoSuiteIndividualShaker(
                zone="Heater Shaker 23",
                device_id="23",
            ),
        }
    )
    result = function.compile(target=target)
    path = result.write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
