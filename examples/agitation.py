"""A conditional agitation program, reference execution, and AutoSuite compilation.

The operation comes from Sample and Run GPC; this is not that entire workflow.
The fixed zone/shaker binding is taken from the latest application configuration.
No command is sent to a device.
"""

from pathlib import Path

from sciloom import Agitator, Boolean, Function, Input, RotationalSpeed, compile_ir, rpm, runtime
from sciloom.backends.autosuite import AutoSuiteTarget, IndividualShakerBinding
from sciloom.interpreter import Interpreter
from sciloom.ir import from_json, to_json


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
    program = from_json(to_json(function.to_ir()))
    session = Interpreter(program)
    started = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": True})
    stopped = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": False})
    assert started.events[0].enabled and started.events[0].speed == 600 * rpm
    assert not stopped.events[0].enabled and stopped.events[0].speed == 600 * rpm
    print("Reference commands:", started.events, stopped.events)

    target = AutoSuiteTarget(
        agitators=(
            IndividualShakerBinding(
                logical_id="reaction_mixer",
                zone="Heater Shaker 23",
                device_id="23",
            ),
        )
    )
    result = compile_ir(program, target=target)
    path = result.write(Path("dist") / "agitation.asfp")
    path.with_suffix(".ir.json").write_text(to_json(program), encoding="utf-8")
    print(path)
