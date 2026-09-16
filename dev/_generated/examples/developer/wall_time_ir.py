"""For developers: read an explicit wall clock from JSON-restored IR.

Run: ``uv run python -m examples.developer.wall_time_ir``
Expected terminal output:
    wall_time_ir.json
    2026-09-16_140506
    Wall-time reads: 1

The complete JSON v4 document is wall_time_ir.json beside this source. Reference
execution uses the supplied UTC+09:00 instant and never samples the host clock.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualWallClock
from sciloom.core.ir import (
    FunctionIR,
    Program,
    ReadWallTime,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)


def build_program() -> Program:
    """Construct an ordered clock read that writes one text output."""
    function = FunctionIR(
        node_id="timestamp",
        name="Timestamp",
        variables=(
            Variable(
                node_id="stamp", owner_id="timestamp", name="stamp", type=ScalarType.TEXT, role=VariableRole.OUTPUT
            ),
        ),
        body=(
            ReadWallTime(
                node_id="read", target=Reference(node_id="destination", symbol_id="stamp"), format="%Y-%m-%d_%H%M%S"
            ),
        ),
    )
    return Program(entry_function_id="timestamp", functions=(function,))


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == build_program()
    clock = VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone(timedelta(hours=9))))
    result = Interpreter(restored, environment=ReferenceEnvironment(wall_clock=clock)).run()
    print(path.name)
    print(result.outputs["stamp"])
    print(f"Wall-time reads: {len(result.events)}")
