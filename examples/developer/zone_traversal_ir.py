"""For developers: index and group Zone values through direct IR and JSON v4.

Run: ``uv run python -m examples.developer.zone_traversal_ir``
Expected terminal output:
    zone_traversal_ir.json
    First well: ('well:27',)
    Groups: 2
    Last group: ('well:8', 'well:2')

The complete semantic program is zone_traversal_ir.json beside this file. This
reference example uses groups of two; AutoSuite currently rejects grouped
traversal and indexing until runtime failure propagation has been verified.
Single-well native traversal is demonstrated in examples/visit_locations.py.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    ForEachZone,
    FunctionIR,
    If,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    ZoneGet,
    ZoneLength,
    ZoneLiteral,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.locations import Zone


def build_program() -> Program:
    """Select the first well, then count complete pairs in a captured selection."""
    return Program(
        entry_function_id="visit",
        functions=(
            FunctionIR(
                node_id="visit",
                name="VisitPairs",
                variables=(
                    Variable(node_id="rack", owner_id="visit", name="rack", type=ZoneType(), role=VariableRole.INPUT),
                    Variable(
                        node_id="first", owner_id="visit", name="first", type=ZoneType(), role=VariableRole.OUTPUT
                    ),
                    Variable(
                        node_id="groups",
                        owner_id="visit",
                        name="groups",
                        type=ScalarType.INTEGER,
                        role=VariableRole.OUTPUT,
                    ),
                    Variable(node_id="last", owner_id="visit", name="last", type=ZoneType(), role=VariableRole.OUTPUT),
                    Variable(
                        node_id="fragment",
                        owner_id="visit",
                        name="fragment",
                        type=ZoneType(),
                        role=VariableRole.INTERNAL,
                        initial=ZoneLiteral(node_id="initial-fragment"),
                    ),
                ),
                body=(
                    Assignment(
                        node_id="empty-first",
                        target=Reference(node_id="first-reset", symbol_id="first"),
                        value=ZoneLiteral(node_id="empty"),
                    ),
                    Assignment(
                        node_id="reset-count",
                        target=Reference(node_id="groups-reset", symbol_id="groups"),
                        value=Literal(node_id="zero", type=ScalarType.INTEGER, value=0),
                    ),
                    If(
                        node_id="nonempty",
                        condition=Binary(
                            node_id="positive",
                            op=BinaryOp.GREATER,
                            left=ZoneLength(node_id="length", value=Reference(node_id="length-rack", symbol_id="rack")),
                            right=Literal(node_id="empty-count", type=ScalarType.INTEGER, value=0),
                        ),
                        then_body=(
                            Assignment(
                                node_id="first-well",
                                target=Reference(node_id="first-write", symbol_id="first"),
                                value=ZoneGet(
                                    node_id="get",
                                    value=Reference(node_id="index-rack", symbol_id="rack"),
                                    index=Literal(node_id="index", type=ScalarType.INTEGER, value=0),
                                ),
                            ),
                        ),
                    ),
                    ForEachZone(
                        node_id="visit-pairs",
                        target=Reference(node_id="current", symbol_id="fragment"),
                        value=Reference(node_id="loop-rack", symbol_id="rack"),
                        fragment_size=2,
                        body=(
                            Assignment(
                                node_id="increment",
                                target=Reference(node_id="groups-write", symbol_id="groups"),
                                value=Binary(
                                    node_id="add",
                                    op=BinaryOp.ADD,
                                    left=Reference(node_id="groups-read", symbol_id="groups"),
                                    right=Literal(node_id="one", type=ScalarType.INTEGER, value=1),
                                ),
                            ),
                        ),
                    ),
                    Assignment(
                        node_id="last-group",
                        target=Reference(node_id="last-write", symbol_id="last"),
                        value=Reference(node_id="fragment-read", symbol_id="fragment"),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    assert program == build_program()
    result = Interpreter(program).run(inputs={"rack": Zone(well_ids=("well:27", "well:0", "well:8", "well:2"))})
    first, last = result.outputs["first"], result.outputs["last"]
    assert isinstance(first, Zone) and isinstance(last, Zone)
    print(path.name)
    print("First well:", first.well_ids)
    print("Groups:", result.outputs["groups"])
    print("Last group:", last.well_ids)
