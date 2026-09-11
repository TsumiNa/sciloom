"""For experiment authors: define conditional agitation and export an ASFP.

The operation comes from Sample and Run GPC; this is not that entire workflow.
The fixed zone/shaker binding is taken from the latest application configuration.
Compiling writes a function package; it does not send commands to a device.
"""

from pathlib import Path

from sciloom import Agitator, Boolean, Function, Input, RotationalSpeed, runtime
from sciloom.backends.autosuite import AutoSuiteTarget, IndividualShakerBinding


class ConfigureAgitation(Function):
    shaker_speed: Input[RotationalSpeed]
    enabled: Input[Boolean]

    def __init__(self, agitator: Agitator):
        self.agitator = agitator

    @runtime
    def run(self):
        if self.enabled:
            self.agitator.set_speed(self.shaker_speed)
        else:
            self.agitator.stop()


if __name__ == "__main__":
    function = ConfigureAgitation(Agitator("reaction_mixer"))
    target = AutoSuiteTarget(
        agitators=(
            IndividualShakerBinding(
                logical_id="reaction_mixer",
                zone="Heater Shaker 23",
                device_id="23",
            ),
        )
    )
    result = function.compile(target=target)
    path = result.write(Path("dist") / "agitation.asfp")
    print(path)
