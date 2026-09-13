"""Device state captures values, retains configuration and freezes history."""

import pytest

from sciloom import Agitator, Function, Input, RotationalSpeed, Var, rpm, runtime
from sciloom.core.configuration_test import ChildConfigure, ParentConfigure, Start
from sciloom.core.diagnostics import ExecutionError
from .runtime import Interpreter


class Reconfigure(Function):
    agitator: Agitator
    speed: Var[RotationalSpeed] = 600 * rpm

    @runtime
    def run(self):
        self.agitator.speed = self.speed
        self.speed = 300 * rpm
        self.agitator.start()
        self.agitator.speed = self.speed
        self.agitator.start()
        self.agitator.speed = 0 * rpm
        self.agitator.stop()


def test_capture_reapply_stop_and_historical_snapshots():
    session = Interpreter(Reconfigure().to_ir())
    result = session.run()
    states = [event.state for event in result.events]
    assert states[0].configuration == {"speed": 600 * rpm}
    assert states[0].applied_configuration == {} and not states[0].enabled
    assert states[1].applied_configuration == {"speed": 600 * rpm} and states[1].enabled
    assert states[2].configuration == {"speed": 300 * rpm}
    assert states[2].applied_configuration == states[1].applied_configuration
    assert states[3].applied_configuration == {"speed": 300 * rpm}
    assert states[4].configuration == {"speed": 0 * rpm} and states[4].enabled
    assert states[5].configuration == states[4].configuration
    assert states[5].applied_configuration == states[3].applied_configuration
    assert not states[5].enabled
    session.run()
    assert states[0].configuration == {"speed": 600 * rpm}
    with pytest.raises(TypeError):
        states[0].configuration["speed"] = 0 * rpm


def test_configuration_persists_in_a_session_but_not_a_new_session():
    class Sometimes(Function):
        agitator: Agitator
        configure: Input[bool]

        @runtime
        def run(self):
            if self.configure:
                self.agitator.speed = 0 * rpm
            self.agitator.start()

    session = Interpreter(Sometimes().to_ir())
    first = session.run(inputs={"configure": True})
    second = session.run(inputs={"configure": False})
    assert first.resources == second.resources
    assert second.resources["resource:agitator"].enabled
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(Sometimes().to_ir()).run(inputs={"configure": False})
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(Start().to_ir()).run()


@pytest.mark.parametrize("cls", [ParentConfigure, ChildConfigure])
def test_parent_and_child_share_saved_configuration(cls):
    result = Interpreter(cls().to_ir()).run()
    assert result.resources["resource:agitator"].applied_configuration == {"speed": 600 * rpm}


def test_list_configuration_captures_an_independent_immutable_value():
    from dataclasses import replace

    from sciloom.core.ir import ConfigureProperty, DeviceResource, DeviceTypeContract, PropertyContract, Reference
    from sciloom.core.ir.codec_list_test import list_program
    from sciloom.core.ir.device_contracts import BASE_DEVICE_CONTRACT

    program = list_program()
    function = program.functions[0]
    prop = PropertyContract(semantic_id="test.values/v1", name="values", type=function.variables[1].type)
    contract = DeviceTypeContract(
        type_id="test.list-device/v1", base_type_ids=(BASE_DEVICE_CONTRACT.type_id,), properties=(prop,)
    )
    capture = ConfigureProperty(
        node_id="capture",
        resource_id="device",
        property_id=prop.semantic_id,
        value=Reference(node_id="captured", symbol_id="output"),
    )
    program = replace(
        program,
        device_types=(BASE_DEVICE_CONTRACT, contract),
        resources=(DeviceResource(node_id="device", logical_id="device", device_type_id=contract.type_id),),
        functions=(replace(function, body=(function.body[0], capture, function.body[1])),),
    )
    session = Interpreter(program)
    first = session.run()
    assert first.resources["device"].configuration == {"values": (1.0,)}
    assert first.outputs == {"output": (2.0,)}
    session.run()
    assert first.resources["device"].configuration == {"values": (1.0,)}
