"""Direct IR/JSON traversal checks, retained state and bounded reference execution."""

from dataclasses import replace

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import ExecutionError, IRValidationError, SourceSpan
from sciloom.core.interpreter import ExecutionConfig, Interpreter
from sciloom.core.locations import Zone
from sciloom.core.specialization import specialize
from . import (
    Assignment,
    Binary,
    BinaryOp,
    ForEachZone,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    ZoneGet,
    ZoneLiteral,
    ZoneType,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def traversal(size=1):
    loop = ForEachZone(
        node_id="loop",
        source=SourceSpan(path="rack.py", line=12),
        target=Reference(node_id="target", symbol_id="well"),
        value=Reference(node_id="selection", symbol_id="rack"),
        fragment_size=size,
        body=(
            Assignment(
                node_id="increment",
                target=Reference(node_id="count-write", symbol_id="count"),
                value=Binary(
                    node_id="add",
                    op=BinaryOp.ADD,
                    left=Reference(node_id="count-read", symbol_id="count"),
                    right=Literal(node_id="one", type=ScalarType.INTEGER, value=1),
                ),
            ),
        ),
    )
    function = FunctionIR(
        node_id="f",
        name="VisitRack",
        variables=(
            Variable(node_id="rack", owner_id="f", name="rack", role=VariableRole.INPUT, type=ZoneType()),
            Variable(
                node_id="well",
                owner_id="f",
                name="well",
                role=VariableRole.INTERNAL,
                type=ZoneType(),
                initial=ZoneLiteral(node_id="initial-well", well_ids=("seed",)),
            ),
            Variable(node_id="count", owner_id="f", name="count", role=VariableRole.OUTPUT, type=ScalarType.INTEGER),
            Variable(node_id="last", owner_id="f", name="last", role=VariableRole.OUTPUT, type=ZoneType()),
        ),
        body=(
            Assignment(
                node_id="reset",
                target=Reference(node_id="reset-target", symbol_id="count"),
                value=Literal(node_id="zero", type=ScalarType.INTEGER, value=0),
            ),
            loop,
            Assignment(
                node_id="save",
                target=Reference(node_id="last-target", symbol_id="last"),
                value=Reference(node_id="last-value", symbol_id="well"),
            ),
        ),
    )
    return Program(entry_function_id="f", functions=(function,))


def test_direct_json_specialization_order_empty_and_persistent_target():
    for size in (1, 2):
        program = traversal(size)
        before = to_json(program)
        assert '"kind": "ForEachZone"' in before
        assert to_dict(program)["format_version"] == 4
        for candidate in (program, from_json(before), specialize(program, bindings=DeviceBindings())):
            assert candidate == program
            assert candidate.functions[0].body[1].source == SourceSpan(path="rack.py", line=12)
            session = Interpreter(candidate)
            empty = session.run(inputs={"rack": Zone.empty()})
            assert empty.outputs == {"count": 0, "last": Zone(well_ids=("seed",))}
            result = session.run(inputs={"rack": Zone(well_ids=("27", "0", "8", "2"))})
            assert result.outputs == {"count": 4 // size, "last": Zone(well_ids=("2",) if size == 1 else ("8", "2"))}
            assert session.run(inputs={"rack": Zone.empty()}).outputs["last"] == result.outputs["last"]
            assert empty.outputs["last"] == Zone(well_ids=("seed",))
        assert to_json(program) == before


def test_incomplete_group_fails_before_target_write_and_does_not_poison_next_run():
    session = Interpreter(traversal(2))
    with pytest.raises(ExecutionError, match="zone_fragment_size"):
        session.run(inputs={"rack": Zone(well_ids=("a", "b", "c"))})
    assert session.run(inputs={"rack": Zone.empty()}).outputs["last"] == Zone(well_ids=("seed",))


def test_empty_loop_bodies_still_consume_steps():
    program = traversal()
    function = program.functions[0]
    loop = replace(function.body[1], body=())
    program = replace(program, functions=(replace(function, body=(function.body[0], loop, function.body[2])),))
    with pytest.raises(ExecutionError, match="step_limit"):
        Interpreter(program, config=ExecutionConfig(max_steps=10)).run(
            inputs={"rack": Zone(well_ids=tuple(map(str, range(50))))}
        )


@pytest.mark.parametrize(
    "change", ["zero", "negative", "bool", "text", "input", "output", "unknown", "type", "body", "extra"]
)
def test_malformed_or_semantically_invalid_traversal_json_is_rejected(change):
    document = to_dict(traversal())
    function = document["functions"][0]
    loop = function["body"][1]
    if change in ("zero", "negative", "bool", "text"):
        loop["fragment_size"] = {"zero": 0, "negative": -1, "bool": True, "text": "2"}[change]
    elif change in ("input", "output"):
        function["variables"][1].update(role=change, initial=None)
    elif change == "unknown":
        loop["target"]["symbol_id"] = "absent"
    elif change == "type":
        loop["value"] = {"kind": "Literal", "node_id": "value", "source": None, "type": "integer", "value": 1}
    elif change == "body":
        loop["value"] = {"kind": "ZoneLiteral", "node_id": "empty", "source": None, "well_ids": []}
        loop["body"][0]["value"]["right"].update(type="text", value="bad even in an empty loop")
    else:
        loop["batch"] = True
    with pytest.raises(IRValidationError):
        from_dict(document)


def test_zone_get_direct_ir_json_and_runtime_bounds():
    program = traversal()
    function = program.functions[0]
    get = ZoneGet(
        node_id="get",
        value=Reference(node_id="get-zone", symbol_id="rack"),
        index=Literal(node_id="index", type=ScalarType.INTEGER, value=1),
    )
    selected = Assignment(node_id="select", target=Reference(node_id="select-target", symbol_id="well"), value=get)
    for index in (-1, 0, 1, 2):
        candidate = replace(
            program,
            functions=(
                replace(
                    function,
                    body=(
                        function.body[0],
                        replace(selected, value=replace(get, index=replace(get.index, value=index))),
                        function.body[2],
                    ),
                ),
            ),
        )
        for restored in (candidate, from_json(to_json(candidate))):
            session = Interpreter(restored)
            if 0 <= index < 2:
                assert session.run(inputs={"rack": Zone(well_ids=("27", "0"))}).outputs["last"] == Zone(
                    well_ids=(("27", "0")[index],)
                )
            else:
                with pytest.raises(ExecutionError, match="index_bounds"):
                    session.run(inputs={"rack": Zone(well_ids=("27", "0"))})
    bad = replace(get, index=Literal(node_id="bool-index", type=ScalarType.BOOLEAN, value=True))
    candidate = replace(program, functions=(replace(function, body=(replace(selected, value=bad),)),))
    with pytest.raises(IRValidationError, match="index_type"):
        to_json(candidate)
