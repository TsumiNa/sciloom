"""Synthetic probe fixtures check construction, never claim native acceptance."""

import hashlib
import json
import xml.etree.ElementTree as ET
from copy import deepcopy

import pytest

from autosuite.tools import probe_dialog_results as probes
from sciloom.core.interpreter import Interpreter, LogEvent, QueuedAcknowledgements, ReferenceEnvironment


@pytest.fixture
def source(tmp_path):
    # Deliberately synthetic flat envelopes, not received native evidence.
    root = ET.Element("functions")
    for kind in probes.DialogKind:
        task = ET.SubElement(root, "task", typeid=probes.TYPE_ID)
        fields = {
            "id": kind.value,
            "resultvariablename": "original_result",
            "interpretmessageasexpressionflag": "1",
            "maxwaittimeunit": "s",
            "validateinput": "0",
            "defaultpauseafterdialog": "0",
            "softstopping": "0",
            "logtoserver": "0",
            "dialogtype": "askforinput" if kind == probes.DialogKind.TEXT else "showmessage",
            "buttonoption": "okstop" if kind == probes.DialogKind.TEXT else "yesnostop",
            "resultunit": "text" if kind == probes.DialogKind.TEXT else "1",
            "yesokresultexpression": "" if kind == probes.DialogKind.TEXT else "1",
            "noresultexpression": "" if kind == probes.DialogKind.TEXT else "0",
            "maxwaittimeexpression": "original_timeout",
            "timeoutanswerexpression": "original_default",
        }
        for field in probes.FIELDS:
            ET.SubElement(task, field).text = fields.get(field, "")
    path = tmp_path / "synthetic.asfp"
    path.write_bytes(ET.tostring(root))
    return path


def generate(destination, source):
    return probes.generate(destination, source_asfp=source, text_task_id="text", choice_task_id="choice")


def test_thirty_hashed_device_free_probes_and_semantic_marker_controls(tmp_path, source):
    original = source.read_bytes()
    path = generate(tmp_path / "probes", source)
    manifest = json.loads(path.read_text())
    assert source.read_bytes() == original
    assert manifest["native_source"]["sha256"] == hashlib.sha256(original).hexdigest()
    assert manifest["native_source"]["product_version"] is None
    assert manifest["native_source"]["profile"] is None
    assert manifest["executor_status"] == "pending"
    assert manifest["semantic_equivalence"] == "unverified"
    assert manifest["host_command_options"] == ["/r", "/sim", "100", "/c"]
    assert len(manifest["cases"]) == len(probes.cases()) == 30
    assert len({case["name"] for case in manifest["cases"]}) == 30
    for case, record in zip(probes.cases(), manifest["cases"], strict=True):
        artifact = path.parent / record["files"][0]["path"]
        data = artifact.read_bytes()
        assert record["files"][0]["sha256"] == hashlib.sha256(data).hexdigest()
        tree = ET.fromstring(data)
        (dialog,) = tree.findall(f".//*[@typeid='{probes.TYPE_ID}']")
        assert tuple(e.tag for e in dialog) == probes.FIELDS
        assert dialog.findtext("resultvariablename") == "captured"
        assert dialog.findtext("maxwaittimeexpression") == ("2" if case.action == probes.Action.TIMEOUT else "0")
        assert dialog.findtext("timeoutanswerexpression") == (
            "'NATIVE_TIMEOUT'" if case.kind == probes.DialogKind.TEXT else "0"
        )
        assert not tree.findall(".//*[@typeid='Chemspeed.SATaskSetAgitation.1']")
        (declaration,) = [v for v in tree.findall(".//variables/variable") if v.findtext("name") == "captured"]
        assert declaration.findtext("value/type") == ("8" if case.kind == probes.DialogKind.TEXT else "3")
        assert record["entry_function"] in [f.findtext("name") for f in tree.findall("function")]
        assert record["executor_status"] == "pending"
        # Only the supported acknowledgement shell is reference-executed here.
        # It proves control placement, not substituted native dialog behavior.
        result = Interpreter(
            probes.shell(case),
            environment=ReferenceEnvironment(
                acknowledgements=QueuedAcknowledgements([True, True]),
            ),
        ).run()
        markers = [e.value for e in result.events if isinstance(e, LogEvent) and e.stream == "markers"]
        if case.successful:
            assert markers == record["semantic_marker_order"]
        else:
            expected = record["semantic_marker_order"]
            assert markers[: len(expected)] == expected and expected[-1] == "dialog.before"
        assert record["actions_required"] == (2 if case.context == probes.Context.LOOP and case.successful else 1)
    second = generate(tmp_path / "second", source)
    for record in manifest["cases"]:
        name = record["files"][0]["path"]
        assert (path.parent / name).read_bytes() == (second.parent / name).read_bytes()


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "kind", "field", "nested", "order", "binding", "policy", "zone"]
)
def test_unsupported_source_rejects_before_writing(tmp_path, source, change):
    root = ET.parse(source).getroot()
    task = root[0]
    if change == "missing":
        task.find("id").text = "elsewhere"
    elif change == "duplicate":
        root.append(deepcopy(task))
    elif change == "kind":
        task.set("typeid", "Unknown")
    elif change == "field":
        ET.SubElement(task, "extra")
    elif change == "nested":
        ET.SubElement(task.find("message"), "nested")
    elif change == "order":
        task[0], task[1] = task[1], task[0]
    elif change == "binding":
        task.find("resultvariablename").text = ""
    elif change == "policy":
        task.find("softstopping").text = "1"
    else:
        task.find("destzone").text = "equipment"
    source.write_bytes(ET.tostring(root))
    with pytest.raises(ValueError):
        generate(tmp_path / "rejected", source)
    assert not (tmp_path / "rejected").exists()


def test_no_overwrite_or_corpus_output(tmp_path, source, monkeypatch):
    with pytest.raises(FileExistsError):
        generate(tmp_path, source)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(corpus, target_is_directory=True)
    monkeypatch.setattr(probes, "CORPUS", corpus)
    with pytest.raises(ValueError, match="corpus"):
        generate(alias / "new", source)
    assert not (corpus / "new").exists()


@pytest.mark.requires_corpus
def test_distilled_envelope_matches_received_template():
    path = probes.CORPUS / "type_templates/63_Chemspeed.SATaskUserDialog.1_representative.xml"
    if not path.exists():
        pytest.skip("Local corpus is absent.")
    assert tuple(e.tag for e in ET.parse(path).getroot()) == probes.FIELDS
