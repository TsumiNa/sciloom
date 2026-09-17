"""Synthetic scratch receipts exercise validation; they are never native evidence."""

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from autosuite.tools import probe_csv_append, probe_csv_read, probe_runtime_failure
from autosuite.tools.validate_native_receipt import ProbeSuite, validate_receipt


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def record(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}


def synthetic_receipt(tmp_path, suite):
    """Only tests fabricate observations; keep all bytes in pytest scratch directories."""
    generated = tmp_path / "generated"
    if suite == ProbeSuite.RUNTIME_FAILURE:
        manifest_path = probe_runtime_failure.generate(generated)
        cases = probe_runtime_failure.build_cases()
    else:
        module = probe_csv_read if suite == ProbeSuite.CSV_READ else probe_csv_append
        manifest_path = module.generate(generated, host_directory="C:/Probes")
        cases = module.cases()
    manifest = json.loads(manifest_path.read_text())
    # A synthetic clean-source declaration tests association, not provenance truth.
    manifest["source_dirty"] = False
    manifest["source_commit"] = "a" * 40
    write_json(manifest_path, manifest)
    received = tmp_path / "received"
    received.mkdir()
    payload = {
        "receipt_format": 1,
        "suite": suite.value,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "source_commit": manifest["source_commit"],
        "package_versions": manifest["package_versions"],
        "product_version": "2.47.1.1",
        "profile": "autosuite-2.47.1.1",
        "configuration_notes": "Synthetic test only; not a native execution or receipt.",
        "cases": [],
    }
    for case in cases:
        app = record(
            received,
            case.name + "/probe.app",
            gzip.compress(
                b'<application productversion="2.47.1.1"><resetvariables>0</resetvariables></application>', mtime=0
            ),
        )
        reexport = record(received, case.name + "/reexport.asfp", (generated / (case.name + ".asfp")).read_bytes())
        before = None
        if suite != ProbeSuite.RUNTIME_FAILURE:
            before = case.data if suite == ProbeSuite.CSV_READ else case.seed
        runs = []
        for number in range(1, 2 if suite == ProbeSuite.RUNTIME_FAILURE else 3):
            prefix = f"{case.name}/run{number}/"
            observations = {
                "outcome": "completed",
                "markers": ["before", "after"],
                "values": [],
                "native_error": None,
                "stopped": False,
                "notes": "Synthetic test observation, not an AutoSuite result.",
            }
            if suite == ProbeSuite.RUNTIME_FAILURE:
                observations["markers"] = list(case.expected_markers) + ([] if case.failure else ["host.after"])
                if case.failure:
                    observations.update(outcome="failed", stopped=True, native_error="Synthetic bounds error")
            else:
                observations["native_status"] = 0
                if suite == ProbeSuite.CSV_READ:
                    observations["values"] = [([] if case.all_rows else 12) for _ in case.types]
            run = {
                "number": number,
                "app": app,
                "reexport": reexport,
                "command": [
                    "AutoSuiteExecutor.exe",
                    f"C:/Probes/{case.name}/probe.app",
                    "/r",
                    "/sim",
                    "100",
                    "/s",
                    "/c",
                ],
                "exit_code": 0,
                "log": record(received, prefix + "executor.log", b"Synthetic native log for validator tests only.\n"),
                "observations": record(received, prefix + "observed.json", json.dumps(observations).encode()),
            }
            if suite != ProbeSuite.RUNTIME_FAILURE:
                after = before if suite == ProbeSuite.CSV_READ else (before or b"") + b"synthetic\r\n"
                run["csv_before"] = None if before is None else record(received, prefix + "before.csv", before)
                run["csv_after"] = None if after is None else record(received, prefix + "after.csv", after)
                before = after
            runs.append(run)
        payload["cases"].append({"name": case.name, "runs": runs})
    receipt_path = received / "receipt.json"
    write_json(receipt_path, payload)
    return manifest_path, receipt_path, payload


@pytest.mark.parametrize(
    "suite,count", [(ProbeSuite.RUNTIME_FAILURE, 9), (ProbeSuite.CSV_READ, 14), (ProbeSuite.CSV_APPEND, 6)]
)
def test_complete_receipts_are_read_only_and_always_pending_review(tmp_path, suite, count):
    manifest, receipt, _ = synthetic_receipt(tmp_path, suite)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assessment = validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=suite)
    assert assessment.native_status == "pending_review"
    assert assessment.source_commit == "a" * 40
    assert len(assessment.case_names) == count
    assert {path: path.read_bytes() for path in before} == before
    if suite == ProbeSuite.RUNTIME_FAILURE:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "autosuite.tools.validate_native_receipt",
                "--suite",
                suite.value,
                "--manifest",
                str(manifest),
                "--receipt",
                str(receipt),
            ],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "Complete receipt: 9 cases; native status: pending_review."


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("manifest_sha256", "0" * 64, "Manifest hash"),
        ("source_commit", "b" * 40, "source commit mismatch"),
        ("package_versions", {"sciloom": "9.0.0", "sciloom-autosuite": "9.0.0"}, "versions mismatch"),
        ("product_version", "9.0.0", "product/profile"),
        ("profile", "autosuite-9.0.0", "product/profile"),
        ("suite", "csv_read", "suite mismatch"),
        ("receipt_format", True, "receipt format"),
    ],
)
def test_mismatched_identity_is_rejected(tmp_path, field, value, match):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    payload[field] = value
    write_json(receipt, payload)
    with pytest.raises(ValueError, match=match):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)


@pytest.mark.parametrize("dirty", [True, None, 0])
def test_dirty_or_unknown_source_is_not_accepted(tmp_path, dirty):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    data = json.loads(manifest.read_text())
    data["source_dirty"] = dirty
    write_json(manifest, data)
    payload["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    write_json(receipt, payload)
    with pytest.raises(ValueError, match="Dirty"):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)


@pytest.mark.parametrize(
    "change",
    [
        "missing_case",
        "duplicate_case",
        "missing_control_marker",
        "missing_run",
        "app",
        "command",
        "log",
        "reexport",
        "artifact",
    ],
)
def test_missing_controls_or_inconsistent_evidence_is_rejected(tmp_path, change):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    run = payload["cases"][0]["runs"][0]
    if change == "missing_case":
        payload["cases"].pop(0)
    elif change == "duplicate_case":
        payload["cases"].append(payload["cases"][0])
    elif change == "missing_control_marker":
        path = receipt.parent / run["observations"]["path"]
        observations = json.loads(path.read_text())
        observations["markers"].remove("host.after")
        run["observations"] = record(receipt.parent, run["observations"]["path"], json.dumps(observations).encode())
    elif change == "missing_run":
        payload["cases"][0]["runs"] = []
    elif change == "app":
        run["app"] = record(
            receipt.parent,
            "entry_control/wrong.app",
            gzip.compress(b'<application productversion="9.0.0"><resetvariables>0</resetvariables></application>'),
        )
    elif change == "command":
        run["command"][3] = "/real"
    elif change == "log":
        run["log"] = record(receipt.parent, "empty.log", b"")
    elif change == "reexport":
        run["reexport"] = record(receipt.parent, "bad.asfp", b"<broken>")
    elif change == "artifact":
        (manifest.parent / "entry_control.asfp").write_bytes(b"changed")
    write_json(receipt, payload)
    with pytest.raises(ValueError):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)


@pytest.mark.parametrize("change", ["missing_bytes", "reset_seed", "changed_bytes", "changed_app", "one_run"])
def test_csv_repeated_runs_require_actual_bytes_and_continuity(tmp_path, change):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.CSV_APPEND)
    case = next(case for case in payload["cases"] if case["name"] == "existing_file")
    first, second = case["runs"]
    if change == "missing_bytes":
        del second["csv_after"]
    elif change == "reset_seed":
        second["csv_before"] = first["csv_before"]
    elif change == "changed_bytes":
        (receipt.parent / second["csv_after"]["path"]).write_bytes(b"tampered")
    elif change == "changed_app":
        second["app"] = record(
            receipt.parent,
            "changed/probe.app",
            gzip.compress(b'<application productversion="2.47.1.1"><resetvariables>1</resetvariables></application>'),
        )
    else:
        case["runs"].pop()
    write_json(receipt, payload)
    with pytest.raises(ValueError):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.CSV_APPEND)


@pytest.mark.parametrize("change", ["missing", "extra", "not_list"])
def test_exact_documented_command_shape_is_required(tmp_path, change):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    run = payload["cases"][0]["runs"][0]
    if change == "missing":
        run["command"].pop()
    elif change == "extra":
        run["command"].append("/m")
    else:
        run["command"] = "AutoSuiteExecutor.exe probe.app /r /sim 100 /s /c"
    write_json(receipt, payload)
    with pytest.raises(ValueError, match="actual Executor argv required"):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)


def test_csv_array_lengths_cannot_replace_values(tmp_path):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.CSV_READ)
    run = next(case for case in payload["cases"] if case["name"] == "recipe_columns")["runs"][0]
    path = receipt.parent / run["observations"]["path"]
    observed = json.loads(path.read_text())
    observed["values"] = [2, 2]
    run["observations"] = record(receipt.parent, run["observations"]["path"], json.dumps(observed).encode())
    write_json(receipt, payload)
    with pytest.raises(ValueError, match="full arrays"):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.CSV_READ)


def test_contradictory_failure_observation_remains_pending_not_verified(tmp_path):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    run = next(case for case in payload["cases"] if case["name"] == "child_negative")["runs"][0]
    path = receipt.parent / run["observations"]["path"]
    observed = json.loads(path.read_text())
    observed.update(outcome="completed", stopped=False, native_error=None)
    observed["markers"].append("host.after")
    run["observations"] = record(receipt.parent, run["observations"]["path"], json.dumps(observed).encode())
    write_json(receipt, payload)
    assessment = validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)
    assert assessment.native_status == "pending_review"
    assert "host.after" in json.loads(path.read_text())["markers"]


def test_path_escape_duplicate_json_and_cli_diagnostics(tmp_path):
    manifest, receipt, payload = synthetic_receipt(tmp_path, ProbeSuite.RUNTIME_FAILURE)
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"outside")
    link = receipt.parent / "link.log"
    link.symlink_to(outside)
    payload["cases"][0]["runs"][0]["log"] = {"path": "link.log", "sha256": hashlib.sha256(b"outside").hexdigest()}
    write_json(receipt, payload)
    with pytest.raises(ValueError, match="escapes"):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "autosuite.tools.validate_native_receipt",
            "--suite",
            "runtime_failure",
            "--manifest",
            str(manifest),
            "--receipt",
            str(receipt),
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "escapes" in result.stderr
    receipt.write_text('{"receipt_format":1,"receipt_format":1}')
    with pytest.raises(ValueError, match="duplicate key"):
        validate_receipt(manifest_path=manifest, receipt_path=receipt, suite=ProbeSuite.RUNTIME_FAILURE)
