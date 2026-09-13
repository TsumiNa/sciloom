"""Portable device programs compile to AutoSuite XML with foreign branches removed."""

from examples.developer.demo_contribution import DemoAgitator
from sciloom import Agitator, Function, Input, RotationalSpeed, comptime, rpm, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json, validate
from sciloom.core.specialization import specialize
from . import AutoSuiteIndividualShaker, AutoSuiteTarget


class PortableAgitation(Function):
    """Apply a demo-only adjustment before the common agitation sequence."""

    agitator: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if comptime.is_device(self.agitator, DemoAgitator):
            self.agitator.gain = 0.5
        self.agitator.speed = self.speed
        self.agitator.start()


def autosuite():
    return AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})


def test_portable_program_compiles_to_asfp_without_the_demo_branch():
    program = PortableAgitation().to_ir()
    original = to_json(program)
    result = compile_ir(from_json(original), target=autosuite())
    assert result.artifact.suffix == ".asfp"
    assert result.artifact.content.startswith(b"<?xml")
    assert result.semantic_ir == program
    assert validate(result.specialized_ir) == ()
    assert specialize(program, bindings=autosuite().resolve_devices(program)) == result.specialized_ir
    assert compile_ir(program, target=autosuite()).artifact == result.artifact
    snapshot = Interpreter(result.specialized_ir).run(inputs={"speed": 600 * rpm})
    assert set(snapshot.resources["resource:agitator"].configuration) == {"speed"}
    assert snapshot.resources["resource:agitator"].enabled
    assert to_json(program) == original
