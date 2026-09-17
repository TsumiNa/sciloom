"""Generate state-lifetime measurements without modifying an APP or running hardware.

Run: uv run python -m autosuite.tools.probe_state_lifetime --output-dir /tmp/state-probes
Output: Generated 4 state-lifetime probe bundles; Executor status: pending.

The fresh directory contains ASFP, JSON, deployment sidecars and manifest.json.
Use each probe under both APP reset settings, call twice, restart the application
and call again. Reference expectations specify SciLoom semantics, not observed
AutoSuite behavior. Follow autosuite/docs/33_DEPLOYMENT_STATE_LIFETIME.md.
"""

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from autosuite.tools.probe_runtime_failure import CORPUS, ROOT, _source_versions
from sciloom import Function, Output, Var, log, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.interpreter import Interpreter
from sciloom.core.interpreter.environment import LogEvent
from sciloom.core.ir import Program, from_json, to_json
from sciloom_autosuite import AutoSuiteTarget, write_autosuite_review


class Accumulator(Function):
    total: Var[int] = 0
    result: Output[int]

    @runtime
    def run(self) -> None:
        self.total += 1
        self.result = self.total
        log(self.total, category="sciloom.state_probe", stream="counter")


class Pair(Function):
    first_value: Output[int]
    second_value: Output[int]

    def __init__(self, shared: bool) -> None:
        self.first = Accumulator()
        self.second = self.first if shared else Accumulator()

    @runtime
    def run(self) -> None:
        self.first_value = self.first()
        self.second_value = self.second()


class Loop(Function):
    iteration: Var[int] = 0
    result: Output[int]

    def __init__(self) -> None:
        self.child = Accumulator()

    @runtime
    def run(self) -> None:
        self.iteration = 0
        while self.iteration < 3:
            self.result = self.child()
            self.iteration += 1


@dataclass(frozen=True, kw_only=True)
class StateCase:
    name: str
    program: Program
    expected_runs: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]


def build_cases() -> tuple[StateCase, ...]:
    """Return four cases covering re-entry, ownership, loops and fresh initialization."""
    return (
        StateCase(name="entry", program=Accumulator().to_ir(), expected_runs=((1,), (2,), (1,))),
        StateCase(name="shared", program=Pair(True).to_ir(), expected_runs=((1, 2), (3, 4), (1, 2))),
        StateCase(name="distinct", program=Pair(False).to_ir(), expected_runs=((1, 1), (2, 2), (1, 1))),
        StateCase(name="loop", program=Loop().to_ir(), expected_runs=((1, 2, 3), (4, 5, 6), (1, 2, 3))),
    )


def reference_result(case: StateCase) -> dict[str, object]:
    """Run JSON-restored semantics twice, then use a fresh reference session."""
    program = from_json(to_json(case.program))
    session = Interpreter(program)
    runs = []
    for interpreter, expected in zip((session, session, Interpreter(program)), case.expected_runs, strict=True):
        result = interpreter.run()
        values = [event.value for event in result.events if isinstance(event, LogEvent)]
        if values != list(expected) or len(values) != len(result.events):
            raise RuntimeError(f"Reference expectation failed for {case.name}.")
        runs.append({"counter_log": values, "outputs": dict(result.outputs)})
    return {"outcome": "completed", "runs": runs, "third_run": "fresh reference session, not an APP restart"}


def generate(output_dir: Path) -> Path:
    """Write candidate probes and pending manifests in fresh scratch space only."""
    destination = output_dir.resolve()
    if destination.is_relative_to(CORPUS.resolve()):
        raise ValueError("Probe output must be outside the read-only corpus.")
    if destination.exists():
        raise FileExistsError(f"Use a new output directory: {destination}")
    versions = _source_versions()
    target = AutoSuiteTarget()
    prepared = [(case, compile_ir(case.program, target=target), reference_result(case)) for case in build_cases()]
    records = []
    destination.mkdir(parents=True, exist_ok=False)
    for case, compiled, reference in prepared:
        write_autosuite_review(compiled, target=target, path=destination / (case.name + ".asfp"))
        (destination / (case.name + ".json")).write_text(to_json(case.program), encoding="utf-8")
        files = {}
        for label, suffix in (("asfp", ".asfp"), ("ir", ".json"), ("deployment", ".deployment.json")):
            path = destination / (case.name + suffix)
            files[label] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        records.append(
            {
                "name": case.name,
                "entry_function": next(
                    f.name for f in case.program.functions if f.node_id == case.program.entry_function_id
                ),
                **files,
                "reference": reference,
                "host_runs": [
                    {
                        "reset_variables": setting,
                        "sequence": ["call", "call", "restart APP then call"],
                        "status": "pending",
                    }
                    for setting in (False, True)
                ],
            }
        )
    manifest = {
        "probe_format": 1,
        "executor_status": "pending",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "package_versions": versions,
        "target": target.target_id,
        "cases": records,
    }
    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    try:
        generate(options.output_dir)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print("Generated 4 state-lifetime probe bundles; Executor status: pending.")


if __name__ == "__main__":
    main()
