"""For developers: restore typed dialog results and supply explicit responses.

Run: ``uv run python -m examples.developer.dialogs_ir``
Expected terminal output:
    dialogs_ir.json
    Barcode: S-001
    Accepted: False
    Responses remaining: 0

The complete direct-IR JSON v4 artifact is dialogs_ir.json beside this file.
The author example is also executed with its own explicit response queue and
must produce the same outputs. This specifies behavior without native dialogs,
clock sampling or hardware execution. AutoSuite result dialogs remain gated.
"""

from pathlib import Path

from examples.identify_sample import IdentifySample
from sciloom import s
from sciloom.core.interpreter import (
    DialogOutcome,
    DialogResponse,
    Interpreter,
    QueuedDialogResponses,
    ReferenceEnvironment,
)
from sciloom.core.ir import (
    AskYesNo,
    FunctionIR,
    Literal,
    Program,
    Reference,
    RequestText,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)


def build_program() -> Program:
    """Construct two ordered result-bearing operations directly in typed IR."""
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="IdentifySample",
                variables=(
                    Variable(
                        node_id="barcode", owner_id="f", name="barcode", type=ScalarType.TEXT, role=VariableRole.OUTPUT
                    ),
                    Variable(
                        node_id="accepted",
                        owner_id="f",
                        name="accepted",
                        type=ScalarType.BOOLEAN,
                        role=VariableRole.OUTPUT,
                    ),
                ),
                body=(
                    RequestText(
                        node_id="request",
                        target=Reference(node_id="barcode_target", symbol_id="barcode"),
                        message=Literal(node_id="scan", type=ScalarType.TEXT, value="Scan barcode"),
                        timeout=Literal(node_id="deadline", type=ScalarType.DURATION, value=30.0),
                    ),
                    AskYesNo(
                        node_id="ask",
                        target=Reference(node_id="accepted_target", symbol_id="accepted"),
                        message=Literal(node_id="confirm", type=ScalarType.TEXT, value="Use this sample?"),
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
    for program in (restored, IdentifySample().to_ir()):
        responses = QueuedDialogResponses(
            (
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001", elapsed=2 * s),
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False, elapsed=1 * s),
            )
        )
        result = Interpreter(program, environment=ReferenceEnvironment(dialogs=responses)).run()
        assert result.outputs == {"barcode": "S-001", "accepted": False}
        assert responses.remaining == 0
    print(path.name)
    print(f"Barcode: {result.outputs['barcode']}")
    print(f"Accepted: {result.outputs['accepted']}")
    print(f"Responses remaining: {responses.remaining}")
