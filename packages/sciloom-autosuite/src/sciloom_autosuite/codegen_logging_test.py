"""Log task envelopes and ordered captures, without claiming Executor validation."""

import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Var, Volume, log, mL, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import FunctionIR, Literal, LogValue, Program, ScalarType, from_json, to_json
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .encoding import SCALARS
from .target import AutoSuiteTarget


class LoggingWire(WireModel):
    """Record the emitted native LogData subset under assumed wire semantics."""

    def __init__(self, content):
        super().__init__(content)
        self.logs = []

    def tasks(self, tasks, frame):
        for task in tasks:
            if task.attrib["typeid"] == "Chemspeed.SATaskLogData.1":
                self.logs.append(
                    (
                        task.findtext("resulttype"),
                        self.expression(task.findtext("expressiontext"), frame),
                        self.expression(task.findtext("categorynameexpression"), frame),
                        self.expression(task.findtext("streamnameexpression"), frame),
                    )
                )
            else:
                super().tasks((task,), frame)


class Records(Function):
    amount: Input[Volume]
    category: Input[str]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.index = 0
        while self.index < 2:
            log(self.amount, category=self.category + "_run", stream="volume")
            self.amount = self.amount + 1 * mL
            self.index += 1


def test_log_capture_order_and_snapshot_values_match_reference():
    authored = Records().to_ir()
    for program in (authored, from_json(to_json(authored))):
        before = to_json(program)
        compiled = compile_ir(program, target=AutoSuiteTarget())
        wire = LoggingWire(compiled.artifact.content)
        wire.run({"amount": 1e-6, "category": "recipe"})
        reference = Interpreter(program).run(inputs={"amount": 1 * mL, "category": "recipe"})
        assert wire.logs == [("volume", e.value.m3, e.category, e.stream) for e in reference.events]
        assert [row[1] for row in wire.logs] == [1e-6, 2e-6]
        assert to_json(program) == before
        assert all("sciloom_tmp" not in v.name for f in compiled.specialized_ir.functions for v in f.variables)


@pytest.mark.parametrize(
    "kind,value",
    [
        (ScalarType.INTEGER, 2),
        (ScalarType.REAL, 1.5),
        (ScalarType.BOOLEAN, True),
        (ScalarType.TEXT, "ready"),
        (ScalarType.VOLUME, 1e-6),
        (ScalarType.DURATION, 2.0),
        (ScalarType.ROTATIONAL_SPEED, 5.0),
    ],
)
def test_literal_only_log_has_macro_storage_and_typed_result(kind, value):
    program = Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Record",
                body=(
                    LogValue(
                        node_id="log",
                        value=Literal(node_id="value", type=kind, value=value),
                        category=Literal(node_id="category", type=ScalarType.TEXT, value="recipe"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="value"),
                    ),
                ),
            ),
        ),
    )
    wire = LoggingWire(compile_ir(program, target=AutoSuiteTarget()).artifact.content)
    wire.run()
    assert wire.logs == [(SCALARS[kind].parameter_type, value, "recipe", "value")]
    macro = wire.root.find(".//*[@typeid='Chemspeed.SAMacroTask.1']")
    assert len(macro.findall("variables/variable")) == 3
    tasks = list(macro.find("tasks"))
    assert [t.attrib["typeid"] for t in tasks] == ["Chemspeed.SATaskSetVariable.1"] * 3 + ["Chemspeed.SATaskLogData.1"]
    captured = [t.findtext("variablename") for t in tasks[:3]]
    assert [
        tasks[3].findtext(p) for p in ("expressiontext", "categorynameexpression", "streamnameexpression")
    ] == captured


def test_log_cannot_hide_a_target_guard_requirement():
    class Bounds(Function):
        labels: Input[list[str]]

        @runtime
        def run(self) -> None:
            log(1, category=self.labels[0], stream="value")

    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        Bounds().compile(target=AutoSuiteTarget())


@pytest.mark.requires_corpus
def test_native_log_envelope_matches_latest_function_evidence():
    source = ET.parse(corpus_file("extracted/latest_app/functions/24_Sample and Run GPC.asfp"))
    native = source.find(".//*[@typeid='Chemspeed.SATaskLogData.1']")
    generated = ET.fromstring(Records().compile(target=AutoSuiteTarget()).artifact.content).find(
        ".//*[@typeid='Chemspeed.SATaskLogData.1']"
    )
    assert [c.tag for c in generated] == [c.tag for c in native]
    assert native.findtext("resulttype") == "text"
    assert native.findtext("expressiontext") == "'Start Sampling'"
