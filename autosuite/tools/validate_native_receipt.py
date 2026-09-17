"""Check native measurement receipts without running Executor or enabling capabilities.

Run: uv run python -m autosuite.tools.validate_native_receipt --help
For a received bundle, supply --suite, --manifest and --receipt as documented in
autosuite/docs/35_NATIVE_MEASUREMENT_RECEIPTS.md. A successful check reports
pending_review: hashes and completeness do not prove recorded native behavior.
This tool is read-only and is not imported by the compiler.
"""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from autosuite.tools import probe_csv_append, probe_csv_read, probe_runtime_failure
from sciloom_autosuite import AutoSuiteDeployment, AutoSuiteVersion


class ProbeSuite(StrEnum):
    RUNTIME_FAILURE = "runtime_failure"
    CSV_READ = "csv_read"
    CSV_APPEND = "csv_append"


@dataclass(frozen=True, kw_only=True)
class ReceiptAssessment:
    """A complete associated receipt, still awaiting review of its native claims."""

    suite: ProbeSuite
    source_commit: str
    product_version: str
    profile: str
    case_names: tuple[str, ...]

    @property
    def native_status(self) -> Literal["pending_review"]:
        return "pending_review"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value: Any, context: str) -> dict[str, Any]:
    _require(type(value) is dict, f"{context}: expected an object.")
    return value


def _text(value: Any, context: str) -> str:
    _require(type(value) is str and bool(value.strip()), f"{context}: expected nonempty text.")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            _require(key not in result, f"{path.name}: duplicate key {key!r}.")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError(f"{path.name}: nonfinite JSON value {value}.")

    return _object(
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant), path.name
    )


def _file(root: Path, value: Any, context: str) -> Path:
    record = _object(value, context)
    name = _text(record.get("path"), context + ".path")
    expected = record.get("sha256")
    _require(
        type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected) is not None, f"{context}: invalid SHA-256."
    )
    relative = Path(name)
    _require(not relative.is_absolute() and not PureWindowsPath(name).is_absolute(), f"{context}: use a relative path.")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root.resolve()), f"{context}: file escapes its evidence bundle.")
    _require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"{context}: file hash mismatch.")
    return path


def _cases(value: Any, context: str) -> dict[str, dict[str, Any]]:
    _require(type(value) is list, f"{context}: expected a case array.")
    result = {}
    for item in value:
        record = _object(item, context)
        name = _text(record.get("name"), context + ".name")
        _require(name not in result, f"{context}: duplicate case {name!r}.")
        result[name] = record
    return result


def _observations(path: Path, context: str) -> dict[str, Any]:
    observed = _read_json(path)
    markers = observed.get("markers")
    _require(
        type(markers) is list and all(type(m) is str and m for m in markers), f"{context}: ordered markers required."
    )
    _require(observed.get("outcome") in ("completed", "failed", "stopped", "timed_out"), f"{context}: invalid outcome.")
    _require(type(observed.get("stopped")) is bool, f"{context}: stopped must be recorded explicitly.")
    _require("native_error" in observed, f"{context}: native_error must be text or null.")
    if observed["native_error"] is not None:
        _text(observed["native_error"], context + ".native_error")
    _require(type(observed.get("values")) is list, f"{context}: complete observed values must be an array.")
    _text(observed.get("notes"), context + ".notes")
    return observed


def validate_receipt(*, manifest_path: Path, receipt_path: Path, suite: ProbeSuite) -> ReceiptAssessment:
    """Check source/artifact association, case coverage, controls and file continuity.

    Args:
        manifest_path: Original unmodified generator manifest beside its artifacts.
        receipt_path: Host receipt beside the received APP/re-export/log/byte files.
        suite: Explicit suite whose complete existing case set is required.

    Returns:
        Immutable completeness assessment with native_status pending_review.

    Raises:
        ValueError: A document, hash, association or control is incomplete/inconsistent.
        OSError: A required evidence file cannot be read.

    Recorded observations may contradict SciLoom semantics. Completeness does not
    approve those claims, prove their authenticity, or change a compiler gate.
    """
    suite = ProbeSuite(suite)
    manifest = _read_json(manifest_path)
    receipt = _read_json(receipt_path)
    _require(type(manifest.get("probe_format")) is int and manifest["probe_format"] == 1, "Unsupported probe format.")
    _require(
        type(receipt.get("receipt_format")) is int and receipt["receipt_format"] == 1, "Unsupported receipt format."
    )
    _require(receipt.get("suite") == suite.value, "Receipt suite mismatch.")
    _require(manifest.get("executor_status") == "pending", "Preserve the original pending generator manifest.")
    _require(manifest.get("source_dirty") is False, "Dirty or unknown source cannot attest to a clean commit.")
    commit = manifest.get("source_commit")
    _require(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Invalid source commit.")
    _require(receipt.get("source_commit") == commit, "Receipt source commit mismatch.")
    _require(
        receipt.get("manifest_sha256") == hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "Manifest hash mismatch.",
    )
    versions = _object(manifest.get("package_versions"), "package_versions")
    _require(set(versions) == {"sciloom", "sciloom-autosuite"}, "Both source package versions are required.")
    _require(
        all(type(v) is str and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v) for v in versions.values())
        and len(set(versions.values())) == 1,
        "Source versions must be explicit and lockstep.",
    )
    _require(receipt.get("package_versions") == versions, "Receipt package versions mismatch.")
    profile = _text(receipt.get("profile"), "profile")
    product = _text(receipt.get("product_version"), "product_version")
    _require(
        profile == AutoSuiteVersion.V2_47_1_1.value and profile == "autosuite-" + product,
        "Unsupported product/profile association.",
    )
    if "target" in manifest:
        _require(manifest["target"] == profile, "Manifest target/profile mismatch.")
    _text(receipt.get("configuration_notes"), "configuration_notes")
    expected = (
        probe_runtime_failure.build_cases()
        if suite == ProbeSuite.RUNTIME_FAILURE
        else probe_csv_read.cases()
        if suite == ProbeSuite.CSV_READ
        else probe_csv_append.cases()
    )
    expected_names = tuple(case.name for case in expected)
    generated = _cases(manifest.get("cases"), "manifest.cases")
    received = _cases(receipt.get("cases"), "receipt.cases")
    _require(set(generated) == set(expected_names), "Manifest lacks the complete suite, including controls.")
    _require(set(received) == set(expected_names), "Receipt lacks the complete suite, including controls.")
    for name in expected_names:
        candidate = generated[name]
        artifacts = (
            [candidate.get("asfp"), candidate.get("ir")]
            if suite == ProbeSuite.RUNTIME_FAILURE
            else candidate.get("files")
        )
        _require(type(artifacts) is list and bool(artifacts), f"{name}: generated artifacts required.")
        artifact_paths = [_file(manifest_path.parent, item, name + ".generated") for item in artifacts]
        _require(len({p.name for p in artifact_paths}) == len(artifact_paths), f"{name}: duplicate generated artifact.")
        expected_suffixes = {".asfp", ".json"} if suite == ProbeSuite.RUNTIME_FAILURE else {".asfp"}
        case = next(case for case in expected if case.name == name)
        seed = None if suite == ProbeSuite.RUNTIME_FAILURE else case.data if suite == ProbeSuite.CSV_READ else case.seed
        if seed is not None:
            expected_suffixes.add(".csv")
        _require(
            {p.name for p in artifact_paths} == {name + suffix for suffix in expected_suffixes},
            f"{name}: missing or unexpected generated files.",
        )
        if seed is not None:
            _require(
                (manifest_path.parent / (name + ".csv")).read_bytes() == seed,
                f"{name}: generated input differs from suite case.",
            )
        runs = received[name].get("runs")
        count = 1 if suite == ProbeSuite.RUNTIME_FAILURE else 2
        _require(type(runs) is list and len(runs) == count, f"{name}: expected {count} run(s).")
        previous_csv = hashlib.sha256(seed).hexdigest() if seed is not None else None
        previous_app = None
        for number, value in enumerate(runs, 1):
            context = f"{name}.run{number}"
            run = _object(value, context)
            _require(
                type(run.get("number")) is int and run["number"] == number, f"{context}: ordered run number required."
            )
            app = _file(receipt_path.parent, run.get("app"), context + ".app")
            deployment = AutoSuiteDeployment.from_app(app)
            _require(deployment.product_version == product, f"{context}: APP product/profile mismatch.")
            _require(deployment.reset_variables is not None, f"{context}: APP reset setting must be observed.")
            if previous_app is not None:
                _require(deployment.app_sha256 == previous_app, f"{context}: APP changed between repeated runs.")
            previous_app = deployment.app_sha256
            reexport = _file(receipt_path.parent, run.get("reexport"), context + ".reexport")
            try:
                _require(
                    ET.parse(reexport).getroot().tag == "functions", f"{context}: native function re-export required."
                )
            except ET.ParseError as error:
                raise ValueError(f"{context}: malformed native re-export XML.") from error
            log = _file(receipt_path.parent, run.get("log"), context + ".log")
            _require(bool(log.read_bytes()), f"{context}: empty native log is inconclusive.")
            command = run.get("command")
            _require(
                type(command) is list and len(command) >= 7 and all(type(s) is str and s for s in command),
                f"{context}: actual Executor argv required.",
            )
            _require(
                PureWindowsPath(command[0]).name.lower() == "autosuiteexecutor.exe", f"{context}: unexpected executor."
            )
            _require(PureWindowsPath(command[1]).name == app.name, f"{context}: command APP filename mismatch.")
            _require(
                command[2:] == ["/r", "/sim", "100", "/s", "/c"],
                f"{context}: record the documented simulation command.",
            )
            _require(type(run.get("exit_code")) is int, f"{context}: integer process exit code required.")
            observed = _observations(
                _file(receipt_path.parent, run.get("observations"), context + ".observations"), context
            )
            if suite == ProbeSuite.RUNTIME_FAILURE:
                if name.endswith("_control"):
                    _require(
                        observed["markers"] == [*case.expected_markers, "host.after"]
                        and observed["outcome"] == "completed"
                        and not observed["stopped"]
                        and observed["native_error"] is None,
                        f"{context}: successful full control and host.after are required; result is inconclusive.",
                    )
            else:
                _require(type(observed.get("native_status")) is int, f"{context}: native CSV result code required.")
                _require(
                    observed["markers"] and observed["markers"][0] == "before",
                    f"{context}: missing before marker is inconclusive.",
                )
                if suite == ProbeSuite.CSV_READ:
                    _require(
                        len(observed["values"]) == len(case.types),
                        f"{context}: all column values, including full arrays, are required.",
                    )
                    if case.all_rows:
                        _require(
                            all(type(value) is list for value in observed["values"]),
                            f"{context}: full arrays are required, not lengths.",
                        )
                    if name == "integer_control":
                        _require(
                            observed["outcome"] == "completed"
                            and observed["native_status"] == 0
                            and observed["native_error"] is None
                            and not observed["stopped"]
                            and observed["values"] == [12]
                            and type(observed["values"][0]) is int,
                            f"{context}: successful integer control required; result is inconclusive.",
                        )
                hashes = []
                for field in ("csv_before", "csv_after"):
                    _require(field in run, f"{context}: {field} must contain exact bytes or explicit null for absence.")
                    record = run[field]
                    if record is not None:
                        _file(receipt_path.parent, record, context + "." + field)
                    hashes.append(None if record is None else record["sha256"])
                _require(hashes[0] == previous_csv, f"{context}: input/seed or repeated-run continuity mismatch.")
                if suite == ProbeSuite.CSV_READ:
                    _require(hashes[1] == hashes[0], f"{context}: CSV input changed during a read measurement.")
                previous_csv = hashes[1]
    return ReceiptAssessment(
        suite=suite, source_commit=commit, product_version=product, profile=profile, case_names=expected_names
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=list(ProbeSuite), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    options = parser.parse_args()
    try:
        result = validate_receipt(
            manifest_path=options.manifest, receipt_path=options.receipt, suite=ProbeSuite(options.suite)
        )
    except (ValueError, OSError, ET.ParseError) as error:
        parser.error(str(error))
    print(f"Complete receipt: {len(result.case_names)} cases; native status: {result.native_status}.")


if __name__ == "__main__":
    main()
