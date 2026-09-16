"""Well-property structure is typed and round-trippable without Python declarations."""

from dataclasses import replace

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import IRValidationError, SourceSpan
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, WellProperties
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom.core.specialization import specialize
from . import (
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
    ZoneType,
    from_dict,
    from_json,
    to_dict,
    to_json,
    validate,
)


def property_program():
    spec = WellPropertySpec(name="sample_ID", type=ScalarType.TEXT)
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Label",
                variables=(
                    Variable(node_id="zone", owner_id="f", name="zone", role=VariableRole.INPUT, type=ZoneType()),
                    Variable(
                        node_id="result", owner_id="f", name="result", role=VariableRole.OUTPUT, type=ScalarType.TEXT
                    ),
                ),
                body=(
                    WriteWellProperty(
                        node_id="write",
                        property=spec,
                        zone=Reference(node_id="write-zone", symbol_id="zone"),
                        value=Literal(node_id="value", type=ScalarType.TEXT, value="A"),
                    ),
                    ReadWellProperty(
                        node_id="read",
                        source=SourceSpan(path="metadata.py", line=4),
                        property=spec,
                        zone=Reference(node_id="read-zone", symbol_id="zone"),
                        target=Reference(node_id="out", symbol_id="result"),
                    ),
                ),
            ),
        ),
    )


def test_direct_ir_json_and_specialization_preserve_semantics():
    program = property_program()
    selected = specialize(program, bindings=DeviceBindings())
    assert selected == program == from_json(to_json(program))
    for candidate in (program, from_json(to_json(program)), selected):
        env = ReferenceEnvironment(
            locations=LocationDirectory(wells=(Well(identity="a", name="A"),)), properties=WellProperties()
        )
        result = Interpreter(candidate, environment=env).run(inputs={"zone": Zone(well_ids=("a",))})
        assert result.outputs == {"result": "A"}
        assert result.events[1].source == program.functions[0].body[1].source
        assert result.events[1].used_default is False
    data = to_dict(program)
    assert data["functions"][0]["body"][0]["property"]["kind"] == "WellPropertySpec"


@pytest.mark.parametrize(
    "change,code",
    [
        ({"property": WellPropertySpec(name="", type=ScalarType.TEXT)}, "well_property_name"),
        ({"property": WellPropertySpec(name="x", type=ScalarType.INTEGER)}, "well_property_type"),
        ({"zone": Literal(node_id="bad", type=ScalarType.TEXT, value="rack")}, "zone_type"),
        ({"default": Literal(node_id="bad", type=ScalarType.INTEGER, value=0)}, "well_property_type"),
        ({"target": Reference(node_id="bad", symbol_id="zone")}, "well_property_type"),
        ({"target": Reference(node_id="bad", symbol_id="other-function-field")}, "unknown_symbol"),
    ],
)
def test_property_types_and_owned_output_binding(change, code):
    program = property_program()
    function = program.functions[0]
    changed = replace(function.body[1], **change)
    program = replace(program, functions=(replace(function, body=(function.body[0], changed)),))
    assert code in [error.code for error in validate(program)]


def test_unknown_wire_fields_and_types_are_rejected():
    document = to_dict(property_program())
    document["functions"][0]["body"][0]["property"]["getter"] = "python.import"
    with pytest.raises(IRValidationError):
        from_dict(document)
