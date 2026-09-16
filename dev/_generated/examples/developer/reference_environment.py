"""For developers: share an event history while keeping session state separate.

Run from the repository root:
    uv run python -m examples.developer.reference_environment

Expected terminal output:
    First run events: 2
    Second run events: 1
    Environment events: 3
    First session enabled: True
    Second session enabled: False

These are reference states, not hardware measurements. Reusing the environment
combines event history; it does not merge the two sessions' device configuration.
This example produces only the short terminal output above.
"""

from examples.agitation import ConfigureAgitation
from sciloom import rpm
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment

if __name__ == "__main__":
    program = ConfigureAgitation().to_ir()
    environment = ReferenceEnvironment()
    first = Interpreter(program, environment=environment)
    second = Interpreter(program, environment=environment)

    started = first.run(inputs={"shaker_speed": 300 * rpm, "enabled": True})
    stopped = second.run(inputs={"shaker_speed": 300 * rpm, "enabled": False})
    assert environment.events == started.events + stopped.events
    resource = program.resources[0].node_id
    assert not stopped.resources[resource].configuration

    print("First run events:", len(started.events))
    print("Second run events:", len(stopped.events))
    print("Environment events:", len(environment.events))
    print("First session enabled:", started.resources[resource].enabled)
    print("Second session enabled:", stopped.resources[resource].enabled)
