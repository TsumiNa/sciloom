"""Generate isolated native CSV probes; this does not compile SciLoom ReadCsv.

Run: uv run python autosuite/tools/probe_csv_read.py --output-dir /tmp/csv-probes --host-directory C:/SciLoomProbes
Output: Generated 14 native CSV probes; Executor status: pending.

The fresh scratch directory contains ASFP probes, data files and manifest.json.
Copy the data to the explicitly named Windows directory before simulation.
No corpus file, APP or equipment is modified. See ../docs/27_CSV_READ_MAPPING.md.
These native behavior measurements are not implementations of portable CSV reads.
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
from sciloom.core.ir import (
    FunctionIR,
    ListLength,
    ListLiteral,
    ListType,
    Literal,
    LogValue,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
)
from sciloom_autosuite import AutoSuiteTarget
from sciloom_autosuite.encoding import literal_value

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "autosuite/corpus"


@dataclass(frozen=True, kw_only=True)
class NativeCase:
    """One vendor-profile question; results are deliberately not predicted."""

    name: str
    data: bytes | None
    types: tuple[ScalarType, ...]
    defaults: tuple[str, ...]
    question: str
    header: bool = False
    row: int = 0
    all_rows: bool = False


def cases() -> tuple[NativeCase, ...]:
    """Cover controls, conversion, unit defaults and aggregate error precedence."""
    return (
        NativeCase(
            name="integer_control",
            data=b"12\n",
            types=(ScalarType.INTEGER,),
            defaults=("7",),
            question="Confirm a plain integer and result 0.",
        ),
        NativeCase(
            name="integer_fraction",
            data=b"1.5\n",
            types=(ScalarType.INTEGER,),
            defaults=("7",),
            question="Does truncation warn without a nonzero result?",
        ),
        NativeCase(
            name="numeric_expression",
            data=b"1+2\n",
            types=(ScalarType.REAL,),
            defaults=("7",),
            question="Does the cell evaluate as an expression rather than literal data?",
        ),
        NativeCase(
            name="text_quotes",
            data='"日本語, ""quoted"""\r\n'.encode(),
            types=(ScalarType.TEXT,),
            defaults=("'fallback'",),
            question="Record exact Unicode and quote decoding.",
        ),
        NativeCase(
            name="text_bom",
            data="\ufeffname\n日本語\n".encode(),
            types=(ScalarType.TEXT,),
            defaults=("'fallback'",),
            header=True,
            question="Does UTF-8 BOM affect header removal or text?",
        ),
        NativeCase(
            name="boolean",
            data=b"true\n",
            types=(ScalarType.BOOLEAN,),
            defaults=("false",),
            question="Confirm the Boolean cell profile.",
        ),
        NativeCase(
            name="volume_unit",
            data=b"2\n",
            types=(ScalarType.VOLUME,),
            defaults=("0.000003",),
            question="Does unit ml convert 2 to 0.000002 m^3?",
        ),
        NativeCase(
            name="volume_default",
            data=b"invalid\n",
            types=(ScalarType.VOLUME,),
            defaults=("0.000003",),
            question="Is the native default interpreted in SI independently of unit ml?",
        ),
        NativeCase(
            name="missing_file",
            data=None,
            types=(ScalarType.INTEGER,),
            defaults=("7",),
            question="Record result, destination and continuation on IO failure.",
        ),
        NativeCase(
            name="eof",
            data=b"12\n",
            types=(ScalarType.INTEGER,),
            defaults=("7",),
            row=1,
            question="Record result, destination and continuation past EOF.",
        ),
        NativeCase(
            name="mixed_columns",
            data=b"bad\n",
            types=(ScalarType.INTEGER, ScalarType.INTEGER),
            defaults=("7", "8"),
            question="Which result wins between invalid and missing columns?",
        ),
        NativeCase(
            name="mixed_rows",
            data=b"bad\n1,2\n3\n",
            types=(ScalarType.INTEGER, ScalarType.INTEGER),
            defaults=("7", "8"),
            all_rows=True,
            question="Inspect aligned arrays and error precedence across rows.",
        ),
        NativeCase(
            name="empty_columns",
            data=b"id,volume\n",
            types=(ScalarType.TEXT, ScalarType.VOLUME),
            defaults=("'missing'", "0"),
            header=True,
            all_rows=True,
            question="Does header-only input clear both arrays or preserve old data?",
        ),
        NativeCase(
            name="recipe_columns",
            data=b"id,volume\nA,1.5\nB,2\n",
            types=(ScalarType.TEXT, ScalarType.VOLUME),
            defaults=("'missing'", "0"),
            header=True,
            all_rows=True,
            question="Confirm F28-shaped array lengths, values, SI units and status.",
        ),
    )


def native_probe(case: NativeCase, host_directory: str) -> bytes:
    """Insert one observed native task into an otherwise compiled logging shell."""
    variables = [
        Variable(
            node_id="status",
            owner_id="f",
            name="status",
            type=ScalarType.INTEGER,
            role=VariableRole.INTERNAL,
            initial=Literal(node_id="initial-status", type=ScalarType.INTEGER, value=-99),
        )
    ]
    for i, scalar in enumerate(case.types):
        value = "sentinel" if scalar == ScalarType.TEXT else (False if scalar == ScalarType.BOOLEAN else 99)
        initial = Literal(node_id=f"initial-{i}", type=scalar, value=value)
        kind = ListType(element_type=scalar) if case.all_rows else scalar
        variables.append(
            Variable(
                node_id=f"v{i}",
                owner_id="f",
                name=f"value{i}",
                role=VariableRole.INTERNAL,
                type=kind,
                initial=ListLiteral(node_id=f"list-{i}", type=kind, elements=(initial,))
                if isinstance(kind, ListType)
                else initial,
            )
        )
    body = [
        LogValue(
            node_id="before",
            value=Literal(node_id="before-value", type=ScalarType.TEXT, value="before"),
            category=Literal(node_id="before-category", type=ScalarType.TEXT, value="sciloom.csv_probe"),
            stream=Literal(node_id="before-stream", type=ScalarType.TEXT, value=case.name),
        )
    ]
    for i, variable in enumerate(variables):
        ref = Reference(node_id=f"read-{i}", symbol_id=variable.node_id)
        body.append(
            LogValue(
                node_id=f"log-{i}",
                value=ListLength(node_id=f"length-{i}", value=ref) if isinstance(variable.type, ListType) else ref,
                category=Literal(node_id=f"category-{i}", type=ScalarType.TEXT, value="sciloom.csv_probe"),
                stream=Literal(
                    node_id=f"stream-{i}",
                    type=ScalarType.TEXT,
                    value=variable.name + (".length" if case.all_rows and i else ""),
                ),
            )
        )
    program = Program(
        entry_function_id="f",
        functions=(FunctionIR(node_id="f", name=case.name, variables=tuple(variables), body=tuple(body)),),
    )
    root = ET.fromstring(compile_ir(program, target=AutoSuiteTarget()).artifact.content)
    tasks = root.find("./function/components/component/tasks")
    assert tasks is not None
    # LogData capture tasks precede its log. Insert after the first actual log,
    # before captures for the remaining status/value observations.
    position = next(i for i, task in enumerate(tasks) if task.get("typeid") == "Chemspeed.SATaskLogData.1") + 1
    task = ET.Element("task", {"typeid": "Chemspeed.SATaskImportCSV.1"})
    path = str(PureWindowsPath(host_directory) / (case.name + ".csv"))
    fields = (
        ("description", "Native CSV probe; semantic equivalence unverified"),
        ("name", "Import CSV"),
        ("edittime", "0"),
        ("importfilepath", literal_value(Literal(node_id="path", type=ScalarType.TEXT, value=path))),
        ("delimitermode", "0"),
        ("iswithheader", str(int(case.header))),
        ("rowtoread", str(case.row + 1)),
        ("importresultvar", "status"),
        ("importrowmode", str(int(case.all_rows))),
    )
    for name, value in fields:
        ET.SubElement(task, name).text = value
    columns = ET.SubElement(task, "columns")
    for i, (scalar, default) in enumerate(zip(case.types, case.defaults, strict=True)):
        column = ET.SubElement(columns, "column")
        for name, value in (
            ("columnindex", str(i + 1)),
            ("destinationvariable", f"value{i}"),
            ("defaultvalue", default),
            ("unit", "ml" if scalar == ScalarType.VOLUME else "1"),
        ):
            ET.SubElement(column, name).text = value
    ET.SubElement(task, "id").text = "{" + str(uuid5(NAMESPACE_URL, "sciloom.csv_probe/" + case.name)).upper() + "}"
    tasks.insert(position, task)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def generate(output_dir: Path, *, host_directory: str) -> Path:
    """Write a fresh native probe bundle outside evidence; never run Executor."""
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
        if case.data is not None:
            names.append(case.name + ".csv")
            artifacts[names[-1]] = case.data
        records.append(
            {
                "name": case.name,
                "question": case.question,
                "absent_file": case.data is None,
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
    print(f"Generated {len(cases())} native CSV probes; Executor status: pending.")


if __name__ == "__main__":
    main()
