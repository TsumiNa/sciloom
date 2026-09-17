"""Direct lifecycle IR rejects unsupported semantics before execution."""

from dataclasses import replace

import pytest

from examples.developer.lifecycle_commands import Reconfigure, RecordingTarget
from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.specialization import specialize
from . import (
    CommandParameter,
    DeviceIf,
    LifecycleCommandContract,
    ScalarType,
    SupportsOperation,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def test_additive_lifecycle_wire_form_and_specialization():
    program = Reconfigure().to_ir()
    document = to_dict(program)
    op = next(op for op in document["device_types"][-1]["operations"] if op["name"] == "apply")
    assert op == {
        "kind": "LifecycleCommandContract",
        "semantic_id": "example.adjustable-agitator.apply/v1",
        "name": "apply",
        "effect": "apply_and_enable",
        "parameters": [],
        "required_configuration": [],
    }
    assert document["format_version"] == 4
    assert from_json(to_json(program)) == program
    function = program.functions[0]
    branch = DeviceIf(
        node_id="branch",
        condition=SupportsOperation(
            node_id="supports", resource_id="resource:agitator", operation_id=op["semantic_id"]
        ),
        then_body=function.body,
    )
    guarded = replace(program, functions=(replace(function, body=(branch,)),))
    target = RecordingTarget()
    bindings = target.resolve_devices(guarded)
    assert specialize(guarded, bindings=bindings).functions[0].body == function.body
    unsupported = replace(bindings.devices[0], supported_operations=())
    assert specialize(guarded, bindings=DeviceBindings(devices=(unsupported,))).functions[0].body == ()


@pytest.mark.parametrize("change", ["parameter", "missing", "duplicate", "effect", "ordinary"])
def test_malformed_new_wire_contracts_and_ordinary_shape_are_rejected(change):
    document = to_dict(Reconfigure().to_ir())
    operations = document["device_types"][-1]["operations"]
    op = next(op for op in operations if op["name"] == "apply")
    if change == "parameter":
        op["parameters"] = [{"kind": "CommandParameter", "name": "unused", "type": "real"}]
    elif change == "missing":
        op["required_configuration"] = ["test.missing/v1"]
    elif change == "duplicate":
        op["required_configuration"] = ["example.adjustable-agitator.gain/v1"] * 2
    elif change == "effect":
        op["effect"] = "guess_from_name"
    else:
        next(op for op in operations if op["name"] == "start")["effect"] = "apply_and_enable"
    with pytest.raises(IRValidationError):
        from_dict(document)


def test_direct_ir_cannot_carry_ignored_lifecycle_arguments():
    program = Reconfigure().to_ir()
    contract = program.device_types[-1]
    invalid = replace(
        contract,
        operations=tuple(
            replace(op, parameters=(CommandParameter(name="ignored", type=ScalarType.REAL),))
            if isinstance(op, LifecycleCommandContract)
            else op
            for op in contract.operations
        ),
    )
    with pytest.raises(IRValidationError, match="parameterless"):
        to_json(replace(program, device_types=(*program.device_types[:-1], invalid)))
