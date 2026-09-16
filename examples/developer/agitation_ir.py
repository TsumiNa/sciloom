"""For SciLoom developers: persist IR and exercise its reference semantics.

Run from the repository root:
    uv run python -m examples.developer.agitation_ir

Expected terminal output:
    agitation_ir.json
    Configured: {'speed': RotationalSpeed(rps=10.0)}
    Applied before start: {}
    Started: True {'speed': RotationalSpeed(rps=10.0)}
    Stopped: False {'speed': RotationalSpeed(rps=10.0)}

Full generated output: agitation_ir.json, beside this source file. Source paths
are rewritten relative to the repository root so the committed companion file
does not depend on the checkout that produced it.

The JSON file stores the same Function's Program. Reloading it preserves the IR.
The first run saves 600 rpm (10 revolutions per second), then explicitly starts.
The configuration event precedes application. The second run stops agitation
while retaining both saved and last-applied configurations in reference state.
These are reference-model states, not measurements of a physical device.

Reuse the experiment author's Function, then inspect the compiler boundary.
This developer example writes JSON and executes the restored IR; it emits no ASFP.
"""

from pathlib import Path

from examples.agitation import ConfigureAgitation
from sciloom import rpm
from sciloom.core.interpreter import DeviceEvent, Interpreter
from sciloom.core.ir import from_json, to_json
from .source_paths import repository_relative

if __name__ == "__main__":
    function = ConfigureAgitation()
    program = repository_relative(function.to_ir())

    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(program), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == program

    session = Interpreter(restored)
    started = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": True})
    stopped = session.run(inputs={"shaker_speed": 600 * rpm, "enabled": False})
    first_event = started.events[0]
    assert isinstance(first_event, DeviceEvent)
    configured = first_event.state
    assert configured.configuration == {"speed": 600 * rpm}
    assert not configured.enabled and not configured.applied_configuration

    print(path.name)
    resource_id = program.resources[0].node_id
    active = started.resources[resource_id]
    inactive = stopped.resources[resource_id]
    assert active.enabled and not inactive.enabled
    assert active.configuration == inactive.configuration == inactive.applied_configuration
    print("Configured:", dict(configured.configuration))
    print("Applied before start:", dict(configured.applied_configuration))
    print("Started:", active.enabled, dict(active.applied_configuration))
    print("Stopped:", inactive.enabled, dict(inactive.applied_configuration))
