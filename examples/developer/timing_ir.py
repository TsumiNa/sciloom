"""For developers: construct timer flow and advance an explicit virtual clock.

Run: ``uv run python -m examples.developer.timing_ir``
Expected terminal output:
    timing_ir.json
    Elapsed: 5.0 s
    Waits: [(0.0, 2.0), (2.0, 5.0)]

The complete JSON v4 document is timing_ir.json beside this file. No real clock,
sleep or equipment is involved. Timer origins are resources owned by FunctionIR.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualClock, WaitEvent
from sciloom.core.ir import (
    FunctionIR,
    Literal,
    Program,
    ScalarType,
    StartTimer,
    TimerResource,
    Wait,
    WaitUntil,
    from_json,
    to_json,
)


def build_program() -> Program:
    """Start a timer, wait two seconds, then wait to the five-second threshold."""
    return Program(
        entry_function_id="timed",
        resources=(TimerResource(node_id="timer", owner_id="timed", name="timer"),),
        functions=(
            FunctionIR(
                node_id="timed",
                name="Timed",
                body=(
                    StartTimer(node_id="start", resource_id="timer"),
                    Wait(node_id="pause", duration=Literal(node_id="two", type=ScalarType.DURATION, value=2.0)),
                    WaitUntil(
                        node_id="finish",
                        resource_id="timer",
                        duration=Literal(node_id="five", type=ScalarType.DURATION, value=5.0),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == build_program()
    clock = VirtualClock()
    result = Interpreter(restored, environment=ReferenceEnvironment(clock=clock)).run()
    print(path.name)
    print(f"Elapsed: {clock.monotonic()} s")
    print("Waits:", [(e.started_at, e.finished_at) for e in result.events if isinstance(e, WaitEvent)])
