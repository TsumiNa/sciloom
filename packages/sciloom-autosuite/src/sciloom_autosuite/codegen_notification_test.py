"""OK dialog evidence and capture scheduling, independent of Executor acceptance."""

import gzip
import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Var, notify, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter, QueuedAcknowledgements, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .target import AutoSuiteTarget


class Notifications(Function):
    label: Input[str]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.index = 0
        while self.index < 2:
            notify(self.label + " ready?")
            self.label = "next"
            self.index += 1


class DialogWire(WireModel):
    """Model message capture after an assumed OK; does not test actual UI blocking."""

    def __init__(self, content):
        super().__init__(content)
        self.messages = []

    def tasks(self, tasks, frame):
        for task in tasks:
            if task.attrib["typeid"] == "Chemspeed.SATaskUserDialog.1":
                self.messages.append(self.expression(task.findtext("message"), frame))
            else:
                super().tasks((task,), frame)


def test_captures_follow_loops_and_match_reference_without_public_temporaries():
    authored = Notifications().to_ir()
    for program in (authored, from_json(to_json(authored))):
        before = to_json(program)
        compiled = compile_ir(program, target=AutoSuiteTarget())
        wire = DialogWire(compiled.artifact.content)
        wire.run({"label": "A"})
        environment = ReferenceEnvironment(acknowledgements=QueuedAcknowledgements([True, True]))
        reference = Interpreter(program, environment=environment).run(inputs={"label": "A"})
        assert wire.messages == [e.message for e in reference.events] == ["A ready?", "next ready?"]
        assert to_json(program) == before
        assert all("sciloom_tmp" not in v.name for f in compiled.specialized_ir.functions for v in f.variables)


def test_dialog_has_no_timeout_result_or_followup_pause_and_captures_once():
    class Constant(Function):
        @runtime
        def run(self) -> None:
            notify("Samples ready.")

    root = ET.fromstring(Constant().compile(target=AutoSuiteTarget()).artifact.content)
    macro = root.find(".//*[@typeid='Chemspeed.SAMacroTask.1']")
    assert len(macro.findall("variables/variable")) == 1
    capture, dialog = list(macro.find("tasks"))
    assert capture.attrib["typeid"] == "Chemspeed.SATaskSetVariable.1"
    assert dialog.findtext("message") == capture.findtext("variablename")
    for field, value in {
        "dialogtype": "showmessage",
        "buttonoption": "ok",
        "interpretmessageasexpressionflag": "1",
        "maxwaittimeexpression": "0",
        "defaultpauseafterdialog": "0",
        "resultvariablename": "",
        "timeoutanswerexpression": "",
        "yesokresultexpression": "",
        "noresultexpression": "",
    }.items():
        assert dialog.findtext(field) == value


def test_notification_cannot_hide_unverified_guard():
    class Bounds(Function):
        messages: Input[list[str]]

        @runtime
        def run(self) -> None:
            notify(self.messages[0])

    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        Bounds().compile(target=AutoSuiteTarget())


@pytest.mark.requires_corpus
def test_dialog_fields_and_defaults_match_ok_task_in_primary_app():
    root = ET.fromstring(gzip.decompress(corpus_file("app/config20260909_polymerization.app").read_bytes()))
    native = next(
        t
        for t in root.iter()
        if t.attrib.get("typeid") == "Chemspeed.SATaskUserDialog.1" and t.findtext("buttonoption") == "ok"
    )
    generated = ET.fromstring(Notifications().compile(target=AutoSuiteTarget()).artifact.content).find(
        ".//*[@typeid='Chemspeed.SATaskUserDialog.1']"
    )
    assert [c.tag for c in generated] == [c.tag for c in native]
    for child in native:
        if child.tag not in {"id", "edittime", "message", "description", "name"}:
            assert generated.findtext(child.tag) == (child.text or "")
