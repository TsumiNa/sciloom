"""State probes retain session distinctions and cannot manufacture native evidence."""

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from autosuite.tools import probe_state_lifetime as probes
from sciloom.core.ir import from_json


def test_reference_sessions_ownership_and_loop_reentry():
    cases = probes.build_cases()
    assert [case.name for case in cases] == ["entry", "shared", "distinct", "loop"]
    for case in cases:
        result = probes.reference_result(case)
        assert [r["counter_log"] for r in result["runs"]] == [list(run) for run in case.expected_runs]
        assert result["outcome"] == "completed"
    programs = {case.name: case.program for case in cases}
    assert len(programs["shared"].functions) == 2
    assert len(programs["distinct"].functions) == 3


def test_generated_artifacts_and_two_reset_experiments_remain_pending(tmp_path):
    path = probes.generate(tmp_path / "state")
    manifest = json.loads(path.read_text())
    assert manifest["executor_status"] == "pending"
    assert len(manifest["source_commit"]) == 40
    assert type(manifest["source_dirty"]) is bool
    assert manifest["package_versions"] == probes._source_versions()
    assert len(manifest["cases"]) == 4
    assert len(list(path.parent.iterdir())) == 13
    for record in manifest["cases"]:
        assert [run["reset_variables"] for run in record["host_runs"]] == [False, True]
        assert all(run["status"] == "pending" for run in record["host_runs"])
        for label in ("asfp", "ir", "deployment"):
            artifact = path.parent / record[label]["path"]
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == record[label]["sha256"]
        report = json.loads((path.parent / record["deployment"]["path"]).read_text())
        assert report["status"] == "unknown" and report["native_status"] == "pending"
        assert report["artifact_sha256"] == record["asfp"]["sha256"]
        assert report["requirements"]
        assert ET.parse(path.parent / record["asfp"]["path"]).getroot().tag == "functions"
        program = from_json((path.parent / record["ir"]["path"]).read_text())
        assert program == next(case.program for case in probes.build_cases() if case.name == record["name"])


def test_output_protection_and_source_check_before_writes(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setattr(probes, "CORPUS", evidence)
    link = tmp_path / "linked-evidence"
    link.symlink_to(evidence, target_is_directory=True)
    for path in (evidence / "new", link / "new"):
        with pytest.raises(ValueError, match="corpus"):
            probes.generate(path)
    with pytest.raises(FileExistsError):
        probes.generate(tmp_path)
    assert not list(evidence.iterdir())

    def invalid_source():
        raise ValueError("checkout")

    monkeypatch.setattr(probes, "_source_versions", invalid_source)
    with pytest.raises(ValueError, match="checkout"):
        probes.generate(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_cli_generates_explicit_scratch_only(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "autosuite.tools.probe_state_lifetime", "--output-dir", str(tmp_path / "cli")],
        cwd=probes.ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Generated 4 state-lifetime probe bundles; Executor status: pending."
