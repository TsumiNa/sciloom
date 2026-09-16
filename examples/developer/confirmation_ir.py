"""For developers: supply an explicit acknowledgement to a JSON-restored program.

Run: ``uv run python -m examples.developer.confirmation_ir``
Expected terminal output:
    confirmation_ir.json
    Acknowledged: Samples are ready. Confirm to continue.
    Responses remaining: 0

The complete JSON v4 document is confirmation_ir.json beside this file. Reference
execution consumes a supplied response; it never opens or auto-confirms a dialog.
"""

from pathlib import Path

from sciloom.core.interpreter import AcknowledgementEvent, Interpreter, QueuedAcknowledgements, ReferenceEnvironment
from sciloom.core.ir import FunctionIR, Literal, Notify, Program, ScalarType, from_json, to_json


def build_program() -> Program:
    """Construct one acknowledgement operation directly in typed IR."""
    notification = Notify(
        node_id="confirm",
        message=Literal(node_id="message", type=ScalarType.TEXT, value="Samples are ready. Confirm to continue."),
    )
    return Program(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Confirm", body=(notification,)),))


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == build_program()
    responses = QueuedAcknowledgements([True])
    environment = ReferenceEnvironment(acknowledgements=responses)
    (event,) = Interpreter(restored, environment=environment).run().events
    assert isinstance(event, AcknowledgementEvent)
    print(path.name)
    print(f"Acknowledged: {event.message}")
    print(f"Responses remaining: {responses.remaining}")
