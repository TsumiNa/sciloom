"""Array evidence and scheduling checks; the wire model is not a vendor Executor."""

import ast
import gzip
import importlib
import operator
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sciloom import Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from .conftest import CORPUS, requires_corpus
from .target import AutoSuiteTarget

ROOT = Path(__file__).resolve().parents[4]
EXTRACTED = CORPUS / "extracted/latest_app/functions"


class ScaleValues(Function):
    """Copy and scale values using ordinary Python list expressions."""

    values: Input[list[float]]
    factor: Input[float]
    result: Output[list[float]]
    index: Var[int] = 0
    batch_size: int = 8

    @runtime
    def run(self) -> None:
        self.result = self.values
        self.index = 0
        while self.index < len(self.result):
            self.result[self.index] *= self.factor
            self.index += 1


class WireModel:
    """Execute only the emitted task subset under explicitly assumed wire semantics.

    Array parameter binding deliberately aliases; whole-array Set Variable copies.
    Indexed writes deliberately grow; reads fault outside the array. This stresses
    SciLoom's isolation and guards, without claiming actual AutoSuite acceptance.
    """

    def __init__(self, content):
        self.root = ET.fromstring(content)
        self.functions = {f.findtext("id"): f for f in self.root}
        self.state = {}
        self.steps = 0

    def expression(self, text, frame):
        text = re.sub(r"(?<![<>=!])=(?!=)", "==", text.replace("<>", "!="))
        operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
        }

        def visit(node):
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                return {"true": True, "false": False}[node.id] if node.id in ("true", "false") else frame[node.id]
            if isinstance(node, ast.BinOp):
                return operations[type(node.op)](visit(node.left), visit(node.right))
            if isinstance(node, ast.Compare):
                assert len(node.ops) == 1
                return operations[type(node.ops[0])](visit(node.left), visit(node.comparators[0]))
            if isinstance(node, ast.UnaryOp):
                return {ast.Not: operator.not_, ast.USub: operator.neg}[type(node.op)](visit(node.operand))
            if isinstance(node, ast.Call):
                assert isinstance(node.func, ast.Name) and node.func.id == "ArraySize"
                return len(visit(node.args[0]))
            if isinstance(node, ast.Subscript):
                values, index = visit(node.value), visit(node.slice)
                if type(index) is not int or index < 0 or index >= len(values):
                    raise IndexError(index)
                return values[index]
            raise AssertionError(ast.dump(node))

        return visit(ast.parse(text, mode="eval").body)

    def run(self, inputs=None, function=None):
        function = self.root[0] if function is None else function
        frame = dict(inputs or {})
        self.tasks(function.find("components"), frame)
        return {
            item.findtext("variablename"): frame[item.findtext("variablename")]
            for item in function.find("functiondata/outputs")
            if item.tag.startswith("item")
        }

    def tasks(self, tasks, frame):
        for task in tasks:
            self.steps += 1
            assert self.steps < 10000, "wire model loop did not terminate"
            kind = task.attrib["typeid"]
            if kind.endswith("SATaskSetVariable.1"):
                name = task.findtext("variablename")
                value = self.expression(task.findtext("expressiontext"), frame)
                index = task.findtext("elementnumber")
                if task.findtext("elementselectmode") == "4":
                    frame[name] = list(value)
                elif index:
                    index = self.expression(index, frame)
                    assert index >= 0
                    frame[name].extend([0] * max(0, index + 1 - len(frame[name])))
                    frame[name][index] = value
                else:
                    frame[name] = value
            elif kind.endswith("SAMacroTask.1"):
                local = self.state.setdefault(task.findtext("id"), {})
                for variable in task.find("variables"):
                    name = variable.findtext("name")
                    if name not in local:
                        if variable.findtext("array") == "1":
                            local[name] = [
                                float(v.findtext("value")) if v.findtext("type") == "5" else int(v.findtext("value"))
                                for v in variable.find("values")
                                if v.tag.startswith("value")
                            ]
                        else:
                            text = variable.findtext("value/value")
                            local[name] = float(text) if variable.findtext("value/type") == "5" else int(text)
                    frame[name] = local[name]
                mode = task.findtext("conditiontype")
                if task.findtext("multicondition") == "1":
                    for branch in task.find("tasks"):
                        if branch.findtext("conditiontype") == "2" or self.expression(
                            branch.findtext("condition"), frame
                        ):
                            self.tasks(branch.find("components"), frame)
                            break
                elif mode == "2":
                    while self.expression(task.findtext("conditionwhile"), frame):
                        self.tasks(task.find("tasks"), frame)
                elif mode != "1" or self.expression(task.findtext("conditionif"), frame):
                    self.tasks(task.find("tasks"), frame)
                for name in local:
                    local[name] = frame[name]
            elif kind.endswith("SATaskExecuteFunction.1"):
                callee = self.functions[task.findtext("functionid")]
                declarations = {
                    p.findtext("id"): p.findtext("variablename")
                    for p in callee.findall("functiondata/inputs/*")
                    if p.tag.startswith("item")
                }
                arguments = {}
                for item in task.find("functiondata/inputs"):
                    if item.tag.startswith("item"):
                        arguments[declarations[item.findtext("id")]] = (
                            frame[item.findtext("variablename")]
                            if item.findtext("isarray") == "1"
                            else self.expression(item.findtext("expression"), frame)
                        )
                outputs = self.run(arguments, callee)
                declarations = {
                    p.findtext("id"): p.findtext("variablename")
                    for p in callee.findall("functiondata/outputs/*")
                    if p.tag.startswith("item")
                }
                for item in task.find("functiondata/outputs"):
                    if item.tag.startswith("item"):
                        frame[item.findtext("variablename")] = outputs[declarations[item.findtext("id")]]
            else:
                raise AssertionError(kind)


def compiled(function):
    result = function.compile(target=AutoSuiteTarget())
    assert compile_ir(from_json(to_json(result.semantic_ir)), target=AutoSuiteTarget()).artifact == result.artifact
    ids = [e.text for e in ET.fromstring(result.artifact.content).iter("id")]
    # Parameter IDs intentionally repeat in calls; task IDs must not.
    task_ids = [e.findtext("id") for e in ET.fromstring(result.artifact.content).iter() if "typeid" in e.attrib]
    assert len(set(task_ids)) == len(task_ids)
    assert ids
    return result


@pytest.mark.parametrize(
    "module,inputs,expected",
    [
        ("scale_values", {"values": [1.0, 2.0, 3.0], "factor": 2.5}, {"result": [2.5, 5.0, 7.5]}),
        ("scale_values", {"values": [], "factor": 2.5}, {"result": []}),
        ("non_zero_array_min", {"values": [0.0, 4.0, 2.0, 0.0]}, {"minimum": 2.0}),
        ("non_zero_array_min", {"values": []}, {"minimum": 999999.0}),
        ("non_zero_array_min", {"values": [0.0, -1.0, 1e-9]}, {"minimum": 999999.0}),
    ],
)
def test_author_examples_and_wire_schedule_agree_with_ir(monkeypatch, module, inputs, expected):
    monkeypatch.syspath_prepend(str(ROOT))
    imported = importlib.import_module(f"examples.{module}")
    cls = imported.ScaleValues if module == "scale_values" else imported.NonZeroArrayMin
    result = compiled(cls())
    before = {k: list(v) if isinstance(v, list) else v for k, v in inputs.items()}
    machine = WireModel(result.artifact.content)
    assert machine.run(inputs) == expected
    assert machine.run(inputs) == expected
    assert inputs == before
    reference = Interpreter(result.semantic_ir).run(inputs=inputs).outputs
    assert {k: list(v) if isinstance(v, tuple) else v for k, v in reference.items()} == expected


def test_calls_copy_inputs_outputs_literals_and_persistent_state():
    class Child(Function):
        values: Input[list[int]]
        result: Output[list[int]]
        state: Var[list[int]] = [0]

        @runtime
        def run(self):
            self.values[0] += 10
            self.state[0] += 1
            self.result = [self.values[0], self.state[0]]

    class Caller(Function):
        values: Var[list[int]] = [1]
        first: Output[list[int]]
        second: Output[list[int]]
        original: Output[list[int]]

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self):
            self.first = self.child(self.values)
            self.second = self.child([2])
            self.first[0] = 99
            self.original = self.values

    result = compiled(Caller())
    machine = WireModel(result.artifact.content)
    assert machine.run() == {"first": [99, 1], "second": [12, 2], "original": [1]}
    assert machine.run() == {"first": [99, 3], "second": [12, 4], "original": [1]}
    root = machine.root
    for call in root.findall(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']"):
        assert call.findtext("functiondata/inputs/item0/isarray") == "1"
        assert not call.findtext("functiondata/inputs/item0/expression")
        assert call.findtext("functiondata/inputs/item0/variablename").startswith("sciloom_tmp_")


@pytest.mark.parametrize("index", [-1, 1, 100])
def test_checked_write_faults_without_autogrowth(index):
    class Bad(Function):
        values: Input[list[int]]

        def __init__(self):
            self.index = index

        @runtime
        def run(self):
            self.values[self.index] = 9

    values = [1]
    with pytest.raises(IndexError):
        WireModel(compiled(Bad()).artifact.content).run({"values": values})
    assert values == [1]


def test_while_condition_checks_run_on_every_retest():
    class Scan(Function):
        values: Var[list[int]] = [1, 1, 0]
        index: Var[int] = 0
        result: Output[int]

        @runtime
        def run(self):
            self.index = 0
            while self.values[self.index] > 0:
                self.index += 1
            self.result = self.index

    result = compiled(Scan())
    assert WireModel(result.artifact.content).run() == {"result": 2}
    assert Interpreter(result.semantic_ir).run().outputs == {"result": 2}


def test_rhs_and_augmented_index_fault_order():
    class Simple(Function):
        values: Var[list[float]] = [1.0]

        @runtime
        def run(self):
            self.values[-1] = 1.0 / 0.0

    class Augmented(Function):
        values: Var[list[float]] = [1.0]

        @runtime
        def run(self):
            self.values[-1] += 1.0 / 0.0

    with pytest.raises(ZeroDivisionError):
        WireModel(compiled(Simple()).artifact.content).run()
    with pytest.raises(IndexError):
        WireModel(compiled(Augmented()).artifact.content).run()


@requires_corpus
def test_array_encoding_matches_raw_evidence_and_composed_scalar_types():
    class Values(Function):
        integers: Var[list[int]] = []
        reals: Var[list[float]] = [1.0, 2.5]
        flags: Var[list[bool]] = [False, True]
        speeds: Var[list[RotationalSpeed]] = [60 * rpm]

        @runtime
        def run(self):
            pass

    root = ET.fromstring(compiled(Values()).artifact.content)
    variables = {v.findtext("name"): v for v in root.iter("variable")}
    raw = ET.fromstring(gzip.decompress((CORPUS / "app/Suzuki-Miyaura-automation.app").read_bytes()))
    integer = next(v for v in raw.iter("variable") if v.findtext("name") == "int_base_array")
    for path in ("values/count", "type", "siunit", "unit", "array", "constant"):
        assert variables["integers"].findtext(path) == integer.findtext(path)
    assert variables["reals"].findtext("values/value1/type") == "5"
    assert variables["reals"].findtext("values/value1/value") == "2.5"
    assert variables["flags"].findtext("values/value1/type") == "11"
    assert variables["flags"].findtext("values/value1/value") == "-1"
    assert variables["speeds"].findtext("values/value0/value") == "1"
    assert variables["speeds"].findtext("siunit") == "1/s"
    assert variables["speeds"].findtext("unit") == "rpm"


@requires_corpus
def test_whole_copy_and_indexed_write_fields_match_observed_modes():
    root = ET.fromstring(compiled(ScaleValues()).artifact.content)
    raw = ET.fromstring(gzip.decompress((CORPUS / "app/config20260902_2.app").read_bytes()))
    whole = next(n for n in raw.iter() if n.findtext("elementselectmode") == "4")
    generated = next(n for n in root.iter() if n.findtext("elementselectmode") == "4")
    assert [c.tag for c in generated] == [c.tag for c in whole]
    for tag in ("elementselectmode", "elementnumber", "numberofelements", "startindex", "clearvariable"):
        assert generated.findtext(tag) == whole.findtext(tag)
    raw_index = ET.parse(EXTRACTED / "44_Set ISynth Drawer State.asfp")
    indexed = next(n for n in raw_index.iter() if n.findtext("variablename") == "g_drawer_state")
    generated = next(n for n in root.iter() if n.findtext("elementnumber"))
    assert generated.findtext("elementselectmode") == indexed.findtext("elementselectmode") == "0"
    assert "[" not in generated.findtext("variablename")


def test_array_outputs_require_definite_assignment():
    class Unset(Function):
        values: Output[list[int]]

        @runtime
        def run(self):
            self.values[0] = 1

    class Conditional(Function):
        enabled: Input[bool]
        values: Output[list[int]]

        @runtime
        def run(self):
            if self.enabled:
                self.values = []

    for function in (Unset(), Conditional()):
        with pytest.raises(CompilationError, match="list_output_initialization"):
            function.compile(target=AutoSuiteTarget())


def test_empty_output_replaces_previous_call_value_and_typed_index_reads_compile():
    class Typed(Function):
        enabled: Input[bool]
        flags: Input[list[bool]]
        speeds: Input[list[RotationalSpeed]]
        result: Output[list[RotationalSpeed]]

        @runtime
        def run(self):
            if self.enabled:
                self.result = [self.speeds[0]]
                if self.flags[0]:
                    self.result[0] = 120 * rpm
            else:
                self.result = []

    result = compiled(Typed())
    machine = WireModel(result.artifact.content)
    assert machine.run({"enabled": True, "flags": [True], "speeds": [1.0]}) == {"result": [2.0]}
    assert machine.run({"enabled": False, "flags": [], "speeds": []}) == {"result": []}


def test_private_ids_and_names_do_not_collide_with_ir_supplied_symbols():
    from sciloom.core.ir import FunctionIR, ListType, Program, ScalarType, Variable, VariableRole

    variable = Variable(
        node_id="generated:1",
        owner_id="f",
        name="sciloom_tmp_2",
        role=VariableRole.INPUT,
        type=ListType(element_type=ScalarType.INTEGER),
    )
    program = Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="Collision", variables=(variable,)),)
    )
    root = ET.fromstring(compile_ir(program, target=AutoSuiteTarget()).artifact.content)
    private = root.findtext(".//variable/name")
    assert private != "sciloom_tmp_2"
    assert root.findtext(".//*[@typeid='Chemspeed.SATaskSetVariable.1']/expressiontext") == "sciloom_tmp_2"
