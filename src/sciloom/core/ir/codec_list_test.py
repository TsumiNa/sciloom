"""JSON v3 lists retain typed high-level operations and reject invalid contracts."""

from dataclasses import replace

import pytest

from . import (
    Assignment, Binary, BinaryOp, FunctionIR, If, ListGet, ListLength, ListLiteral,
    ListSet, ListType, Literal, Program, Reference, ScalarType, Variable,
    VariableRole, from_dict, from_json, to_dict, to_json, validate,
)
from ..diagnostics import IRValidationError


def list_program():
    kind = ListType(element_type=ScalarType.REAL)
    initial = ListLiteral(node_id="initial", type=kind, elements=(Literal(node_id="one", type=ScalarType.INTEGER, value=1),))
    state = Variable(node_id="state", owner_id="f", name="state", role=VariableRole.INTERNAL, type=kind, initial=initial)
    output = Variable(node_id="output", owner_id="f", name="output", role=VariableRole.OUTPUT, type=kind)
    body = (
        Assignment(node_id="copy", target=Reference(node_id="out1", symbol_id="output"), value=Reference(node_id="state1", symbol_id="state")),
        ListSet(node_id="update", target=Reference(node_id="out2", symbol_id="output"), index=Literal(node_id="index", type=ScalarType.INTEGER, value=0), value=Literal(node_id="two", type=ScalarType.REAL, value=2.0), op=BinaryOp.MULTIPLY),
    )
    return Program(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Lists", variables=(state, output), body=body),))


def test_v3_roundtrip_decodes_enum_or_list_types_and_optional_enum():
    program = list_program()
    document = to_dict(program)
    assert document["format_version"] == 3
    assert document["functions"][0]["variables"][0]["type"] == {"kind": "ListType", "element_type": "real"}
    assert document["functions"][0]["body"][1]["op"] == "*"
    assert from_json(to_json(program)) == program


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d.update(format_version=2), "format_version"),
    (lambda d: d["functions"][0]["variables"][0]["type"].update(element_type="unknown"), "json_shape"),
    (lambda d: d["functions"][0]["variables"][0]["type"].update(element_type={"kind": "ListType", "element_type": "real"}), "json_shape"),
    (lambda d: d["functions"][0]["variables"][0]["type"].update(units="mL"), "json_shape"),
    (lambda d: d["functions"][0]["variables"][0].update(type="list[real]"), "json_shape"),
    (lambda d: d["functions"][0]["variables"][0]["initial"].pop("type"), "json_shape"),
    (lambda d: d["functions"][0]["body"][1].update(op="append"), "json_shape"),
    (lambda d: d["functions"][0]["body"][1].update(op="and"), "operator_type"),
    (lambda d: d["functions"][0]["body"][1]["index"].update(type="boolean", value=True), "index_type"),
    (lambda d: d["functions"][0]["body"][1]["value"].update(type="boolean", value=True), "operator_type"),
    (lambda d: d["functions"][0]["variables"][0]["initial"]["elements"][0].update(type="boolean", value=True), "list_element_type"),
    (lambda d: d["functions"][0]["variables"][0]["initial"].update(elements=[{"kind": "Reference", "node_id": "dynamic", "symbol_id": "state"}]), "initializer_literal"),
])
def test_invalid_list_documents_fail_strictly(mutate, code):
    document = to_dict(list_program())
    mutate(document)
    with pytest.raises(IRValidationError) as caught:
        from_dict(document)
    assert code in {d.code for d in caught.value.diagnostics}


def test_list_variables_are_invariant_and_do_not_gain_implicit_truthiness():
    program = list_program()
    function = program.functions[0]
    output = replace(function.variables[1], type=ListType(element_type=ScalarType.INTEGER))
    invalid = replace(program, functions=(replace(function, variables=(function.variables[0], output)),))
    assert "type_mismatch" in {d.code for d in validate(invalid)}
    condition = Reference(node_id="condition", symbol_id="state")
    invalid = replace(program, functions=(replace(function, body=(If(node_id="if", condition=condition),)),))
    assert "condition_type" in {d.code for d in validate(invalid)}


def test_list_comparison_is_not_implicitly_python_list_comparison():
    program = list_program()
    function = program.functions[0]
    comparison = Binary(node_id="equal", op=BinaryOp.EQUAL, left=Reference(node_id="left", symbol_id="state"), right=Reference(node_id="right", symbol_id="state"))
    invalid = replace(program, functions=(replace(function, body=(If(node_id="if", condition=comparison),)),))
    assert "operator_type" in {d.code for d in validate(invalid)}


def test_length_and_index_require_list_values():
    program = list_program()
    function = program.functions[0]
    for value in (
        ListLength(node_id="length", value=Literal(node_id="scalar", type=ScalarType.INTEGER, value=1)),
        ListGet(node_id="get", value=Literal(node_id="scalar", type=ScalarType.INTEGER, value=1), index=Literal(node_id="index", type=ScalarType.INTEGER, value=0)),
    ):
        invalid = replace(program, functions=(replace(function, body=(Assignment(node_id="assign", target=Reference(node_id="out", symbol_id="output"), value=value),)),))
        assert "list_type" in {d.code for d in validate(invalid)}


def test_mutable_or_nested_typed_initializers_fail_structure_validation():
    program = list_program()
    variable = program.functions[0].variables[0]
    for initial in (replace(variable.initial, elements=list(variable.initial.elements)), replace(variable.initial, type=ListType(element_type=ListType(element_type=ScalarType.REAL)))):
        bad_variable = replace(variable, initial=initial)
        invalid = replace(program, functions=(replace(program.functions[0], variables=(bad_variable, program.functions[0].variables[1])),))
        assert validate(invalid)[0].code == "ir_shape"
