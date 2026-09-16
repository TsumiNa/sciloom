"""Native measurement artifacts remain separate from portable compilation."""

import hashlib
import json
import xml.etree.ElementTree as ET

import pytest

from autosuite.tools import probe_csv_read as probes


def test_native_bundle_has_typed_macro_destinations_and_pending_results(tmp_path):
    manifest_path = probes.generate(tmp_path / "probes", host_directory="C:/SciLoomProbes")
    manifest = json.loads(manifest_path.read_text())
    assert manifest["executor_status"] == "pending"
    assert manifest["semantic_equivalence"] == "unverified"
    assert len(manifest["cases"]) == 14
    for case in manifest["cases"]:
        for file in case["files"]:
            assert hashlib.sha256((manifest_path.parent / file["path"]).read_bytes()).hexdigest() == file["sha256"]
        root = ET.parse(manifest_path.parent / (case["name"] + ".asfp"))
        macro = root.find("./function/components/component")
        variables = {v.findtext("name") for v in macro.findall("./variables/variable")}
        read = macro.find("./tasks/task[@typeid='Chemspeed.SATaskImportCSV.1']")
        assert read is not None
        assert read.findtext("importresultvar") in variables
        for i, column in enumerate(read.findall("./columns/column")):
            assert column.findtext("destinationvariable") in variables
            assert column.findtext("columnindex") == str(i + 1)
        assert not root.findall(".//*[@typeid='Chemspeed.SATaskSetAgitation.1']")
    assert not (manifest_path.parent / "missing_file.csv").exists()


@pytest.mark.requires_corpus
def test_probe_envelope_matches_observed_import_shape():
    template = probes.CORPUS / "type_templates/46_Chemspeed.SATaskImportCSV.1_representative.xml"
    if not template.exists():
        pytest.skip("Local corpus is absent.")
    original = ET.parse(template).getroot()
    for case in probes.cases():
        generated = ET.fromstring(probes.native_probe(case, "C:/SciLoomProbes")).find(
            ".//*[@typeid='Chemspeed.SATaskImportCSV.1']"
        )
        assert [e.tag for e in generated] == [e.tag for e in original]
        assert [e.tag for e in generated.find("./columns/column")] == [e.tag for e in original.find("./columns/column")]


def test_no_overwrite_corpus_or_relative_host_paths(tmp_path, monkeypatch):
    with pytest.raises(FileExistsError):
        probes.generate(tmp_path, host_directory="C:/SciLoomProbes")
    monkeypatch.setattr(probes, "CORPUS", tmp_path / "evidence")
    with pytest.raises(ValueError, match="corpus"):
        probes.generate(tmp_path / "evidence/new", host_directory="C:/SciLoomProbes")
    with pytest.raises(ValueError, match="absolute Windows"):
        probes.generate(tmp_path / "new", host_directory="relative")
    assert not (tmp_path / "new").exists()


def test_probe_provenance_rejects_another_loaded_checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(probes, "getfile", lambda obj: str(tmp_path / "another.py"))
    with pytest.raises(ValueError, match="outside this checkout"):
        probes.generate(tmp_path / "wrong", host_directory="C:/SciLoomProbes")
    assert not (tmp_path / "wrong").exists()
