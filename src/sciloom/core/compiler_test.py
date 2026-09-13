"""The compiler contract must work without AutoSuite or XML."""

import subprocess
import sys
from dataclasses import replace

import pytest

from .compiler import Artifact, compile_ir
from .devices import DeviceBindings
from .diagnostics import CompilationError, Diagnostic, IRValidationError
from .ir import FunctionIR, Program


class TextTarget:
    target_id = "test-text"

    def __init__(self, *, reject=False):
        self.reject = reject
        self.emitted = False

    def resolve_devices(self, program):
        return DeviceBindings()

    def validate(self, program):
        return (Diagnostic(code="unsupported", message="Rejected by target.", path="$"),) if self.reject else ()

    def emit(self, program):
        self.emitted = True
        return Artifact(content=b"plain text, not XML", media_type="text/plain", suffix=".txt")


def program():
    return Program(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Empty"),))


def test_non_xml_artifact_and_write(tmp_path):
    target = TextTarget()
    source = program()
    result = compile_ir(source, target=target)
    assert result.semantic_ir is source
    assert result.target_id == "test-text"
    assert result.artifact.suffix == ".txt"
    assert result.write(tmp_path / "out.txt").read_bytes() == b"plain text, not XML"


def test_validation_precedes_emission():
    target = TextTarget()
    with pytest.raises(IRValidationError):
        compile_ir(replace(program(), entry_function_id="missing"), target=target)
    assert not target.emitted
    target = TextTarget(reject=True)
    with pytest.raises(CompilationError, match="unsupported"):
        compile_ir(program(), target=target)
    assert not target.emitted


def test_target_is_explicit():
    with pytest.raises(TypeError):
        compile_ir(program())
    with pytest.raises(TypeError, match="target"):
        compile_ir(program(), target="autosuite-2.47.1.1")


def test_import_and_compilation_without_vendor_modules():
    script = """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.devices", "sciloom.dsl", "sciloom_autosuite")):
            raise ImportError("authoring and vendor modules are forbidden")
sys.meta_path.insert(0, Block())
import sciloom
assert "sciloom.core.compiler" not in sys.modules
assert not {"Target", "Artifact", "CompileResult", "compile_ir", "RuntimeField"} & set(sciloom.__all__)
for name in ("Target", "Artifact", "CompileResult", "compile_ir", "RuntimeField"):
    assert not hasattr(sciloom, name)
from sciloom.core.compiler_test import program, TextTarget
from sciloom.core.compiler import compile_ir
from sciloom.core.ir import from_json, to_json
from sciloom.core.interpreter import Interpreter
assert compile_ir(from_json(to_json(program())), target=TextTarget()).artifact.content.startswith(b"plain")
"""
    subprocess.run([sys.executable, "-c", script], check=True)
