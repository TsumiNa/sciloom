"""For SciLoom developers: persist IR and exercise its reference semantics.

Run from the repository root:
    uv run python -m examples.developer.agitation_ir

Reuse the experiment author's Function, then inspect the compiler boundary.
Reference execution records commands and state; it never controls hardware.
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
    print("Reference commands:", started.events, stopped.events)
