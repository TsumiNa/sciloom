"""An external package adds device members without changing shared semantics."""

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
from typing import ClassVar, Callable

import pytest

from examples.developer.demo_contribution import DemoAgitator, DemoTarget
from examples.developer.demo_device import DemoExperiment
from sciloom import Agitator, Function, Input, rpm, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.devices import DeviceBindings
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import DeviceCommand, from_json, to_json
from sciloom.devices import operation
from sciloom.devices.declarations import bind_device


class PulseAgitator(Agitator):
    device_type_id = "example.pulse-agitator/v1"
    writable_properties = ("speed",)
    required_configuration = ("speed",)

    @operation(id="example.pulse-agitator.pulse/v1")
    def pulse(self, count: int, /, levels: list[float], *, enabled: bool) -> None:
        raise AssertionError("Lowering must not call this body")

    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (pulse, Agitator.start, Agitator.stop)


def test_external_contribution_roundtrip_and_no_invented_execution():
    program = DemoExperiment().to_ir()
    target = DemoTarget(devices={"agitator": DemoAgitator()})
    result = compile_ir(from_json(to_json(program)), target=target)
    assert result.semantic_ir == program
    assert from_json(result.artifact.content.decode()) == result.specialized_ir
    with pytest.raises(ExecutionError, match="unsupported_operation"):
        Interpreter(program).run()


def test_native_argument_binding_and_value_types():
    class Pulse(Function):
        agitator: PulseAgitator

        @runtime
        def run(self):
            self.agitator.pulse(2, [0.25, 1], enabled=True)

    program = Pulse().to_ir()
    command = program.functions[0].body[0]
    assert isinstance(command, DeviceCommand)
    assert [a.name for a in command.arguments] == ["count", "levels", "enabled"]
    assert from_json(to_json(program)) == program

    class Missing(Pulse):
        @runtime
        def run(self):
            self.agitator.pulse(2, [1.0])

    class PositionalOnly(Pulse):
        @runtime
        def run(self):
            self.agitator.pulse(count=2, levels=[1.0], enabled=True)

    class KeywordOnly(Pulse):
        @runtime
        def run(self):
            self.agitator.pulse(2, [1.0], True)

    class WrongType(Pulse):
        @runtime
        def run(self):
            self.agitator.pulse(2, [True], enabled=True)

    for cls in (Missing, PositionalOnly, KeywordOnly, WrongType):
        with pytest.raises(IRValidationError):
            cls().to_ir()


def test_selected_native_capability_and_trusted_signature():
    class RestrictedTarget(DemoTarget):
        def resolve_devices(self, program):
            binding = bind_device(logical_id="agitator", device=DemoAgitator(), physical_id="demo")
            return DeviceBindings(devices=(replace(binding, supported_operations=()),))

    with pytest.raises(CompilationError, match="device_capability"):
        DemoExperiment().compile(target=RestrictedTarget(devices={}))
    program = DemoExperiment().to_ir()
    contract = next(c for c in program.device_types if c.type_id == DemoAgitator.device_type_id)
    forged = replace(contract, required_configuration=())
    program = replace(program, device_types=tuple(forged if c == contract else c for c in program.device_types))
    with pytest.raises(CompilationError, match="contract"):
        compile_ir(program, target=DemoTarget(devices={"agitator": DemoAgitator()}))


def test_demo_required_gain_and_range_are_contributor_rules():
    class Missing(Function):
        agitator: DemoAgitator

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            self.agitator.start()

    class Unknown(Function):
        agitator: DemoAgitator
        gain: Input[float]

        @runtime
        def run(self):
            self.agitator.gain = self.gain

    class Outside(Unknown):
        @runtime
        def run(self):
            self.agitator.gain = 1.5

    target = DemoTarget(devices={"agitator": DemoAgitator()})
    with pytest.raises(CompilationError, match="device_configuration"):
        Missing().compile(target=target)
    for cls in (Unknown, Outside):
        with pytest.raises(CompilationError, match="demo_gain_range"):
            cls().compile(target=target)


def test_contribution_imports_from_outside_sciloom(tmp_path):
    source = Path(__file__).resolve().parents[3] / "examples/developer/demo_contribution"
    shutil.copytree(source, tmp_path / "demo_contribution", ignore=shutil.ignore_patterns("__pycache__"))
    script = tmp_path / "check.py"
    script.write_text('from demo_contribution import DemoAgitator, DemoTarget\nimport sys\nfrom sciloom.core.compiler import Target\nassert isinstance(DemoTarget(devices={"agitator": DemoAgitator()}), Target)\nassert not any(k.startswith("sciloom.contrib.autosuite") for k in sys.modules)\n')
    result = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("valid", [True, False])
def test_contributor_mypy_contract(tmp_path, valid):
    source = '''from typing import assert_type
from examples.developer.demo_contribution import DemoAgitator, DemoTarget
from sciloom import RotationalSpeed, rpm
from sciloom.core.compiler import Target
def configure(device: DemoAgitator) -> None:
    device.speed = 600 * rpm
    device.gain = 0.5
    device.calibrate()
    assert_type(device.speed, RotationalSpeed)
target: Target = DemoTarget(devices={"agitator": DemoAgitator()})
'''
    if not valid:
        source += '''def wrong(device: DemoAgitator) -> None:
    device.speed = 123
    device.gain = "high"
    device.calibrate(1)
'''
    script = tmp_path / "typing_contribution.py"
    script.write_text(source)
    result = subprocess.run([sys.executable, "-m", "mypy", str(script)], capture_output=True, text=True)
    assert result.returncode == (0 if valid else 1), result.stdout + result.stderr
    if not valid:
        assert result.stdout.count(" error: ") == 3, result.stdout
