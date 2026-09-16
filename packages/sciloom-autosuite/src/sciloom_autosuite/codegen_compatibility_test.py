"""Old v4 JSON retains exact ASFP bytes, including all deterministic UUIDs."""

import hashlib
import json
from pathlib import Path

import pytest

from sciloom.core.compiler import compile_ir
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json
from sciloom.units import rpm
from . import AutoSuiteIndividualShaker, AutoSuiteTarget

FIXTURES = Path(__file__).resolve().parents[4] / "src/sciloom/core/ir/fixtures/v4"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text())


@pytest.mark.parametrize("name", MANIFEST["programs"])
def test_old_v4_artifact_bytes(name):
    program = from_json((FIXTURES / f"{name}.json").read_text())
    target = AutoSuiteTarget(
        devices={
            r.logical_id: AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23") for r in program.resources
        }
    )
    result = compile_ir(program, target=target)
    assert hashlib.sha256(result.artifact.content).hexdigest() == MANIFEST["programs"][name]["asfp_sha256"]
    if name == "portable_agitation":
        snapshot = Interpreter(result.specialized_ir).run(inputs={"speed": 600 * rpm})
        assert snapshot.resources["resource:agitator"].applied_configuration == {"speed": 600 * rpm}
