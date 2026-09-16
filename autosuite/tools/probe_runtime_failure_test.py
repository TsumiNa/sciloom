"""Probe generation cannot claim Executor success or write into evidence."""

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from autosuite.tools import probe_runtime_failure as probes
from sciloom.core.ir import from_json


def test_all_cases_have_reference_controls_and_precise_failure_sources():
    cases = probes.build_cases()
    assert len(cases) == 9
    for case in cases:
        result = probes.reference_result(case)
        assert result["markers"] == list(case.expected_markers)
        assert result["outcome"] == ("failed" if case.failure else "completed")
        diagnostic = result["diagnostic"]
        if case.failure:
            assert diagnostic["code"] == "index_bounds"
            assert diagnostic["node_id"]
            assert diagnostic["source"]["path"].endswith("probe_runtime_failure.py")
            assert diagnostic["source"]["line"] > 0
        else:
            assert diagnostic is None


def test_generated_manifest_hashes_and_pending_status(tmp_path):
    manifest_path = probes.generate(tmp_path / "probes")
    manifest = json.loads(manifest_path.read_text())
    assert manifest["executor_status"] == "pending"
    assert len(manifest["source_commit"]) == 40
    assert type(manifest["source_dirty"]) is bool
    assert manifest["package_versions"]["sciloom"] == manifest["package_versions"]["sciloom-autosuite"]
    assert len(manifest["cases"]) == 9
    by_name = {case.name: case for case in probes.build_cases()}
    for record in manifest["cases"]:
        case = by_name[record["name"]]
        assert record["reference"] == probes.reference_result(case)
        for artifact in ("asfp", "ir"):
            path = manifest_path.parent / record[artifact]["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record[artifact]["sha256"]
        program = from_json((manifest_path.parent / record["ir"]["path"]).read_text())
        assert program == case.program
        root = ET.parse(manifest_path.parent / record["asfp"]["path"]).getroot()
        assert root.tag == "functions"
        assert not any("Stir" in element.attrib.get("typeid", "") for element in root.iter())
        expressions = [e.text or "" for e in root.findall(".//expressiontext")]
        assert any("[" in expression for expression in expressions)
        assert any("ArraySize(" in expression for expression in expressions)


def test_generator_refuses_existing_directory_and_corpus_even_via_symlink(tmp_path, monkeypatch):
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "keep"
    sentinel.write_text("untouched")
    with pytest.raises(FileExistsError):
        probes.generate(existing)
    assert list(existing.iterdir()) == [sentinel]
    assert sentinel.read_text() == "untouched"
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setattr(probes, "CORPUS", evidence)
    link = tmp_path / "link"
    link.symlink_to(evidence, target_is_directory=True)
    for output in (evidence / "new", link / "new"):
        with pytest.raises(ValueError, match="corpus"):
            probes.generate(output)
    assert list(evidence.iterdir()) == []


def test_cli_generates_only_explicit_scratch_output(tmp_path):
    output = tmp_path / "cli"
    result = subprocess.run(
        [sys.executable, probes.__file__, "--output-dir", str(output)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Generated 9 probe pairs; Executor status: pending."
    assert len(list(output.iterdir())) == 19
