"""For SciLoom developers: persist IR and exercise its reference semantics.

Run from the repository root:
    uv run python -m examples.developer.agitation_ir

Expected terminal output:
    dist/developer/agitation.ir.json
    Started: AgitationState(enabled=True, speed=RotationalSpeed(rps=10.0))
    Stopped: AgitationState(enabled=False, speed=RotationalSpeed(rps=10.0))

The JSON file stores the same Function's Program. Reloading it preserves the IR.
The first run commands 600 rpm (10 revolutions per second); the second disables
agitation while retaining the last known commanded speed in reference state.
These are reference-model states, not measurements of a physical device.

Reuse the experiment author's Function, then inspect the compiler boundary.
This developer example writes JSON and executes the restored IR; it emits no ASFP.
"""

from pathlib import Path

from examples.agitation import ConfigureAgitation
from sciloom import Agitator, rpm
from sciloom.interpreter import Interpreter
from sciloom.ir import from_json, to_json


if __name__ == "__main__":
    function = ConfigureAgitation(Agitator("reaction_mixer"))
    program = function.to_ir()

    path = Path("dist/developer/agitation.ir.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(program), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == program

    session = Interpreter(restored)
    started = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": True})
    stopped = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": False})
    assert started.events[0].enabled and started.events[0].speed == 600 * rpm
    assert not stopped.events[0].enabled and stopped.events[0].speed == 600 * rpm

    print(path)
    resource_id = program.resources[0].node_id
    print("Started:", started.resources[resource_id])
    print("Stopped:", stopped.resources[resource_id])
