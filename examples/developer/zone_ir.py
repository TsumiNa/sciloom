"""For developers: pass Zone values through JSON and a fixed reference directory.

Run: ``uv run python -m examples.developer.zone_ir``
Expected terminal output:
    zone_ir.json
    Selected wells: ('well:27', 'well:0', 'well:8')
    Count: 3

zone_ir.json is the complete direct-IR companion. The synthetic identities denote
physical wells, not positions in the result. Reference execution performs no
hardware I/O. A real APP directory can instead be read with
AutoSuiteLayout.from_app(path).directory, without changing that APP.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import (
    Assignment,
    FunctionIR,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    ZoneCombine,
    ZoneFind,
    ZoneLength,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.locations import LocationDirectory, Well, Zone


def build_program() -> Program:
    """Build typed location queries, leaving the directory outside serialized IR."""
    return Program(
        entry_function_id="resolve",
        functions=(
            FunctionIR(
                node_id="resolve",
                name="ResolveLocations",
                variables=tuple(
                    Variable(node_id=name, owner_id="resolve", name=name, type=kind, role=role)
                    for name, kind, role in (
                        ("first_name", ScalarType.TEXT, VariableRole.INPUT),
                        ("second_name", ScalarType.TEXT, VariableRole.INPUT),
                        ("selected", ZoneType(), VariableRole.OUTPUT),
                        ("count", ScalarType.INTEGER, VariableRole.OUTPUT),
                    )
                ),
                body=(
                    Assignment(
                        node_id="combine",
                        target=Reference(node_id="selected-write", symbol_id="selected"),
                        value=ZoneCombine(
                            node_id="union",
                            left=ZoneFind(node_id="first", name=Reference(node_id="name1", symbol_id="first_name")),
                            right=ZoneFind(node_id="second", name=Reference(node_id="name2", symbol_id="second_name")),
                        ),
                    ),
                    Assignment(
                        node_id="count-write",
                        target=Reference(node_id="count-target", symbol_id="count"),
                        value=ZoneLength(
                            node_id="length", value=Reference(node_id="selected-read", symbol_id="selected")
                        ),
                    ),
                ),
            ),
        ),
    )


def example_directory() -> LocationDirectory:
    """Supply overlapping named selections in a deliberately nonnumeric order."""
    return LocationDirectory(
        wells=tuple(Well(identity=f"well:{number}", name=f"Rack: Well #{number}") for number in (0, 8, 27)),
        zones={
            "first rack": Zone(well_ids=("well:27", "well:0")),
            "second rack": Zone(well_ids=("well:0", "well:8")),
        },
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    assert program == build_program()
    result = Interpreter(program, environment=ReferenceEnvironment(locations=example_directory())).run(
        inputs={"first_name": "first rack", "second_name": "second rack"}
    )
    selected = result.outputs["selected"]
    assert isinstance(selected, Zone)
    print(path.name)
    print("Selected wells:", selected.well_ids)
    print("Count:", result.outputs["count"])
