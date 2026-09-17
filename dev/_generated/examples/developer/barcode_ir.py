"""For developers: direct barcode IR, JSON and explicit reference services.

Run: ``uv run python -m examples.developer.barcode_ir``
Expected terminal output:
    barcode_ir.json
    Barcode: S-001
    Stored: S-001
    Events: DialogEvent, WellPropertyWriteEvent, LogEvent

The complete JSON v4 companion is barcode_ir.json. This program matches the
author example capture_barcode.py; it specifies behavior without hardware I/O.
Native result-dialog and dynamic single-well checks remain gated.
"""

from pathlib import Path

from sciloom.core.interpreter import (
    DialogOutcome,
    DialogResponse,
    Interpreter,
    QueuedDialogResponses,
    ReferenceEnvironment,
    WellProperties,
)
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    FunctionIR,
    Literal,
    LogValue,
    Program,
    Reference,
    RequestText,
    ScalarType,
    Variable,
    VariableRole,
    WellName,
    WellPropertySpec,
    WriteWellProperty,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.locations import LocationDirectory, Well, Zone


def build_program() -> Program:
    """Capture a result and write metadata only after a valid single-well request."""
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="CaptureBarcode",
                variables=(
                    Variable(node_id="well", owner_id="f", name="well", type=ZoneType(), role=VariableRole.INPUT),
                    Variable(
                        node_id="barcode", owner_id="f", name="barcode", type=ScalarType.TEXT, role=VariableRole.OUTPUT
                    ),
                    Variable(
                        node_id="name",
                        owner_id="f",
                        name="well_name",
                        type=ScalarType.TEXT,
                        role=VariableRole.INTERNAL,
                        initial=Literal(node_id="empty-name", type=ScalarType.TEXT, value=""),
                    ),
                ),
                body=(
                    Assignment(
                        node_id="capture-name",
                        target=Reference(node_id="name-target", symbol_id="name"),
                        value=WellName(node_id="well-name", value=Reference(node_id="name-well", symbol_id="well")),
                    ),
                    RequestText(
                        node_id="request",
                        target=Reference(node_id="barcode-target", symbol_id="barcode"),
                        message=Binary(
                            node_id="prompt",
                            op=BinaryOp.ADD,
                            left=Literal(node_id="prefix", type=ScalarType.TEXT, value="Barcode for "),
                            right=Reference(node_id="captured-name", symbol_id="name"),
                        ),
                        timeout=Literal(node_id="deadline", type=ScalarType.DURATION, value=30.0),
                    ),
                    WriteWellProperty(
                        node_id="write",
                        property=WellPropertySpec(name="sample_ID", type=ScalarType.TEXT),
                        zone=Reference(node_id="write-well", symbol_id="well"),
                        value=Reference(node_id="write-barcode", symbol_id="barcode"),
                    ),
                    LogValue(
                        node_id="log",
                        value=Reference(node_id="log-barcode", symbol_id="barcode"),
                        category=Literal(node_id="category", type=ScalarType.TEXT, value="samples"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="barcode"),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    properties = WellProperties()
    environment = ReferenceEnvironment(
        locations=LocationDirectory(wells=(Well(identity="rack/1", name="A1"),)),
        properties=properties,
        dialogs=QueuedDialogResponses([DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001")]),
    )
    result = Interpreter(program, environment=environment).run(inputs={"well": Zone(well_ids=("rack/1",))})
    print(path.name)
    print(f"Barcode: {result.outputs['barcode']}")
    print(f"Stored: {properties.snapshot()[('rack/1', 'sample_ID')]}")
    print("Events: " + ", ".join(type(event).__name__ for event in result.events))
