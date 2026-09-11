"""The compiler contract must work without AutoSuite or XML."""

import subprocess
import sys
from dataclasses import replace

import pytest

from sciloom.compiler import Artifact, compile_ir
from sciloom.diagnostics import CompilationError, Diagnostic, IRValidationError
from sciloom.ir import FunctionIR, Package


class TextTarget:
    target_id = "test-text"

    def __init__(self, *, reject=False):
        self.reject = reject
        self.emitted = False

    def validate(self, program):
        return (Diagnostic(code="unsupported", message="Rejected by target.", path="$"),) if self.reject else ()

    def emit(self, program):
        self.emitted = True
        return Artifact(content=b"plain text, not XML", media_type="text/plain", suffix=".txt")


def program():
    return Package(entry_function_id="f", functions=(FunctionIR(node_id="f", name="Empty"),))


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
        if fullname.startswith("sciloom.backends"):
            raise ImportError("vendor modules are forbidden")
sys.meta_path.insert(0, Block())
from sciloom.compiler_test import program, TextTarget
from sciloom.compiler import compile_ir
from sciloom.ir import from_json, to_json
assert compile_ir(from_json(to_json(program())), target=TextTarget()).artifact.content.startswith(b"plain")
"""
    subprocess.run([sys.executable, "-c", script], check=True)
