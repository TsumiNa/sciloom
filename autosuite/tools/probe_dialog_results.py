"""Generate bounded native dialog measurements; never enable semantic compilation.

Run: uv run python -m autosuite.tools.probe_dialog_results --help
After supplying a received ASFP, exact text/choice task IDs and a fresh output
directory, output is: Generated 30 native dialog probes; Executor status: pending.

The scratch directory holds ASFP candidates and a hashed manifest. These measure
vendor behavior, including possible default-answer continuation. They are not
implementations of RequestText/AskYesNo. See ../docs/36_DIALOG_RESULT_PROBES.md.
"""

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from autosuite.tools.probe_runtime_failure import CORPUS, ROOT, _source_versions
from sciloom.core.compiler import compile_ir
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    Call,
    FunctionIR,
    Literal,
    LogValue,
    Notify,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    While,
)
from sciloom_autosuite import AutoSuiteTarget

TYPE_ID = "Chemspeed.SATaskUserDialog.1"
# Distilled ordered envelope; raw native material stays outside git.
FIELDS = (
    "highlightzone",
    "destzone",
    "description",
    "name",
    "edittime",
    "resultvariablename",
    "targetamountvariable",
    "sourcematerial",
    "maxwaittimeexpression",
    "dialogtype",
    "resultunit",
    "interpretmessageasexpressionflag",
    "message",
    "initialvalue",
    "buttonoption",
    "timeoutanswerexpression",
    "yesokresultexpression",
    "noresultexpression",
    "maxwaittimeunit",
    "picturepathexpression",
    "validateinput",
    "minvalidationvalueexpression",
    "maxvalidationvalueexpression",
    "fontsize",
    "usemonospacedfont",
    "defaultpauseafterdialog",
    "softstopping",
    "autodialogheight",
    "dialogwidth",
    "dialogheight",
    "hlrootelementname",
    "hlzonecolor",
    "hldescriptioncount",
    "logtoserver",
    "messagetype",
    "severity",
    "runid",
    "experimentid",
    "trialnumber",
    "productid",
    "id",
)


class DialogKind(StrEnum):
    TEXT = "text"
    CHOICE = "choice"


class Context(StrEnum):
    ENTRY = "entry"
    CHILD = "child"
    LOOP = "loop"


class Action(StrEnum):
    TEXT = "text"
    EMPTY = "empty"
    YES = "yes"
    NO = "no"
    CANCEL = "cancel"
    STOP = "stop"
    TIMEOUT = "timeout"


@dataclass(frozen=True, kw_only=True)
class NativeCase:
    kind: DialogKind
    context: Context
    action: Action

    @property
    def name(self) -> str:
        return f"{self.kind.value}_{self.context.value}_{self.action.value}"

    @property
    def successful(self) -> bool:
        return self.action in (Action.TEXT, Action.EMPTY, Action.YES, Action.NO)

    @property
    def actions_required(self) -> int:
        return 2 if self.context == Context.LOOP and self.successful else 1


def cases() -> tuple[NativeCase, ...]:
    """Enumerate finite controls and termination questions in three call contexts."""
    return tuple(
        NativeCase(kind=kind, context=context, action=action)
        for kind, actions in (
            (DialogKind.TEXT, (Action.TEXT, Action.EMPTY, Action.CANCEL, Action.STOP, Action.TIMEOUT)),
            (DialogKind.CHOICE, (Action.YES, Action.NO, Action.CANCEL, Action.STOP, Action.TIMEOUT)),
        )
        for context in Context
        for action in actions
    )


def select_task(root: ET.Element, task_id: str, kind: DialogKind) -> ET.Element:
    """Select one explicit observed payload and reject ambiguous/unsupported forms."""
    found = [e for e in root.iter() if e.findtext("id") == task_id]
    if len(found) != 1:
        raise ValueError("Each source task ID must select exactly one native task.")
    task = found[0]
    if task.tag not in ("task", "component") or task.attrib != {"typeid": TYPE_ID}:
        raise ValueError("The selected source must be an observed UserDialog task.")
    if tuple(e.tag for e in task) != FIELDS or any(len(e) or e.attrib for e in task):
        raise ValueError("Unsupported native dialog envelope, order or nested payload.")
    expected = {
        "interpretmessageasexpressionflag": "1",
        "maxwaittimeunit": "s",
        "validateinput": "0",
        "defaultpauseafterdialog": "0",
        "softstopping": "0",
        "logtoserver": "0",
        "dialogtype": "askforinput" if kind == DialogKind.TEXT else "showmessage",
        "buttonoption": "okstop" if kind == DialogKind.TEXT else "yesnostop",
        "resultunit": "text" if kind == DialogKind.TEXT else "1",
        "yesokresultexpression": "" if kind == DialogKind.TEXT else "1",
        "noresultexpression": "" if kind == DialogKind.TEXT else "0",
    }
    for field, value in expected.items():
        if (task.findtext(field) or "") != value:
            raise ValueError(f"Unsupported native {kind.value} field {field}.")
    for field in (
        "highlightzone",
        "destzone",
        "targetamountvariable",
        "sourcematerial",
        "picturepathexpression",
        "hlrootelementname",
        "runid",
        "experimentid",
        "trialnumber",
        "productid",
    ):
        if task.findtext(field):
            raise ValueError(f"Device-free probes require an empty {field}.")
    if not task.findtext("resultvariablename"):
        raise ValueError("Source dialog must have an observed result binding.")
    return task


def shell(case: NativeCase) -> Program:
    """Compile only already-supported logging, acknowledgement and call structures."""
    scalar = ScalarType.TEXT if case.kind == DialogKind.TEXT else ScalarType.INTEGER

    def log(node_id: str, marker: str, *, value: Reference | None = None) -> LogValue:
        return LogValue(
            node_id=node_id,
            value=value
            if value is not None
            else Literal(node_id=node_id + ":value", type=ScalarType.TEXT, value=marker),
            category=Literal(node_id=node_id + ":category", type=ScalarType.TEXT, value="sciloom.dialog_probe"),
            stream=Literal(
                node_id=node_id + ":stream", type=ScalarType.TEXT, value="native.value" if value else "markers"
            ),
        )

    dialog = FunctionIR(
        node_id="dialog",
        name=case.name + "_dialog",
        variables=(
            Variable(
                node_id="value",
                owner_id="dialog",
                name="captured",
                type=scalar,
                role=VariableRole.INTERNAL,
                initial=Literal(node_id="initial", type=scalar, value="unchanged" if scalar == ScalarType.TEXT else -9),
            ),
        ),
        body=(
            log("before", "dialog.before"),
            Notify(
                node_id="placeholder", message=Literal(node_id="message", type=ScalarType.TEXT, value="native probe")
            ),
            log("value-log", "", value=Reference(node_id="value-read", symbol_id="value")),
            log("after", "dialog.after"),
        ),
    )
    if case.context == Context.ENTRY:
        return Program(entry_function_id="dialog", functions=(dialog,))
    call = Call(node_id="call", function_id="dialog")
    if case.context == Context.CHILD:
        parent = FunctionIR(
            node_id="caller",
            name=case.name,
            body=(
                log("caller-before", "caller.before"),
                call,
                log("caller-after", "caller.after"),
            ),
        )
    else:
        counter = Variable(
            node_id="index",
            owner_id="caller",
            name="index",
            type=ScalarType.INTEGER,
            role=VariableRole.INTERNAL,
            initial=Literal(node_id="index-initial", type=ScalarType.INTEGER, value=0),
        )
        parent = FunctionIR(
            node_id="caller",
            name=case.name,
            variables=(counter,),
            body=(
                Assignment(
                    node_id="reset",
                    target=Reference(node_id="reset-target", symbol_id="index"),
                    value=Literal(node_id="reset-value", type=ScalarType.INTEGER, value=0),
                ),
                log("caller-before", "caller.before"),
                While(
                    node_id="loop",
                    condition=Binary(
                        node_id="condition",
                        op=BinaryOp.LESS,
                        left=Reference(node_id="index-condition", symbol_id="index"),
                        right=Literal(node_id="limit", type=ScalarType.INTEGER, value=2),
                    ),
                    body=(
                        log("loop-before", "loop.before"),
                        call,
                        log("loop-after", "loop.after"),
                        Assignment(
                            node_id="increment",
                            target=Reference(node_id="increment-target", symbol_id="index"),
                            value=Binary(
                                node_id="plus",
                                op=BinaryOp.ADD,
                                left=Reference(node_id="index-read", symbol_id="index"),
                                right=Literal(node_id="one", type=ScalarType.INTEGER, value=1),
                            ),
                        ),
                    ),
                ),
                log("loop-finished", "loop.finished"),
                log("caller-after", "caller.after"),
            ),
        )
    return Program(entry_function_id="caller", functions=(parent, dialog))


def native_probe(case: NativeCase, template: ET.Element) -> bytes:
    """Substitute one measured native task, without compiling the gated semantic nodes."""
    root = ET.fromstring(compile_ir(shell(case), target=AutoSuiteTarget()).artifact.content)
    placeholders = [(parent, node) for parent in root.iter() for node in parent if node.get("typeid") == TYPE_ID]
    if len(placeholders) != 1:
        raise ValueError("Measurement shell must contain exactly one dialog occurrence.")
    parent, placeholder = placeholders[0]
    task = deepcopy(template)
    task.tag = placeholder.tag
    task.tail = None
    changes = {
        "description": "Native measurement only; portable result/termination semantics unverified",
        "edittime": "0",
        "resultvariablename": "captured",
        "message": "'" + case.name + "'",
        "initialvalue": "''" if case.kind == DialogKind.TEXT else "",
        "maxwaittimeexpression": "2" if case.action == Action.TIMEOUT else "0",
        "timeoutanswerexpression": "'NATIVE_TIMEOUT'" if case.kind == DialogKind.TEXT else "0",
        "id": "{" + str(uuid5(NAMESPACE_URL, "sciloom.dialog_probe/" + case.name)).upper() + "}",
    }
    for field, value in changes.items():
        node = task.find(field)
        assert node is not None
        node.text = value
    parent[list(parent).index(placeholder)] = task
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def generate(output_dir: Path, *, source_asfp: Path, text_task_id: str, choice_task_id: str) -> Path:
    """Write a fresh candidate bundle; source material and compiler gates stay unchanged."""
    destination = output_dir.resolve()
    if destination.is_relative_to(CORPUS.resolve()):
        raise ValueError("Probe output must be outside the read-only corpus.")
    if destination.exists():
        raise FileExistsError("Use a new output directory.")
    versions = _source_versions()
    source = source_asfp.read_bytes()
    root = ET.fromstring(source)
    if root.tag != "functions":
        raise ValueError("Supply a native ASFP functions package, not an APP or isolated task.")
    templates = {
        DialogKind.TEXT: select_task(root, text_task_id, DialogKind.TEXT),
        DialogKind.CHOICE: select_task(root, choice_task_id, DialogKind.CHOICE),
    }
    artifacts = {}
    records = []
    for case in cases():
        name = case.name + ".asfp"
        artifacts[name] = native_probe(case, templates[case.kind])
        program = shell(case)
        markers = ["dialog.before"]
        if case.successful:
            markers.append("dialog.after")
        if case.context == Context.CHILD:
            markers = ["caller.before", *markers, *(["caller.after"] if case.successful else [])]
        elif case.context == Context.LOOP:
            markers = ["caller.before", "loop.before", *markers]
            if case.successful:
                markers += [
                    "loop.after",
                    "loop.before",
                    "dialog.before",
                    "dialog.after",
                    "loop.after",
                    "loop.finished",
                    "caller.after",
                ]
        records.append(
            {
                "name": case.name,
                "kind": case.kind.value,
                "context": case.context.value,
                "action": case.action.value,
                "actions_required": case.actions_required,
                "entry_function": next(f.name for f in program.functions if f.node_id == program.entry_function_id),
                "semantic_marker_order": markers,
                "successful_control": case.successful,
                "native_success_value": {Action.TEXT: "S-001", Action.EMPTY: "", Action.YES: 1, Action.NO: 0}.get(
                    case.action
                ),
                "semantic_requirement": "continue exactly once per accepted response"
                if case.successful
                else "terminate before value/after/caller markers",
                "executor_status": "pending",
                "files": [{"path": name, "sha256": hashlib.sha256(artifacts[name]).hexdigest()}],
            }
        )
    manifest = {
        "probe_format": 1,
        "suite": "dialog_results",
        "executor_status": "pending",
        "semantic_equivalence": "unverified",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "package_versions": versions,
        "candidate_target": AutoSuiteTarget().target_id,
        "native_source": {
            "filename": source_asfp.name,
            "sha256": hashlib.sha256(source).hexdigest(),
            "product_version": root.get("productversion"),
            "profile": None,
        },
        "selected_tasks": [
            {
                "kind": kind.value,
                "id": template.findtext("id"),
                "parsed_xml_sha256": hashlib.sha256(ET.tostring(template, encoding="utf-8")).hexdigest(),
            }
            for kind, template in templates.items()
        ],
        "host_command_options": ["/r", "/sim", "100", "/c"],
        "host_after_marker_required": True,
        "cases": records,
    }
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in artifacts.items():
        (destination / name).write_bytes(content)
    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-asfp", required=True, type=Path)
    parser.add_argument("--text-task-id", required=True)
    parser.add_argument("--choice-task-id", required=True)
    options = parser.parse_args()
    try:
        generate(
            options.output_dir,
            source_asfp=options.source_asfp,
            text_task_id=options.text_task_id,
            choice_task_id=options.choice_task_id,
        )
    except (ValueError, OSError, ET.ParseError) as error:
        parser.error(str(error))
    print(f"Generated {len(cases())} native dialog probes; Executor status: pending.")


if __name__ == "__main__":
    main()
