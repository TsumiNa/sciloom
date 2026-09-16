"""Zone records extend v4 while keeping location validation separate from encoding."""

import json
from dataclasses import replace

import pytest

from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.locations import Zone
from . import (
    Assignment,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    WellName,
    ZoneCombine,
    ZoneFind,
    ZoneLength,
    ZoneLiteral,
    ZoneType,
    from_json,
    to_json,
)


def program_with(value, kind=ZoneType()):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Zones",
                variables=(Variable(node_id="out", owner_id="f", name="result", role=VariableRole.OUTPUT, type=kind),),
                body=(Assignment(node_id="assign", target=Reference(node_id="write", symbol_id="out"), value=value),),
            ),
        ),
    )


def test_zone_literals_use_stable_records_and_round_trip():
    program = program_with(ZoneLiteral(node_id="zone", well_ids=("opaque:27", "opaque:0")))
    document = to_json(program)
    assert json.loads(document)["format_version"] == 4
    assert '"kind": "ZoneType"' in document and '"kind": "ZoneLiteral"' in document
    assert from_json(document) == program
    for candidate in (program, from_json(document)):
        assert Interpreter(candidate).run().outputs["result"] == Zone(well_ids=("opaque:27", "opaque:0"))


@pytest.mark.parametrize("identities", [("duplicate", "duplicate"), ("",), ("   ",)])
def test_invalid_zone_identities_are_semantic_errors(identities):
    with pytest.raises(IRValidationError, match="zone_literal"):
        to_json(program_with(ZoneLiteral(node_id="bad", well_ids=identities)))


@pytest.mark.parametrize(
    "value,kind,code",
    [
        (
            ZoneFind(node_id="find", name=Literal(node_id="name", type=ScalarType.INTEGER, value=0)),
            ZoneType(),
            "text_type",
        ),
        (
            ZoneCombine(
                node_id="combine",
                left=ZoneLiteral(node_id="left"),
                right=Literal(node_id="right", type=ScalarType.INTEGER, value=0),
            ),
            ZoneType(),
            "zone_type",
        ),
        (
            ZoneLength(node_id="length", value=Literal(node_id="value", type=ScalarType.TEXT, value="rack")),
            ScalarType.INTEGER,
            "zone_type",
        ),
        (WellName(node_id="name", value=ZoneLiteral(node_id="empty")), ScalarType.TEXT, "zone_cardinality"),
    ],
)
def test_zone_expression_type_rules(value, kind, code):
    with pytest.raises(IRValidationError, match=code):
        to_json(program_with(value, kind))


@pytest.mark.parametrize("bad_ids", [[27], [True], "opaque:27", [None]])
def test_malformed_json_ids_fail_structural_validation(bad_ids):
    document = json.loads(to_json(program_with(ZoneLiteral(node_id="zone"))))
    document["functions"][0]["body"][0]["value"]["well_ids"] = bad_ids
    with pytest.raises(IRValidationError):
        from_json(json.dumps(document))


def test_zone_type_rejects_unknown_fields_and_list_elements():
    document = json.loads(to_json(program_with(ZoneLiteral(node_id="zone"))))
    value_type = document["functions"][0]["variables"][0]["type"]
    value_type["future"] = True
    with pytest.raises(IRValidationError):
        from_json(json.dumps(document))
    value_type.clear()
    value_type.update(kind="ListType", element_type={"kind": "ZoneType"})
    with pytest.raises(IRValidationError):
        from_json(json.dumps(document))


def test_empty_zone_initializer_and_nonempty_output_do_not_alias():
    program = program_with(ZoneLiteral(node_id="selection", well_ids=("well:0",)))
    function = program.functions[0]
    state = Variable(
        node_id="state",
        owner_id="f",
        name="state",
        role=VariableRole.INTERNAL,
        type=ZoneType(),
        initial=ZoneLiteral(node_id="initial"),
    )
    program = replace(program, functions=(replace(function, variables=(*function.variables, state)),))
    assert from_json(to_json(program)) == program
    result = Interpreter(program).run()
    assert result.outputs["result"] == Zone(well_ids=("well:0",))
