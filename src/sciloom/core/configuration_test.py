"""Configuration proofs must account for branches, zero iterations and calls."""

from dataclasses import replace

import pytest

from sciloom import Agitator, Function, Input, rpm, runtime
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from .compiler import compile_ir
from .devices import DeviceBinding, DeviceBindings
from .configuration import validate_device_usage
from .diagnostics import CompilationError
from .ir import ConfigureProperty, DeviceResource, FunctionIR, Literal, Program, PropertyContract, ScalarType, StartAgitation
from .ir.device_contracts import AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT, AGITATION_SPEED_ID, START_AGITATION_ID, STOP_AGITATION_ID


class Configure(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm


class Start(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.start()


class ParentConfigure(Function):
    agitator: Agitator

    def __init__(self):
        self.child = Start()
        self.child.agitator = self.agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm
        self.child()


class ChildConfigure(Function):
    agitator: Agitator

    def __init__(self):
        self.child = Configure()
        self.child.agitator = self.agitator

    @runtime
    def run(self):
        self.child()
        self.agitator.start()


def target():
    return AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})


@pytest.mark.parametrize("cls", [ParentConfigure, ChildConfigure])
def test_shared_configuration_flows_across_function_boundaries(cls):
    model = cls()
    authored = model.to_ir()
    result = model.compile(target=target())
    assert result.semantic_ir == authored
    assert all(not f.variables for f in authored.functions)


def test_standalone_start_cannot_depend_on_previous_entry_invocations():
    with pytest.raises(CompilationError, match="device_configuration"):
        Start().compile(target=target())


def test_conditional_and_loop_configuration_are_not_definite():
    class Conditional(Function):
        agitator: Agitator
        enabled: Input[bool]

        @runtime
        def run(self):
            if self.enabled:
                self.agitator.speed = 600 * rpm
            self.agitator.start()

    class Loop(Conditional):
        @runtime
        def run(self):
            while self.enabled:
                self.agitator.speed = 600 * rpm
            self.agitator.start()

    for cls in (Conditional, Loop):
        with pytest.raises(CompilationError, match="device_configuration"):
            cls().compile(target=target())


def test_configuration_inside_each_branch_and_iteration_is_sufficient():
    class Complete(Function):
        agitator: Agitator
        enabled: Input[bool]

        @runtime
        def run(self):
            if self.enabled:
                self.agitator.speed = 600 * rpm
            else:
                self.agitator.speed = 0 * rpm
            self.agitator.start()
            while self.enabled:
                self.agitator.speed = 300 * rpm
                self.agitator.start()

    Complete().compile(target=target())


def test_type_inheritance_does_not_imply_supported_operations():
    program = ParentConfigure().to_ir()
    bindings = target().resolve_devices(program)
    unsupported = replace(bindings.devices[0], supported_operations=(STOP_AGITATION_ID,))
    diagnostics = validate_device_usage(program, DeviceBindings(devices=(unsupported,)))
    assert diagnostics[0].code == "device_capability"


def test_every_required_parameter_must_be_configured():
    gain = PropertyContract(semantic_id="test.shaker.gain/v1", name="gain", type=ScalarType.REAL)
    contract = replace(AGITATOR_CONTRACT, type_id="test.shaker/v1", base_type_ids=(AGITATOR_CONTRACT.type_id, BASE_DEVICE_CONTRACT.type_id), properties=(*AGITATOR_CONTRACT.properties, gain), required_configuration=(AGITATION_SPEED_ID, gain.semantic_id))
    binding = DeviceBinding(logical_id="agitator", contract=contract, physical_id="test:1", writable_properties=contract.required_configuration, supported_operations=(START_AGITATION_ID, STOP_AGITATION_ID))
    program = Program(
        entry_function_id="f", device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT, contract),
        resources=(DeviceResource(node_id="device", logical_id="agitator", device_type_id=contract.type_id),),
        functions=(FunctionIR(node_id="f", name="Configure", body=(
            ConfigureProperty(node_id="speed", resource_id="device", property_id=AGITATION_SPEED_ID, value=Literal(node_id="value", type=ScalarType.ROTATIONAL_SPEED, value=10)),
            StartAgitation(node_id="start", resource_id="device"),
        )),),
    )
    assert validate_device_usage(program, DeviceBindings(devices=(binding,)))[0].code == "device_configuration"
    function = program.functions[0]
    extra = ConfigureProperty(node_id="gain", resource_id="device", property_id=gain.semantic_id, value=Literal(node_id="gain_value", type=ScalarType.REAL, value=0.5))
    complete = replace(program, functions=(replace(function, body=(function.body[0], extra, function.body[1])),))
    assert validate_device_usage(complete, DeviceBindings(devices=(binding,))) == ()
    from .interpreter import Interpreter
    from .diagnostics import ExecutionError

    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program).run()
    state = Interpreter(complete).run().resources["device"]
    assert state.configuration == state.applied_configuration == {"speed": 600 * rpm, "gain": 0.5}
