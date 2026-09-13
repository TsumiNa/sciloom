"""Agitation intent is executable and inspectable without a device backend."""

from dataclasses import replace

import pytest

from sciloom import Agitator, Function, Input, RotationalSpeed, Var, rpm, rps, runtime
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.ir import (
    ConfigureProperty,
    DeviceResource,
    FunctionIR,
    If,
    Program,
    Reference,
    ScalarType,
    StartAgitation,
    StopAgitation,
    Variable,
    VariableRole,
    from_json,
    to_json,
    validate,
)
from sciloom.core.ir.device_contracts import (
    AGITATION_SPEED_ID,
    AGITATOR_CONTRACT,
    AGITATOR_TYPE_ID,
    BASE_DEVICE_CONTRACT,
)
from .runtime import Interpreter


class ConfigureAgitation(Function):
    speed: Input[RotationalSpeed]
    enabled: Input[bool]

    agitator: Agitator

    @runtime
    def run(self):
        if self.enabled:
            self.agitator.speed = self.speed
            self.agitator.start()
        else:
            self.agitator.stop()


def direct_agitation():
    return Program(
        entry_function_id="configure",
        device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT),
        resources=(DeviceResource(node_id="mixer", logical_id="reaction_mixer", device_type_id=AGITATOR_TYPE_ID),),
        functions=(
            FunctionIR(
                node_id="configure",
                name="ConfigureAgitation",
                variables=(
                    Variable(
                        node_id="speed",
                        owner_id="configure",
                        name="speed",
                        type=ScalarType.ROTATIONAL_SPEED,
                        role=VariableRole.INPUT,
                    ),
                    Variable(
                        node_id="enabled",
                        owner_id="configure",
                        name="enabled",
                        type=ScalarType.BOOLEAN,
                        role=VariableRole.INPUT,
                    ),
                ),
                body=(
                    If(
                        node_id="if",
                        condition=Reference(node_id="flag", symbol_id="enabled"),
                        then_body=(
                            ConfigureProperty(
                                node_id="set",
                                resource_id="mixer",
                                property_id=AGITATION_SPEED_ID,
                                value=Reference(node_id="rate", symbol_id="speed"),
                            ),
                            StartAgitation(node_id="start", resource_id="mixer"),
                        ),
                        else_body=(StopAgitation(node_id="stop", resource_id="mixer"),),
                    ),
                ),
            ),
        ),
    )


def test_python_direct_and_json_agitation_have_the_same_intent():
    python = ConfigureAgitation().to_ir()
    programs = (python, direct_agitation(), from_json(to_json(direct_agitation())))
    for program in programs:
        assert len(program.resources) == 1
        resource_id = program.resources[0].node_id
        assert isinstance(program.functions[0].body[0].then_body[0], ConfigureProperty)
        assert "Chemspeed" not in to_json(program)
        session = Interpreter(program)
        started = session.run(inputs={"speed": 600 * rpm, "enabled": True})
        assert started.resources[resource_id].enabled
        assert started.resources[resource_id].applied_configuration["speed"] == 10 * rps
        stopped = session.run(inputs={"speed": 1200 * rpm, "enabled": False})
        assert not stopped.resources[resource_id].enabled
        assert stopped.resources[resource_id].applied_configuration["speed"] == 600 * rpm
        assert [(e.state.enabled, e.state.applied_configuration.get("speed")) for e in started.events] == [
            (False, None),
            (True, 600 * rpm),
        ]
        assert [(e.state.enabled, e.state.applied_configuration.get("speed")) for e in stopped.events] == [
            (False, 600 * rpm)
        ]
        assert started.resources[resource_id].enabled  # detached resource snapshot


def test_unit_literals_and_host_quantities_lower_without_executing_methods():
    class LiteralSpeed(Function):
        agitator: Agitator

        def __init__(self):
            self.speed = 600 * rpm

        @runtime
        def run(self):
            self.agitator.speed = self.speed
            self.agitator.start()
            self.agitator.speed = 1200 * rpm
            self.agitator.start()
            self.agitator.stop()

    result = Interpreter(LiteralSpeed().to_ir()).run()
    assert [(e.state.enabled, e.state.applied_configuration.get("speed")) for e in result.events] == [
        (False, None),
        (True, 10 * rps),
        (True, 10 * rps),
        (True, 20 * rps),
        (False, 20 * rps),
    ]
    with pytest.raises(TypeError, match="compiled"):
        LiteralSpeed().agitator.start()


def test_physical_input_requires_a_quantity():
    with pytest.raises(ExecutionError, match="runtime_type"):
        Interpreter(direct_agitation()).run(inputs={"speed": 600, "enabled": True})


def test_unknown_resources_fail_ir_validation():
    program = replace(direct_agitation(), resources=())
    assert "unknown_resource" in {d.code for d in validate(program)}
    with pytest.raises(IRValidationError):
        Interpreter(program)


def test_bare_speed_in_source_is_not_implicitly_rpm():
    class Bare(Function):
        agitator: Agitator

        @runtime
        def run(self):
            self.agitator.speed = 600
            self.agitator.start()

    with pytest.raises(IRValidationError, match="type_mismatch"):
        Bare().to_ir()


def test_rotational_speed_can_pass_through_function_calls_and_outputs():
    from sciloom import Output

    class Echo(Function):
        speed: Input[RotationalSpeed]
        result: Output[RotationalSpeed]

        @runtime
        def run(self):
            self.result = self.speed

    result = Interpreter(Echo().to_ir()).run(inputs={"speed": 600 * rpm})
    assert result.outputs == {"result": 10 * rps}

    class Caller(Function):
        result: Output[RotationalSpeed]

        def __init__(self):
            self.echo = Echo()

        @runtime
        def run(self):
            self.result = self.echo(speed=600 * rpm)

    assert Interpreter(Caller().to_ir()).run().outputs == {"result": 10 * rps}


def test_duplicate_logical_resource_identity_is_rejected():
    program = direct_agitation()
    duplicate = DeviceResource(node_id="other", logical_id="reaction_mixer", device_type_id=AGITATOR_TYPE_ID)
    errors = validate(replace(program, resources=(*program.resources, duplicate)))
    assert "resource_identity" in {d.code for d in errors}


def test_operations_compose_in_loops_and_functions_with_distinct_resources():

    class Sequence(Function):
        index: Var[int] = 0

        def __init__(self):
            self.first = ConfigureAgitation()
            self.second = ConfigureAgitation()

        @runtime
        def run(self):
            while self.index < 2:
                self.first(speed=600 * rpm, enabled=True)
                self.index += 1
            self.second(speed=10 * rps, enabled=False)

    result = Interpreter(Sequence().to_ir()).run()
    assert [(e.resource_id, e.state.enabled) for e in result.events] == [
        ("resource:first.agitator", False),
        ("resource:first.agitator", True),
        ("resource:first.agitator", True),
        ("resource:first.agitator", True),
        ("resource:second.agitator", False),
    ]
    assert result.resources["resource:second.agitator"].applied_configuration == {}


def test_domain_ir_executes_without_source_or_vendor_modules():
    import subprocess
    import sys

    script = """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.dsl", "sciloom.contrib")):
            raise ImportError("source and vendor modules are forbidden")
sys.meta_path.insert(0, Block())
from sciloom.core.ir import from_json
from sciloom.core.interpreter import Interpreter
from sciloom.units import rpm
result = Interpreter(from_json(sys.stdin.read())).run(inputs={"speed": 600 * rpm, "enabled": True})
assert result.resources["mixer"].applied_configuration["speed"] == 600 * rpm
assert len(result.events) == 2
"""
    subprocess.run([sys.executable, "-c", script], input=to_json(direct_agitation()), text=True, check=True)
