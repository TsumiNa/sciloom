"""For experiment authors: define conditional agitation and export an ASFP.

Run from the repository root:
    uv run python examples/agitation.py

Expected terminal output:
    agitation.asfp

The package contains ConfigureAgitation with two runtime inputs:
shaker_speed (angularspeed) and enabled (bool). When enabled is true, it sets
the supplied speed on Heater Shaker 23; otherwise it disables agitation.
The speed stays an input parameter; compiling does not choose a speed or send
commands to hardware.

Full generated output: agitation.asfp, beside this source file.

Generated ASFP excerpts (metadata and other fields omitted):

    Enabled branch:
        <condition>enabled</condition>
        ...
        <component typeid="Chemspeed.SATaskSetAgitation.1">
          <zone>Heater Shaker 23</zone>
          <!-- metadata omitted -->
          <taskdatas>
            <count>1</count>
            <taskdata0>
              <progid>Chemspeed.SADeviceIndividualShaker.1</progid>
              <deviceid>23</deviceid>
              <wellid>-1</wellid>
              <speed>shaker_speed</speed>
            </taskdata0>
          </taskdatas>
          <switchon>1</switchon>
          <speedunit>rpm</speedunit>
          <!-- remaining fields omitted -->
        </component>

    Disabled branch's Stir task:
        <switchon>0</switchon>

The operation comes from Sample and Run GPC; this is not that entire workflow.
The fixed zone/shaker binding is taken from the latest application configuration.
"""

from pathlib import Path

from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom.contrib.autosuite import AutoSuiteTarget, IndividualShakerBinding


class ConfigureAgitation(Function):
    """Set or disable a logical agitator using runtime inputs.

    Attributes:
        shaker_speed: Commanded rotational speed when enabled.
        enabled: Whether agitation should be enabled.
    """

    shaker_speed: Input[RotationalSpeed]
    enabled: Input[bool]

    def __init__(self, agitator: Agitator) -> None:
        """Bind a logical component during host specialization.

        Args:
            agitator: Logical resource; the compilation target selects hardware.
        """
        self.agitator = agitator

    @runtime
    def run(self) -> None:
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
    path = result.write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
