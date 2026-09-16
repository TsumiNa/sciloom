"""Unverified guards remain unavailable through composition and JSON entry points."""

import pytest

from sciloom import Function, Input, Output, Var, Volume, mL, runtime, text
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom.core.ir.traversal import iter_nodes
from .target import AutoSuiteTarget


class GuardedRead(Function):
    values: Input[list[str]]
    result: Output[str]

    @runtime
    def run(self) -> None:
        self.result = self.values[0]


class GuardedCaller(Function):
    values: Input[list[str]]
    result: Output[str]

    def __init__(self):
        self.child = GuardedRead()

    @runtime
    def run(self) -> None:
        self.result = self.child(self.values)


class GuardedLoop(Function):
    values: Input[list[str]]
    result: Output[str]
    running: Var[bool] = True

    @runtime
    def run(self) -> None:
        self.running = True
        while self.running:
            self.result = self.values[0]
            self.running = False


@pytest.mark.parametrize("model", [GuardedRead, GuardedCaller, GuardedLoop])
def test_guard_gate_cannot_be_bypassed_by_composition_or_json(model):
    authored = model().to_ir()
    canonical = to_json(authored)
    for program in (authored, from_json(canonical)):
        assert Interpreter(program).run(inputs={"values": ["A"]}).outputs["result"] == "A"
        expected_paths = {node.node_id: path for node, path in iter_nodes(program)}
        with pytest.raises(CompilationError) as error:
            compile_ir(program, target=AutoSuiteTarget())
        guards = [d for d in error.value.diagnostics if d.code == "unsupported_runtime_guard"]
        assert len(guards) == 1
        diagnostic = guards[0]
        assert diagnostic.path == expected_paths[diagnostic.node_id]
        assert diagnostic.source.path == __file__
        assert diagnostic.source.line > 0
    assert to_json(authored) == canonical


def test_dynamic_split_and_quantity_division_keep_the_same_pending_gate():
    class Split(Function):
        value: Input[str]
        index: Input[int]
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = text.split_part(self.value, ":", self.index)

    class Divide(Function):
        amount: Input[Volume]
        divisor: Input[float]
        result: Output[Volume]

        @runtime
        def run(self) -> None:
            self.result = self.amount / self.divisor

    for model, inputs, expected in (
        (Split(), {"value": "A:B", "index": 1}, "B"),
        (Divide(), {"amount": 2 * mL, "divisor": 2.0}, 1 * mL),
    ):
        program = model.to_ir()
        assert Interpreter(program).run(inputs=inputs).outputs["result"] == expected
        with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
            compile_ir(from_json(to_json(program)), target=AutoSuiteTarget())
