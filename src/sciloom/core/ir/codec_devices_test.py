"""The v4 device directory and deferred nodes have a strict, data-only wire form."""

from dataclasses import replace

import pytest

from . import CanWrite, CommandArgument, CommandContract, CommandParameter, ConfigureProperty, DeviceCommand, DeviceIf, DeviceResource, FunctionIR, IsDevice, Literal, Program, PropertyContract, ScalarType, SupportsOperation, from_dict, from_json, to_dict, to_json, validate
from .device_contracts import AGITATOR_CONTRACT, AGITATOR_TYPE_ID, AGITATION_SPEED_ID, BASE_DEVICE_CONTRACT, START_AGITATION_ID
from ..diagnostics import ExecutionError, IRValidationError
from ..interpreter import Interpreter


def extension_program():
    command = CommandContract(semantic_id="test.calibrate/v1", name="calibrate", parameters=(CommandParameter(name="level", type=ScalarType.REAL),))
    prop = PropertyContract(semantic_id="test.gain/v1", name="gain", type=ScalarType.REAL)
    contract = replace(AGITATOR_CONTRACT, type_id="test.shaker/v1", base_type_ids=(AGITATOR_TYPE_ID, BASE_DEVICE_CONTRACT.type_id), properties=(*AGITATOR_CONTRACT.properties, prop), operations=(*AGITATOR_CONTRACT.operations, command))
    return Program(
        entry_function_id="f", device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT, contract),
        resources=(DeviceResource(node_id="r", logical_id="agitator", device_type_id=AGITATOR_TYPE_ID),),
        functions=(FunctionIR(node_id="f", name="Check", body=(DeviceCommand(
            node_id="call", resource_id="r", operation_id=command.semantic_id,
            arguments=(CommandArgument(name="level", value=Literal(node_id="level", type=ScalarType.REAL, value=0.5)),),
        ),)),),
    )


@pytest.mark.parametrize("predicate", [
    CanWrite(node_id="query", resource_id="r", property_id="test.gain/v1"),
    SupportsOperation(node_id="query", resource_id="r", operation_id="test.calibrate/v1"),
    IsDevice(node_id="query", resource_id="r", device_type_id="test.shaker/v1"),
])
def test_v4_preserves_all_deferred_device_nodes_without_importing_implementations(predicate):
    program = extension_program()
    function = program.functions[0]
    program = replace(program, functions=(replace(function, body=(DeviceIf(node_id="branch", condition=predicate, then_body=function.body),)),))
    assert from_json(to_json(program)) == program
    assert to_dict(program)["format_version"] == 4
    with pytest.raises(ExecutionError, match="unspecialized_device_condition"):
        Interpreter(program)


def test_unknown_native_execution_is_explicit_and_has_source_identity():
    with pytest.raises(ExecutionError, match="unsupported_operation") as caught:
        Interpreter(extension_program()).run()
    assert caught.value.diagnostics[0].node_id == "call"


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d.update(format_version=3), "format_version"),
    (lambda d: d["resources"][0].pop("device_type_id"), "json_shape"),
    (lambda d: d["resources"][0].update(device_type_id="missing.type/v1"), "device_contract"),
    (lambda d: d["device_types"][2]["properties"][-1].update(type="integer"), "type_mismatch"),
    (lambda d: d["functions"][0]["body"][0].update(operation_id="missing.command/v1"), "device_command"),
    (lambda d: d["functions"][0]["body"][0]["arguments"][0].update(name="missing"), "device_command"),
    (lambda d: d["device_types"][1]["properties"][0].update(type="real"), "device_contract"),
    (lambda d: d["device_types"][2].update(base_type_ids=["test.shaker/v1"]), "device_contract"),
])
def test_device_documents_reject_invalid_contracts(mutate, code):
    program = extension_program()
    # Include a float property write so changing its declared type is observable.
    function = program.functions[0]
    write = ConfigureProperty(node_id="write", resource_id="r", property_id="test.gain/v1", value=Literal(node_id="gain", type=ScalarType.REAL, value=0.5))
    document = to_dict(replace(program, functions=(replace(function, body=(*function.body, write)),)))
    mutate(document)
    with pytest.raises(IRValidationError) as caught:
        from_dict(document)
    assert code in {d.code for d in caught.value.diagnostics}


def test_generic_command_cannot_bypass_builtin_lifecycle_checks():
    program = extension_program()
    function = program.functions[0]
    call = DeviceCommand(node_id="start", resource_id="r", operation_id=START_AGITATION_ID)
    invalid = replace(program, functions=(replace(function, body=(call,)),))
    assert "device_command" in {d.code for d in validate(invalid)}
