"""The contributor example stays reproducible and cannot imply a native adapter."""

from dataclasses import replace
from pathlib import Path

import pytest

from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from .lifecycle_commands import Reconfigure, RecordingTarget
from .source_paths import repository_relative


def test_lifecycle_companion_and_native_rejection():
    compiled = Reconfigure().compile(target=RecordingTarget())
    program = repository_relative(compiled.specialized_ir)
    companion = Path(__file__).with_name("lifecycle_commands.json").read_text()
    assert to_json(program) == companion
    assert from_json(companion) == program
    assert "unsupported_device_command" in {d.code for d in AutoSuiteTarget().validate(program)}
    # Exercise the task emitter's independent rejection after satisfying its
    # fixed-binding input contract; this does not claim profile compatibility.
    function = program.functions[0]
    halt_only = replace(program, functions=(replace(function, body=(function.body[-1],)),))
    with pytest.raises(CompilationError, match="unsupported_operation"):
        AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="rack", device_id="1")}).emit(halt_only)
