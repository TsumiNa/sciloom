"""For developers: construct a typed log, round-trip JSON and inspect its event.

Run: ``uv run python -m examples.developer.logging_ir``
Expected terminal output:
    logging_ir.json
    recipe/volume: 1.0 mL

The complete JSON v4 document is logging_ir.json beside this file. Reference
execution captures one volume event without accessing a file or instrument.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, LogEvent
from sciloom.core.ir import FunctionIR, Literal, LogValue, Program, ScalarType, from_json, to_json
from sciloom.units import Volume, mL


def build_program() -> Program:
    """Build a single volume-log statement without the Python DSL."""
    record = LogValue(
        node_id="record",
        value=Literal(node_id="value", type=ScalarType.VOLUME, value=1e-6),
        category=Literal(node_id="category", type=ScalarType.TEXT, value="recipe"),
        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="volume"),
    )
    return Program(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Record", body=(record,)),))


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == build_program()
    (event,) = Interpreter(restored).run().events
    assert isinstance(event, LogEvent) and isinstance(event.value, Volume)
    assert event.type == ScalarType.VOLUME and event.value == 1 * mL
    print(path.name)
    print(f"{event.category}/{event.stream}: {event.value / mL} mL")
