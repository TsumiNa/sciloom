"""The v4 device directory and deferred nodes have a strict, data-only wire form."""

from dataclasses import replace

import pytest

from sciloom.core.bindings import DeviceBinding
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from . import (
    CanWrite,
    CommandArgument,
    CommandContract,
    CommandParameter,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    DeviceResource,
    FunctionIR,
    IsDevice,
    Literal,
    Program,
    PropertyContract,
    ScalarType,
    SupportsOperation,
    ZoneType,
    from_dict,
    from_json,
    to_dict,
    to_json,
    validate,
)
from .device_contracts import AGITATOR_CONTRACT, AGITATOR_TYPE_ID, BASE_DEVICE_CONTRACT, START_AGITATION_ID


def extension_program():
    command = CommandContract(
        semantic_id="test.calibrate/v1",
        name="calibrate",
        parameters=(CommandParameter(name="level", type=ScalarType.REAL),),
    )

    prop = PropertyContract(semantic_id="test.gain/v1", name="gain", type=ScalarType.REAL)
    contract = replace(
        AGITATOR_CONTRACT,
        type_id="test.shaker/v1",
        base_type_ids=(AGITATOR_TYPE_ID, BASE_DEVICE_CONTRACT.type_id),
        properties=(*AGITATOR_CONTRACT.properties, prop),
        operations=(*AGITATOR_CONTRACT.operations, command),
    )
    return Program(
        entry_function_id="f",
        device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT, contract),
        resources=(DeviceResource(node_id="r", logical_id="agitator", device_type_id=contract.type_id),),
        functions=(
            FunctionIR(
                node_id="f",
                name="Check",
                body=(
                    DeviceCommand(
                        node_id="call",
                        resource_id="r",
                        operation_id=command.semantic_id,
                        arguments=(
                            CommandArgument(
                                name="level", value=Literal(node_id="level", type=ScalarType.REAL, value=0.5)
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


@pytest.mark.parametrize("member_kind", ["property", "command"])
def test_device_contracts_reject_zone_types_in_ir_json_and_bindings(member_kind):
    program = extension_program()
    contract = program.device_types[-1]
    document = to_dict(program)
    if member_kind == "property":
        bad_contract = replace(
            contract, properties=(*contract.properties[:-1], replace(contract.properties[-1], type=ZoneType()))
        )
        document["device_types"][-1]["properties"][-1]["type"] = {"kind": "ZoneType"}
    else:
        command = contract.operations[-1]
        bad_command = replace(command, parameters=(replace(command.parameters[0], type=ZoneType()),))
        bad_contract = replace(contract, operations=(*contract.operations[:-1], bad_command))
        document["device_types"][-1]["operations"][-1]["parameters"][0]["type"] = {"kind": "ZoneType"}
    bad_program = replace(program, device_types=(*program.device_types[:-1], bad_contract))
    assert any(d.code == "ir_shape" for d in validate(bad_program))
    with pytest.raises(IRValidationError, match="ir_shape"):
        to_json(bad_program)
    with pytest.raises(IRValidationError, match="json_shape"):
        from_dict(document)
    with pytest.raises(IRValidationError, match="ir_shape"):
        DeviceBinding(
            logical_id="agitator",
            physical_id="physical",
            contract=bad_contract,
            base_contracts=program.device_types[:-1],
            writable_properties=(),
            supported_operations=(),
        )


@pytest.mark.parametrize(
    "predicate",
    [
        CanWrite(node_id="query", resource_id="r", property_id="test.gain/v1"),
        SupportsOperation(node_id="query", resource_id="r", operation_id="test.calibrate/v1"),
        IsDevice(node_id="query", resource_id="r", device_type_id="test.shaker/v1"),
    ],
)
def test_v4_preserves_all_deferred_device_nodes_without_importing_implementations(predicate):
    program = extension_program()
    function = program.functions[0]
    program = replace(
        program,
        functions=(
            replace(function, body=(DeviceIf(node_id="branch", condition=predicate, then_body=function.body),)),
        ),
    )
    assert from_json(to_json(program)) == program
    assert to_dict(program)["format_version"] == 4
    with pytest.raises(ExecutionError, match="unspecialized_device_condition"):
        Interpreter(program)


def test_unknown_native_execution_is_explicit_and_has_source_identity():
    with pytest.raises(ExecutionError, match="unsupported_operation") as caught:
        Interpreter(extension_program()).run()
    assert caught.value.diagnostics[0].node_id == "call"


@pytest.mark.parametrize(
    "mutate,code",
    [
        (lambda d: d.update(format_version=3), "format_version"),
        (lambda d: d["resources"][0].pop("device_type_id"), "json_shape"),
        (lambda d: d["resources"][0].update(device_type_id="missing.type/v1"), "device_contract"),
        (lambda d: d["device_types"][2]["properties"][-1].update(type="integer"), "type_mismatch"),
        (lambda d: d["functions"][0]["body"][0].update(operation_id="missing.command/v1"), "device_command"),
        (lambda d: d["functions"][0]["body"][0]["arguments"][0].update(name="missing"), "device_command"),
        (lambda d: d["device_types"][1]["properties"][0].update(type="real"), "device_contract"),
        (lambda d: d["device_types"][2].update(base_type_ids=["test.shaker/v1"]), "device_contract"),
    ],
)
def test_device_documents_reject_invalid_contracts(mutate, code):
    program = extension_program()
    # Include a float property write so changing its declared type is observable.
    function = program.functions[0]
    write = ConfigureProperty(
        node_id="write",
        resource_id="r",
        property_id="test.gain/v1",
        value=Literal(node_id="gain", type=ScalarType.REAL, value=0.5),
    )
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


def test_extension_commands_require_a_declared_or_guard_narrowed_interface():
    program = extension_program()
    resource = replace(program.resources[0], device_type_id=AGITATOR_TYPE_ID)
    generic = replace(program, resources=(resource,))
    assert "device_command" in {d.code for d in validate(generic)}
    function = generic.functions[0]
    guard = IsDevice(node_id="guard", resource_id="r", device_type_id="test.shaker/v1")
    narrowed = replace(
        generic,
        functions=(replace(function, body=(DeviceIf(node_id="if", condition=guard, then_body=function.body),)),),
    )
    assert from_json(to_json(narrowed)) == narrowed
    wrong_branch = replace(
        narrowed,
        functions=(replace(function, body=(DeviceIf(node_id="if", condition=guard, else_body=function.body),)),),
    )
    assert "device_command" in {d.code for d in validate(wrong_branch)}


@pytest.mark.parametrize(
    "predicate",
    [
        CanWrite(node_id="query", resource_id="r", property_id="test.gain/v1"),
        SupportsOperation(node_id="query", resource_id="r", operation_id="test.calibrate/v1"),
    ],
)
def test_capability_queries_allow_compatible_extensions_but_not_unrelated_families(predicate):
    program = extension_program()
    function = replace(program.functions[0], body=(DeviceIf(node_id="if", condition=predicate),))
    generic = replace(
        program, resources=(replace(program.resources[0], device_type_id=AGITATOR_TYPE_ID),), functions=(function,)
    )
    assert validate(generic) == ()  # A query is not permission to call the member.
    from .device_contracts import DeviceTypeContract

    unrelated = DeviceTypeContract(type_id="test.thermometer/v1", base_type_ids=(BASE_DEVICE_CONTRACT.type_id,))
    invalid = replace(
        generic,
        device_types=(*generic.device_types, unrelated),
        resources=(replace(program.resources[0], device_type_id=unrelated.type_id),),
    )
    codes = {d.code for d in validate(invalid)}
    assert codes & {"device_property", "device_command"}


def test_is_device_rejects_unrelated_and_sibling_types_in_ir_and_json():
    from .device_contracts import DeviceTypeContract

    program = extension_program()
    other = DeviceTypeContract(type_id="test.thermometer/v1", base_type_ids=(BASE_DEVICE_CONTRACT.type_id,))
    sibling = replace(program.device_types[-1], type_id="test.other-shaker/v1")
    for queried in (other, sibling):
        branch = DeviceIf(
            node_id="if", condition=IsDevice(node_id="query", resource_id="r", device_type_id=queried.type_id)
        )
        invalid = replace(
            program,
            device_types=(*program.device_types, queried),
            functions=(replace(program.functions[0], body=(branch,)),),
        )
        assert "device_condition" in {d.code for d in validate(invalid)}
        # Build a shape-valid wire document without bypassing decoder validation.
        document = to_dict(replace(program, device_types=(*program.device_types, queried)))
        document["functions"][0]["body"] = [
            {
                "kind": "DeviceIf",
                "node_id": "if",
                "condition": {
                    "kind": "IsDevice",
                    "node_id": "query",
                    "resource_id": "r",
                    "device_type_id": queried.type_id,
                },
            }
        ]
        with pytest.raises(IRValidationError, match="inheritance chain"):
            from_dict(document)
