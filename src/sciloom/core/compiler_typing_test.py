"""Static extension contracts accept valid targets and reject malformed artifacts/IR."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("valid", [True, False])
def test_compiler_type_contract(tmp_path, valid):
    source = """
from pathlib import Path
from typing import assert_type
from sciloom.core.devices import DeviceBindings
from sciloom.core.compiler import Artifact, CompileResult, Target, compile_ir
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import FunctionIR, ListType, Literal, Program, ScalarType

class TextTarget:
    @property
    def target_id(self) -> str:
        return "text"
    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings()
    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()
    def emit(self, program: Program) -> Artifact:
        return Artifact(content=b"ok", media_type="text/plain", suffix=".txt")

target: Target = TextTarget()
program = Program(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Example"),))
result = compile_ir(program, target=target)
assert_type(result, CompileResult)
assert_type(result.artifact, Artifact)
assert_type(result.semantic_ir, Program)
assert_type(result.specialized_ir, Program)
assert_type(result.write("example.txt"), Path)
literal = Literal(node_id="literal", type=ScalarType.REAL, value=1.0)
numbers = ListType(element_type=ScalarType.REAL)
"""
    if not valid:
        source += """
class BadTarget:
    target_id = "bad"
    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings()
    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()
    def emit(self, program: Program) -> str:
        return "not an artifact"

bad: Target = BadTarget()
compile_ir(program, target=BadTarget())
Artifact(content="text", media_type="text/plain", suffix=".txt")
Literal(node_id="bad", type=ScalarType.REAL, value="text")
ListType(element_type=float)
def bad_artifact() -> Artifact:
    return "not an artifact"
"""
    path = tmp_path / "compiler_contract.py"
    path.write_text(textwrap.dedent(source))
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(root / "pyproject.toml"),
            "--cache-dir",
            str(tmp_path / "cache"),
            str(path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if valid:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert result.stdout.count(" error: ") == 6, result.stdout
        for code in ("[assignment]", "[arg-type]", "[return-value]"):
            assert code in result.stdout
