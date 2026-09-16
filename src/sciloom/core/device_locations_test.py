"""Location requirements retain call context and the actual failing source node."""

from dataclasses import replace

import pytest

from .bindings import DeviceBindings
from .bindings_selection_test import selection
from .device_locations import validate_device_locations
from .diagnostics import IRValidationError, SourceSpan
from .ir import (
    Call,
    DeviceAt,
    DeviceResource,
    FunctionIR,
    If,
    Literal,
    Program,
    ScalarType,
    StopAgitation,
    While,
    ZoneLiteral,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from .ir.device_contracts import AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT
from .specialization import specialize


def program_with(body):
    return Program(
        entry_function_id="f",
        functions=(FunctionIR(node_id="f", name="Selected", body=body),),
        resources=(DeviceResource(node_id="r", logical_id="mixer", device_type_id=AGITATOR_CONTRACT.type_id),),
        device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT),
    )


def scope(body=(), identity="at"):
    return DeviceAt(
        node_id=identity, resource_id="r", location=ZoneLiteral(node_id=identity + ":zone", well_ids=("a",)), body=body
    )


def test_missing_scope_diagnostics_identify_unguarded_commands_across_recursive_calls():
    guarded = StopAgitation(node_id="guarded", resource_id="r")
    bad = StopAgitation(node_id="bad", resource_id="r", source=SourceSpan(path="selected.py", line=15))
    program = program_with((scope((guarded,)), Call(node_id="call", function_id="child")))
    child = FunctionIR(node_id="child", name="Child", body=(bad, Call(node_id="recurse", function_id="f")))
    program = replace(program, functions=(*program.functions, child))
    bindings = DeviceBindings(devices=(selection(),))
    before = to_json(program)
    for candidate in (program, from_json(before), specialize(program, bindings=bindings)):
        errors = validate_device_locations(candidate, bindings)
        assert [(d.code, d.node_id, d.path, d.source) for d in errors] == [
            ("device_selection_required", "bad", "$.functions[1].body[0]", bad.source)
        ]
    assert to_json(program) == before


def test_recursive_calls_cannot_hide_reentry_into_the_same_selection():
    program = program_with((scope((Call(node_id="call", function_id="middle"),)),))
    middle = FunctionIR(node_id="middle", name="Middle", body=(Call(node_id="back", function_id="f"),))
    program = replace(program, functions=(*program.functions, middle))
    errors = validate_device_locations(program, DeviceBindings(devices=(selection(),)))
    assert [(d.code, d.node_id) for d in errors] == [("device_selection_nesting", "call")]


def test_zero_iteration_loops_and_branches_do_not_supply_persistent_scopes():
    stop = StopAgitation(node_id="stop", resource_id="r")
    no = Literal(node_id="no", type=ScalarType.BOOLEAN, value=False)
    bindings = DeviceBindings(devices=(selection(),))
    for unreachable in (
        While(node_id="while", condition=no, body=(stop,)),
        If(node_id="if", condition=no, then_body=(stop,)),
    ):
        assert validate_device_locations(program_with((unreachable,)), bindings) == ()
    after = program_with((scope(), stop))
    assert validate_device_locations(after, bindings)[0].node_id == "stop"
    fixed = DeviceBindings(devices=(selection().candidates[0].binding,))
    assert validate_device_locations(program_with((scope(),)), fixed)[0].code == "device_selection_binding"


@pytest.mark.parametrize("fault", ["resource", "location", "unknown_field"])
def test_location_json_requires_a_real_resource_and_zone_expression(fault):
    document = to_dict(program_with((scope(),)))
    node = document["functions"][0]["body"][0]
    assert node["kind"] == "DeviceAt" and document["format_version"] == 4
    if fault == "resource":
        node["resource_id"] = "missing"
    elif fault == "location":
        node["location"] = {"kind": "Literal", "node_id": "number", "type": "integer", "value": 0}
    else:
        node["restore"] = True
    with pytest.raises(IRValidationError):
        from_dict(document)
