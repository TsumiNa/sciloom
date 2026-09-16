"""Unknown export mode remains a measured native candidate, never an enabled mapping."""

import hashlib
import json
import xml.etree.ElementTree as ET

import pytest

from autosuite.tools import probe_csv_append as probes


def test_bundle_keeps_observed_profile_and_records_pending_measurements(tmp_path):
    path = probes.generate(tmp_path / "probes", host_directory="C:/SciLoomAppendProbes")
    manifest = json.loads(path.read_text())
    assert manifest["executor_status"] == "pending" and manifest["semantic_equivalence"] == "unverified"
    assert len(manifest["cases"]) == 6
    for case in manifest["cases"]:
        for file in case["files"]:
            assert hashlib.sha256((path.parent / file["path"]).read_bytes()).hexdigest() == file["sha256"]
        root = ET.parse(path.parent / (case["name"] + ".asfp"))
        macro = root.find("./function/components/component")
        variables = {v.findtext("name") for v in macro.findall("./variables/variable")}
        task = macro.find("./tasks/task[@typeid='Chemspeed.SATaskExportCSV.1']")
        assert task.findtext("exportresultvar") in variables
        assert task.findtext("exportbehaviour") == "0"
        assert task.findtext("./columns/column/variabletype") == "text"
        assert len(macro.findall("./tasks/task[@typeid='Chemspeed.SATaskLogData.1']")) == 3
        assert not root.findall(".//*[@typeid='Chemspeed.SATaskSetAgitation.1']")
    assert (path.parent / "existing_file.csv").read_bytes() == b"sentinel\r\n"
    assert not (path.parent / "missing_parent.csv").exists()


@pytest.mark.requires_corpus
def test_native_envelope_matches_export_evidence():
    path = probes.CORPUS / "type_templates/43_Chemspeed.SATaskExportCSV.1_representative.xml"
    if not path.exists():
        pytest.skip("Local corpus is absent.")
    original = ET.parse(path).getroot()
    for case in probes.cases():
        task = ET.fromstring(probes.native_probe(case, "C:/SciLoomAppendProbes")).find(
            ".//*[@typeid='Chemspeed.SATaskExportCSV.1']"
        )
        assert [child.tag for child in task] == [child.tag for child in original]
        assert [child.tag for child in task.find("columns/column")] == [
            child.tag for child in original.find("columns/column")
        ]


def test_no_evidence_writes_overwrite_relative_paths_or_foreign_checkout(tmp_path, monkeypatch):
    with pytest.raises(FileExistsError):
        probes.generate(tmp_path, host_directory="C:/SciLoomAppendProbes")
    monkeypatch.setattr(probes, "CORPUS", tmp_path / "evidence")
    with pytest.raises(ValueError, match="corpus"):
        probes.generate(tmp_path / "evidence/new", host_directory="C:/SciLoomAppendProbes")
    with pytest.raises(ValueError, match="absolute Windows"):
        probes.generate(tmp_path / "new", host_directory="relative")
    monkeypatch.setattr(probes, "getfile", lambda obj: str(tmp_path / "foreign.py"))
    with pytest.raises(ValueError, match="outside this checkout"):
        probes.generate(tmp_path / "new", host_directory="C:/SciLoomAppendProbes")
    assert not (tmp_path / "new").exists()
