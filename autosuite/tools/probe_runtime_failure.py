"""Generate host failure probes without touching corpus files or running hardware.

Run from the checkout:
    uv run python autosuite/tools/probe_runtime_failure.py --output-dir /tmp/sciloom-failure-probes

Expected short output:
    Generated 9 probe pairs; Executor status: pending.

The new directory contains nine ASFP/JSON pairs and manifest.json with hashes,
reference expectations and provenance. These are scratch validation artifacts,
not accepted application programs. Follow autosuite/docs/24_RUNTIME_FAILURE_GATE.md
on the AutoSuite host; this script neither generates an APP nor runs Executor.
"""

import argparse
import hashlib
import json
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from inspect import getfile
from pathlib import Path

from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import Diagnostic, ExecutionError
from sciloom.core.interpreter.environment import LogEvent
from sciloom.core.interpreter.runtime import Interpreter
from sciloom.core.ir.codec import from_json, to_json
from sciloom.core.ir.model import Program
from sciloom.flow.fields import Var
from sciloom.flow.function import Function, runtime
from sciloom.flow.logging import log
from sciloom_autosuite.target import AutoSuiteTarget

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "autosuite/corpus"


class EntryProbe(Function):
    """Attempt one read between distinguishable log markers."""

    values: Var[list[int]] = [7]
    captured: Var[int] = 0

    def __init__(self, position: int) -> None:
        self.position = position

    @runtime
    def run(self) -> None:
        log("entry.before", category="sciloom.failure_probe", stream="markers")
        self.captured = self.values[self.position]
        log("entry.after", category="sciloom.failure_probe", stream="markers")


class ChildProbe(Function):
    """Check whether a failing call also prevents the caller's next action."""

    def __init__(self, position: int) -> None:
        self.child = EntryProbe(position)

    @runtime
    def run(self) -> None:
        log("caller.before", category="sciloom.failure_probe", stream="markers")
        self.child()
        log("caller.after", category="sciloom.failure_probe", stream="markers")


class LoopProbe(Function):
    """Check the remaining body, next iteration and statement after a loop."""

    values: Var[list[int]] = [7]
    captured: Var[int] = 0
    iteration: Var[int] = 0

    def __init__(self, position: int) -> None:
        self.position = position

    @runtime
    def run(self) -> None:
        self.iteration = 0
        while self.iteration < 2:
            log("loop.before", category="sciloom.failure_probe", stream="markers")
            self.captured = self.values[self.position]
            log("loop.after", category="sciloom.failure_probe", stream="markers")
            self.iteration += 1
        log("loop.finished", category="sciloom.failure_probe", stream="markers")


@dataclass(frozen=True, kw_only=True)
class ProbeCase:
    """A fixed candidate/control with its expected reference marker sequence."""

    name: str
    program: Program
    failure: bool
    expected_markers: tuple[str, ...]


def build_cases() -> tuple[ProbeCase, ...]:
    """Build entry/call/loop controls, positive bounds failures and negative indices."""
    cases = []
    for scope, model, before, complete in (
        ("entry", EntryProbe, ("entry.before",), ("entry.before", "entry.after")),
        (
            "child",
            ChildProbe,
            ("caller.before", "entry.before"),
            ("caller.before", "entry.before", "entry.after", "caller.after"),
        ),
        (
            "loop",
            LoopProbe,
            ("loop.before",),
            ("loop.before", "loop.after", "loop.before", "loop.after", "loop.finished"),
        ),
    ):
        for mode, position in (("control", 0), ("out_of_range", 1), ("negative", -1)):
            cases.append(
                ProbeCase(
                    name=f"{scope}_{mode}",
                    program=model(position).to_ir(),
                    failure=position != 0,
                    expected_markers=before if position != 0 else complete,
                )
            )
    return tuple(cases)


def reference_result(case: ProbeCase) -> dict[str, object]:
    """Execute the JSON-restored candidate and record the actual reference result."""
    session = Interpreter(from_json(to_json(case.program)))
    diagnostic: Diagnostic | None = None
    try:
        session.run()
    except ExecutionError as error:
        diagnostic = error.diagnostics[0]
    markers = []
    for event in session.environment.events:
        if not isinstance(event, LogEvent) or not isinstance(event.value, str):
            raise RuntimeError("Probe emitted an unexpected event.")
        markers.append(event.value)
    if (
        (diagnostic is not None) != case.failure
        or (diagnostic is not None and diagnostic.code != "index_bounds")
        or tuple(markers) != case.expected_markers
    ):
        raise RuntimeError(f"Reference expectation failed for {case.name}.")
    return {
        "outcome": "failed" if diagnostic is not None else "completed",
        "markers": markers,
        "diagnostic": asdict(diagnostic) if diagnostic is not None else None,
    }


def _source_versions() -> dict[str, str]:
    """Tie declared versions and loaded implementations to this source checkout."""
    versions = {}
    for name, project, implementation, path in (
        ("sciloom", ROOT, Function, "src/sciloom/flow/function.py"),
        (
            "sciloom-autosuite",
            ROOT / "packages/sciloom-autosuite",
            AutoSuiteTarget,
            "packages/sciloom-autosuite/src/sciloom_autosuite/target.py",
        ),
    ):
        if Path(getfile(implementation)).resolve() != (ROOT / path).resolve():
            raise ValueError(f"Loaded {name} is outside this checkout; run uv sync --locked first.")
        value = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        if not isinstance(value, str):
            raise ValueError(f"Source version for {name} must be a string.")
        versions[name] = value
    if len(set(versions.values())) != 1:
        raise ValueError("Source workspace package versions must remain in lockstep.")
    return versions


def generate(output_dir: Path) -> Path:
    """Write fresh candidate artifacts and a pending manifest outside the corpus.

    Args:
        output_dir: New scratch directory; existing directories are refused.

    Returns:
        Path of the generated manifest. Executor status is always pending.

    Raises:
        ValueError: The destination is in the corpus, or source provenance is inconsistent.
        FileExistsError: The destination already exists.
        RuntimeError: A reference expectation fails before files are written.
    """
    destination = output_dir.resolve()
    if destination.is_relative_to(CORPUS.resolve()):
        raise ValueError("Probe output must be outside the read-only corpus.")
    if destination.exists():
        raise FileExistsError(f"Use a new output directory: {destination}")
    package_versions = _source_versions()
    target = AutoSuiteTarget()
    artifacts: dict[str, bytes] = {}
    records = []
    for case in build_cases():
        compiled = compile_ir(case.program, target=target)
        record: dict[str, object] = {
            "name": case.name,
            "entry_function": next(
                f.name for f in case.program.functions if f.node_id == case.program.entry_function_id
            ),
            "reference": reference_result(case),
        }
        for label, suffix, content in (
            ("asfp", ".asfp", compiled.artifact.content),
            ("ir", ".json", to_json(case.program).encode("utf-8")),
        ):
            name = case.name + suffix
            artifacts[name] = content
            record[label] = {"path": name, "sha256": hashlib.sha256(content).hexdigest()}
        records.append(record)
    manifest = {
        "probe_format": 1,
        "executor_status": "pending",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "package_versions": package_versions,
        "target": target.target_id,
        "cases": records,
    }
    artifacts["manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in artifacts.items():
        (destination / name).write_bytes(content)
    return destination / "manifest.json"


def main() -> None:
    """Generate probes in an explicitly named fresh directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    try:
        generate(options.output_dir)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print("Generated 9 probe pairs; Executor status: pending.")


if __name__ == "__main__":
    main()
