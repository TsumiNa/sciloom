"""All source branches are typed before target-dependent branch selection."""

from dataclasses import replace
import subprocess
import sys

import pytest

from examples.developer.demo_contribution import DemoAgitator, DemoTarget
from examples.developer.portable_agitation import PortableAgitation
from sciloom import Agitator, Function, Var, comptime, rpm, runtime
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from sciloom.core.compiler import compile_ir
from sciloom.core.devices import DeviceBindings
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import DeviceCommand, DeviceIf, from_json, to_json, validate
from sciloom.core.specialization import specialize


def autosuite():
    return AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})


def demo():
    return DemoTarget(devices={"agitator": DemoAgitator()})


def test_portable_json_rebinding_is_pure_and_retains_source_identity():
    program = PortableAgitation().to_ir()
    original = to_json(program)
    with pytest.raises(ExecutionError, match="unspecialized"):
        Interpreter(program)
    for target, expected in ((autosuite(), {"speed"}), (demo(), {"speed", "gain"})):
        result = compile_ir(from_json(original), target=target)
        selected = result.specialized_ir
        assert validate(selected) == ()
        assert result.semantic_ir == program
        assert specialize(program, bindings=target.resolve_devices(program)) == selected
        assert specialize(selected, bindings=target.resolve_devices(selected)) == selected
        assert compile_ir(program, target=target).artifact == result.artifact
        snapshot = Interpreter(selected).run(inputs={"speed": 600 * rpm})
        assert set(snapshot.resources["resource:agitator"].configuration) == expected
        assert snapshot.resources["resource:agitator"].enabled
        assert selected.functions[0].body[-1] == program.functions[0].body[-1]
    assert to_json(program) == original


def test_nested_queries_and_native_command_capabilities():
    class Conditional(Function):
        agitator: Agitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                if comptime.can_write(self.agitator, "gain"):
                    self.agitator.gain = 0.5
                if comptime.supports(self.agitator, DemoAgitator.calibrate):
                    self.agitator.calibrate()
            elif comptime.supports(self.agitator, Agitator.stop):
                self.agitator.stop()

    program = Conditional().to_ir()
    selected = compile_ir(program, target=demo()).specialized_ir
    assert isinstance(selected.functions[0].body[-1], DeviceCommand)
    assert not any(isinstance(s, DeviceIf) for s in selected.functions[0].body)
    Conditional().compile(target=autosuite())

    class NoCalibration(DemoTarget):
        def resolve_devices(self, program):
            bindings = super().resolve_devices(program)
            binding = replace(bindings.devices[0], supported_operations=())
            return DeviceBindings(devices=(binding,))

    selected = Conditional().compile(target=NoCalibration(devices={"agitator": DemoAgitator()})).specialized_ir
    assert len(selected.functions[0].body) == 1


def test_can_write_resolves_declared_compatible_extensions_without_narrowing():
    class Query(Function):
        agitator: Agitator
        result: Var[bool] = False

        @runtime
        def run(self):
            if comptime.can_write(self.agitator, "gain"):
                self.result = True

    for target in (autosuite(), demo()):
        Query().compile(target=target)

    class Invalid(Query):
        @runtime
        def run(self):
            if comptime.can_write(self.agitator, "gain"):
                self.agitator.gain = 0.5

    with pytest.raises(IRValidationError, match="device_property"):
        Invalid().to_ir()


def test_unselected_branches_still_require_valid_source_and_types():
    class Invalid(Function):
        agitator: Agitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                self.agitator.gain = True

    class WrongElse(Invalid):
        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                pass
            else:
                self.agitator.gain = 0.5

    class AfterGuard(Invalid):
        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                pass
            self.agitator.gain = 0.5

    for cls in (Invalid, WrongElse, AfterGuard):
        with pytest.raises(IRValidationError):
            cls().compile(target=autosuite())


def test_queries_are_restricted_markers():
    class Unknown(Function):
        agitator: Agitator

        @runtime
        def run(self):
            if comptime.can_write(self.agitator, "unknown"):
                pass

    class Dynamic(Unknown):
        name = "speed"

        @runtime
        def run(self):
            if comptime.can_write(self.agitator, self.name):
                pass

    class Getter(Unknown):
        @runtime
        def run(self):
            if comptime.supports(self.agitator, Agitator.speed):
                pass

    class Loop(Unknown):
        @runtime
        def run(self):
            while comptime.is_device(self.agitator, DemoAgitator):
                pass

    class Combined(Unknown):
        @runtime
        def run(self):
            if comptime.can_write(self.agitator, "speed") and comptime.supports(self.agitator, Agitator.start):
                pass

    class Assigned(Unknown):
        result: Var[bool] = False

        @runtime
        def run(self):
            self.result = comptime.can_write(self.agitator, "speed")

    for cls in (Unknown, Dynamic, Getter, Loop, Combined, Assigned):
        with pytest.raises(IRValidationError):
            cls().to_ir()
    for query, arg in ((comptime.can_write, "speed"), (comptime.supports, Agitator.start), (comptime.is_device, DemoAgitator)):
        with pytest.raises(TypeError, match="if/elif"):
            query(DemoAgitator(), arg)


def test_querying_an_ancestor_does_not_widen_a_known_subtype():
    class Specific(Function):
        agitator: DemoAgitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, Agitator):
                self.agitator.gain = 0.5

    Specific().compile(target=demo())


def test_missing_binding_and_configuration_are_not_false_queries():
    program = PortableAgitation().to_ir()
    with pytest.raises(CompilationError, match="missing_resource_binding"):
        specialize(program, bindings=DeviceBindings())

    class MissingGain(Function):
        agitator: Agitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                self.agitator.speed = 600 * rpm
                self.agitator.start()

    MissingGain().compile(target=autosuite())
    with pytest.raises(CompilationError, match="device_configuration"):
        MissingGain().compile(target=demo())


def test_selected_child_configuration_flows_to_parent_start():
    class Child(Function):
        agitator: Agitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                self.agitator.gain = 0.5

    class Parent(Function):
        agitator: Agitator

        def __init__(self):
            self.child = Child()
            self.child.agitator = self.agitator

        @runtime
        def run(self):
            if comptime.is_device(self.agitator, DemoAgitator):
                self.child()
            self.agitator.speed = 600 * rpm
            self.agitator.start()

    for target, count in ((autosuite(), 1), (demo(), 2)):
        result = Parent().compile(target=target)
        assert len(result.specialized_ir.functions) == count
        assert Interpreter(result.specialized_ir).run().resources["resource:agitator"].enabled


@pytest.mark.parametrize("valid", [True, False])
def test_mypy_typeguard_and_property_types(tmp_path, valid):
    source = '''from typing import assert_type
from sciloom import Agitator, comptime
from examples.developer.demo_contribution import DemoAgitator
def configure(device: Agitator) -> None:
    if comptime.is_device(device, DemoAgitator):
        assert_type(device, DemoAgitator)
        device.gain = 0.5
        device.calibrate()
    assert_type(device, Agitator)
'''
    if not valid:
        source += '''    device.gain = 1.0
    if comptime.is_device(device, DemoAgitator):
        device.gain = "invalid"
'''
    path = tmp_path / "guard_types.py"
    path.write_text(source)
    result = subprocess.run([sys.executable, "-m", "mypy", str(path)], capture_output=True, text=True)
    assert result.returncode == (0 if valid else 1), result.stdout + result.stderr
    if not valid:
        assert result.stdout.count(" error: ") == 2, result.stdout
