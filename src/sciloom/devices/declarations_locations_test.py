"""Command Zone types must not widen configuration-property or list boundaries."""

from dataclasses import replace

import pytest

from examples.developer.location_command_ir import InspectLocations, LocatedAgitator, RecordingTarget
from sciloom import Agitator, FlowRate, Function, Input, Length, Zone, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import (
    DeviceCommand,
    ListType,
    ScalarType,
    ZoneLiteral,
    ZoneType,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from sciloom.core.ir.device_contracts import AGITATOR_CONTRACT
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from .declarations import device_contract, operation


def test_source_json_and_specialization_preserve_parameter_order_and_identity():
    program = InspectLocations().to_ir()
    assert device_contract(Agitator) == AGITATOR_CONTRACT
    command = program.functions[0].body[0]
    assert isinstance(command, DeviceCommand)
    assert [a.name for a in command.arguments] == ["source", "destination", "flow"]
    assert [a.value.symbol_id for a in command.arguments[:2]] == ["fn:0:var:source", "fn:0:var:destination"]
    contract = device_contract(LocatedAgitator)
    inspect = next(op for op in contract.operations if op.name == "inspect")
    assert [p.type for p in inspect.parameters] == [ZoneType(), ZoneType(), ScalarType.FLOW_RATE]
    for candidate in (program, from_json(to_json(program))):
        result = compile_ir(candidate, target=RecordingTarget())
        assert result.specialized_ir.functions[0].body[0] == command
        env = ReferenceEnvironment()
        with pytest.raises(ExecutionError, match="unsupported_operation"):
            Interpreter(candidate, environment=env).run(inputs={"source": Zone.empty(), "destination": Zone.empty()})
        assert env.events == ()
        assert "unsupported_transfer_quantity" in {d.code for d in AutoSuiteTarget().validate(candidate)}


def test_native_unknown_zone_command_is_rejected_without_quantity_guard():
    program = InspectLocations().to_ir()
    document = to_dict(program)
    contract = document["device_types"][-1]
    operation = next(op for op in contract["operations"] if op["name"] == "inspect")
    operation["parameters"][-1]["type"] = "real"
    document["functions"][0]["body"][0]["arguments"][-1]["value"]["type"] = "real"
    candidate = from_dict(document)
    target = AutoSuiteTarget(devices={"device": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})
    with pytest.raises(CompilationError, match="unsupported_operation"):
        target.emit(candidate)


def test_direct_zone_literal_command_keeps_opaque_ordered_wells():
    program = InspectLocations().to_ir()
    function = program.functions[0]
    command = function.body[0]
    command = replace(
        command,
        arguments=(
            replace(command.arguments[0], value=ZoneLiteral(node_id="s", well_ids=("well:b", "well:a"))),
            replace(command.arguments[1], value=ZoneLiteral(node_id="d", well_ids=("well:c",))),
            command.arguments[2],
        ),
    )
    direct = replace(program, functions=(replace(function, body=(command,)),))
    restored = from_json(to_json(direct))
    assert restored.functions[0].body[0].arguments[0].value.well_ids == ("well:b", "well:a")
    assert restored == direct


@pytest.mark.parametrize("annotation", [Zone, list[Zone], dict[str, int], object])
def test_properties_do_not_accept_zone_or_arbitrary_objects(annotation):
    class Invalid(Agitator):
        device_type_id = "example.invalid-property/v1"

        @property
        def extra(self) -> annotation: ...

        @extra.setter
        @operation(id="example.invalid-property.extra/v1")
        def extra(self, value: annotation) -> None: ...

    with pytest.raises(IRValidationError, match="device_contract"):
        device_contract(Invalid)


@pytest.mark.parametrize("annotation", [list[Zone], dict[str, int], object])
def test_commands_still_reject_unsupported_parameter_types(annotation):
    class Invalid(Agitator):
        device_type_id = "example.invalid-command/v1"

        @operation(id="example.invalid-command.extra/v1")
        def extra(self, value: annotation) -> None: ...

    with pytest.raises(IRValidationError, match="device_contract"):
        device_contract(Invalid)


@pytest.mark.parametrize("kind,scalar", [(FlowRate, ScalarType.FLOW_RATE), (Length, ScalarType.LENGTH)])
@pytest.mark.parametrize("array", [False, True])
def test_new_quantities_have_typed_property_and_command_declarations(kind, scalar, array):
    annotation = list[kind] if array else kind

    class Contributed(Agitator):
        device_type_id = "example.quantity-property/v1"

        @property
        def extra(self) -> annotation: ...

        @extra.setter
        @operation(id="example.quantity-property.extra/v1")
        def extra(self, value: annotation) -> None: ...

        @operation(id="example.quantity-property.inspect/v1")
        def inspect(self, value: annotation) -> None: ...

    contract = device_contract(Contributed)
    expected = ListType(element_type=scalar) if array else scalar
    assert next(p for p in contract.properties if p.name == "extra").type == expected
    assert next(op for op in contract.operations if op.name == "inspect").parameters[0].type == expected


def test_wire_property_zone_and_zone_list_reject_without_string_coercion():
    document = to_dict(InspectLocations().to_ir())
    contract = document["device_types"][-1]
    contract["properties"][0]["type"] = {"kind": "ZoneType"}
    with pytest.raises(IRValidationError, match="json_shape"):
        from_dict(document)
    document = to_dict(InspectLocations().to_ir())
    inspect = next(op for op in document["device_types"][-1]["operations"] if op["name"] == "inspect")
    inspect["parameters"][0]["type"] = {"kind": "ListType", "element_type": {"kind": "ZoneType"}}
    with pytest.raises(IRValidationError, match="json_shape"):
        from_dict(document)


def test_source_command_wrong_location_type_rejects():
    class Wrong(Function):
        device: LocatedAgitator
        source: Input[str]
        destination: Input[Zone]
        flow: Input[FlowRate]

        @runtime
        def run(self):
            self.device.inspect(self.source, self.destination, self.flow)

    with pytest.raises(IRValidationError, match="type_mismatch"):
        Wrong().to_ir()
