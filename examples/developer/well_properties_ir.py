"""For developers: write/read stored labels through direct IR and explicit services.

Run: ``uv run python -m examples.developer.well_properties_ir``
Expected terminal output:
    well_properties_ir.json
    Last label: batch A
    Properties: {('rack/2', 'sample_ID'): 'batch A', ('rack/1', 'sample_ID'): 'batch A'}

The complete JSON v4 program is well_properties_ir.json. This has the same
behavior as examples/label_wells.py. The directory supplies identities; the
separate mutable property store supplies metadata. Neither accesses equipment.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, WellProperties
from sciloom.core.ir import (
    Assignment,
    ForEachZone,
    FunctionIR,
    Literal,
    Program,
    ReadWellProperty,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    WellPropertySpec,
    WriteWellProperty,
    ZoneLiteral,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.locations import LocationDirectory, Well, Zone


def build_program() -> Program:
    """Express stored-label write and sequential readback without Python source."""
    prop = WellPropertySpec(name="sample_ID", type=ScalarType.TEXT)
    return Program(
        entry_function_id="label-wells",
        functions=(
            FunctionIR(
                node_id="label-wells",
                name="LabelWells",
                variables=(
                    Variable(
                        node_id="rack", owner_id="label-wells", name="rack", type=ZoneType(), role=VariableRole.INPUT
                    ),
                    Variable(
                        node_id="label",
                        owner_id="label-wells",
                        name="label",
                        type=ScalarType.TEXT,
                        role=VariableRole.INPUT,
                    ),
                    Variable(
                        node_id="well",
                        owner_id="label-wells",
                        name="well",
                        type=ZoneType(),
                        role=VariableRole.INTERNAL,
                        initial=ZoneLiteral(node_id="empty-well"),
                    ),
                    Variable(
                        node_id="last",
                        owner_id="label-wells",
                        name="last_label",
                        type=ScalarType.TEXT,
                        role=VariableRole.OUTPUT,
                    ),
                ),
                body=(
                    WriteWellProperty(
                        node_id="write-labels",
                        property=prop,
                        zone=Reference(node_id="write-rack", symbol_id="rack"),
                        value=Reference(node_id="input-label", symbol_id="label"),
                    ),
                    Assignment(
                        node_id="empty-result",
                        target=Reference(node_id="reset-target", symbol_id="last"),
                        value=Literal(node_id="empty-text", type=ScalarType.TEXT, value=""),
                    ),
                    ForEachZone(
                        node_id="read-labels",
                        target=Reference(node_id="iterator", symbol_id="well"),
                        value=Reference(node_id="read-rack", symbol_id="rack"),
                        body=(
                            ReadWellProperty(
                                node_id="read-one",
                                property=prop,
                                zone=Reference(node_id="current", symbol_id="well"),
                                target=Reference(node_id="result", symbol_id="last"),
                                default=Literal(node_id="fallback", type=ScalarType.TEXT, value=""),
                            ),
                        ),
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
    directory = LocationDirectory(wells=(Well(identity="rack/1", name="First"), Well(identity="rack/2", name="Second")))
    result = Interpreter(program, environment=ReferenceEnvironment(locations=directory, properties=properties)).run(
        inputs={"rack": Zone(well_ids=("rack/2", "rack/1")), "label": "batch A"},
    )
    print(path.name)
    print("Last label:", result.outputs["last_label"])
    print("Properties:", dict(properties.snapshot()))
