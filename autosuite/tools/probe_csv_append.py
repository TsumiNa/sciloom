"""Generate Export CSV measurements without enabling portable CSV compilation.

Run: uv run python autosuite/tools/probe_csv_append.py --output-dir /tmp/append-probes --host-directory C:/SciLoomAppendProbes
Output: Generated 6 native CSV append probes; Executor status: pending.

The fresh scratch bundle contains ASFPs, seed files and manifest.json. Use a new
Windows scratch directory for each experiment; these probes may overwrite files.
They never run Executor or modify the corpus. See ../docs/28_CSV_APPEND_MAPPING.md.
"""

import argparse
import hashlib
import json
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from inspect import getfile
from pathlib import Path, PureWindowsPath
from uuid import NAMESPACE_URL, uuid5

from sciloom.core.compiler import compile_ir
from sciloom.core.ir import FunctionIR, Literal, LogValue, Program, Reference, ScalarType, Variable, VariableRole
from sciloom_autosuite import AutoSuiteTarget
from sciloom_autosuite.encoding import literal_value

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "autosuite/corpus"


@dataclass(frozen=True, kw_only=True)
class NativeCase:
    """An observed profile and one question about its execution."""

    name: str
    value: str
    seed: bytes | None
    question: str
    missing_parent: bool = False


def cases() -> tuple[NativeCase, ...]:
    """Measure mode, repeated writes, physical encoding and error continuation."""
    return (
        NativeCase(name="new_file", value="record", seed=None, question="Run twice: create, append or replace?"),
        NativeCase(
            name="existing_file",
            value="record",
            seed=b"sentinel\r\n",
            question="Is the sentinel preserved after each of two runs?",
        ),
        NativeCase(
            name="quoted_unicode",
            value='日本語,"quoted"\\path',
            seed=None,
            question="Record bytes, encoding, delimiters and escaped quotes/backslash.",
        ),
        NativeCase(
            name="embedded_newlines",
            value="line1\nline2\r\nline3",
            seed=None,
            question="Are embedded newlines quoted and preserved?",
        ),
        NativeCase(
            name="empty_text", value="", seed=None, question="Does empty text write a distinguishable complete record?"
        ),
        NativeCase(
            name="missing_parent",
            value="record",
            seed=None,
            missing_parent=True,
            question="Does IO error set result 1, then reach the after marker, without creating a directory?",
        ),
    )


def native_probe(case: NativeCase, host_directory: str) -> bytes:
    """Insert the observed export envelope into a typed Macro logging shell."""
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name=case.name,
                variables=(
                    Variable(
                        node_id="status",
                        owner_id="f",
                        name="status",
                        type=ScalarType.INTEGER,
                        role=VariableRole.INTERNAL,
                        initial=Literal(node_id="initial", type=ScalarType.INTEGER, value=-99),
                    ),
                ),
                body=tuple(
                    LogValue(
                        node_id=name,
                        value=Reference(node_id="status-read", symbol_id="status")
                        if name == "status-log"
                        else Literal(node_id=name + "-value", type=ScalarType.TEXT, value=name),
                        category=Literal(
                            node_id=name + "-category", type=ScalarType.TEXT, value="sciloom.csv_append_probe"
                        ),
                        stream=Literal(node_id=name + "-stream", type=ScalarType.TEXT, value=case.name + "." + name),
                    )
                    for name in ("before", "status-log", "after")
                ),
            ),
        ),
    )
    root = ET.fromstring(compile_ir(program, target=AutoSuiteTarget()).artifact.content)
    tasks = root.find("./function/components/component/tasks")
    assert tasks is not None
    position = next(i for i, task in enumerate(tasks) if task.get("typeid") == "Chemspeed.SATaskLogData.1") + 1
    path = PureWindowsPath(host_directory)
    if case.missing_parent:
        path /= "absent-parent"
    path /= case.name + ".csv"
    task = ET.Element("task", {"typeid": "Chemspeed.SATaskExportCSV.1"})
    for name, value in (
        ("description", "Native measurement: exportbehaviour=0 is not confirmed as append"),
        ("name", "Export CSV"),
        ("edittime", "0"),
        ("exportfilepath", literal_value(Literal(node_id="path", type=ScalarType.TEXT, value=str(path)))),
        ("delimitermode", "0"),
        ("endlinecharacter", "0"),
        ("exportbehaviour", "0"),
        ("changerowvar", "1"),
        ("exportresultvar", "status"),
        ("multiplelines", "0"),
    ):
        ET.SubElement(task, name).text = value
    column = ET.SubElement(ET.SubElement(task, "columns"), "column")
    for name, value in (
        ("columnindex", "1"),
        ("expression", literal_value(Literal(node_id="text", type=ScalarType.TEXT, value=case.value))),
        ("variabletype", "text"),
        ("unit", "1"),
    ):
        ET.SubElement(column, name).text = value
    ET.SubElement(task, "id").text = (
        "{" + str(uuid5(NAMESPACE_URL, "sciloom.csv_append_probe/" + case.name)).upper() + "}"
    )
    tasks.insert(position, task)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def generate(output_dir: Path, *, host_directory: str) -> Path:
    """Write a fresh scratch bundle with hashes and pending execution status."""
    destination = output_dir.resolve()
    if destination.is_relative_to(CORPUS.resolve()):
        raise ValueError("Probe output must be outside the read-only corpus.")
    if destination.exists():
        raise FileExistsError("Use a new output directory.")
    if not PureWindowsPath(host_directory).is_absolute():
        raise ValueError("host_directory must be an absolute Windows directory.")
    for implementation, relative in (
        (compile_ir, "src/sciloom/core/compiler.py"),
        (AutoSuiteTarget, "packages/sciloom-autosuite/src/sciloom_autosuite/target.py"),
    ):
        if Path(getfile(implementation)).resolve() != (ROOT / relative).resolve():
            raise ValueError("Loaded implementation is outside this checkout; run uv sync --locked first.")
    versions = {
        name: tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
        for name, root in (("sciloom", ROOT), ("sciloom-autosuite", ROOT / "packages/sciloom-autosuite"))
    }
    if len(set(versions.values())) != 1:
        raise ValueError("Workspace versions must remain in lockstep.")
    artifacts = {}
    records = []
    for case in cases():
        names = [case.name + ".asfp"]
        artifacts[names[0]] = native_probe(case, host_directory)
        if case.seed is not None:
            names.append(case.name + ".csv")
            artifacts[names[-1]] = case.seed
        records.append(
            {
                "name": case.name,
                "question": case.question,
                "run_count": 2,
                "initial_file": "absent" if case.seed is None else "copy seed once before first run",
                "missing_parent": case.missing_parent,
                "files": [{"path": name, "sha256": hashlib.sha256(artifacts[name]).hexdigest()} for name in names],
            }
        )
    manifest = {
        "probe_format": 1,
        "executor_status": "pending",
        "semantic_equivalence": "unverified",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "package_versions": versions,
        "host_directory": host_directory,
        "cases": records,
    }
    destination.mkdir(parents=True)
    for name, data in artifacts.items():
        (destination / name).write_bytes(data)
    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--host-directory", required=True)
    options = parser.parse_args()
    try:
        generate(options.output_dir, host_directory=options.host_directory)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(f"Generated {len(cases())} native CSV append probes; Executor status: pending.")


if __name__ == "__main__":
    main()
