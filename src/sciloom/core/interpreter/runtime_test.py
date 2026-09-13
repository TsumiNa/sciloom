"""Semantic execution tests independent of target serialization."""

import subprocess
import sys

import pytest

from sciloom import Function, Input, Output, Var, runtime
from sciloom.core.diagnostics import ExecutionError
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from .runtime import ExecutionConfig, Interpreter


class Accumulator(Function):
    amount: Input[int]
    total: Var[int] = 0
    result: Output[int]

    @runtime
    def run(self):
        self.total += self.amount
        self.result = self.total


def independent_accumulator():
    return Program(
        entry_function_id="acc",
        functions=(
            FunctionIR(
                node_id="acc",
                name="Accumulator",
                variables=(
                    Variable(
                        node_id="amount",
                        owner_id="acc",
                        name="amount",
                        role=VariableRole.INPUT,
                        type=ScalarType.INTEGER,
                    ),
                    Variable(
                        node_id="total",
                        owner_id="acc",
                        name="total",
                        role=VariableRole.INTERNAL,
                        type=ScalarType.INTEGER,
                        initial=Literal(node_id="zero", type=ScalarType.INTEGER, value=0),
                    ),
                    Variable(
                        node_id="out", owner_id="acc", name="result", role=VariableRole.OUTPUT, type=ScalarType.INTEGER
                    ),
                ),
                body=(
                    Assignment(
                        node_id="add",
                        target=Reference(node_id="dst", symbol_id="total"),
                        value=Binary(
                            node_id="sum",
                            op=BinaryOp.ADD,
                            left=Reference(node_id="old", symbol_id="total"),
                            right=Reference(node_id="input", symbol_id="amount"),
                        ),
                    ),
                    Assignment(
                        node_id="copy",
                        target=Reference(node_id="output", symbol_id="out"),
                        value=Reference(node_id="new", symbol_id="total"),
                    ),
                ),
            ),
        ),
    )


def test_python_direct_and_json_ir_agree_across_calls():
    instance = Accumulator()
    before = vars(instance).copy()
    programs = (instance.to_ir(), independent_accumulator(), from_json(to_json(independent_accumulator())))
    for program in programs:
        session = Interpreter(program)
        first = session.run(inputs={"amount": 3})
        assert first.outputs == {"result": 3}
        assert session.run(inputs={"amount": 2}).outputs == {"result": 5}
        assert first.outputs == {"result": 3}  # detached snapshots
        assert Interpreter(program).run(inputs={"amount": 2}).outputs == {"result": 2}
        with pytest.raises(TypeError):
            first.outputs["result"] = 99
        with pytest.raises(TypeError):
            first.state[program.entry_function_id]["total"] = 99
    assert vars(instance) == before


def test_shared_and_distinct_instances_have_correct_state():
    class Pair(Function):
        result: Output[int]
        other: Var[int] = 0

        def __init__(self, shared):
            self.first = Accumulator()
            self.second = self.first if shared else Accumulator()

        @runtime
        def run(self):
            self.result = self.first(amount=1)
            self.other = self.second(amount=2)
            self.result += self.other

    assert Interpreter(Pair(True).to_ir()).run().outputs == {"result": 4}
    assert Interpreter(Pair(False).to_ir()).run().outputs == {"result": 3}


def test_recursive_frames_are_independent():
    class Factorial(Function):
        n: Input[int]
        result: Output[int]

        def __init__(self):
            self.again = self

        @runtime
        def run(self):
            if self.n <= 1:
                self.result = 1
            else:
                self.result = self.again(n=self.n - 1)
                self.result *= self.n

    program = Factorial().to_ir()
    assert Interpreter(program).run(inputs={"n": 5}).outputs == {"result": 120}
    with pytest.raises(ExecutionError, match="call_depth"):
        Interpreter(program, config=ExecutionConfig(max_call_depth=2)).run(inputs={"n": 5})


def test_loop_and_short_circuit_do_not_execute_dead_expressions():
    class Safe(Function):
        count: Var[int] = 0
        answer: Output[bool]

        @runtime
        def run(self):
            while self.count < 3:
                self.count += 1
            self.answer = False and (1 / 0 > 0)
            self.answer = True or (1 / 0 > 0)

    result = Interpreter(Safe().to_ir()).run()
    assert result.outputs == {"answer": True}
    assert result.state["fn:0"]["fn:0:var:count"] == 3


def test_empty_infinite_loop_is_bounded():
    class Infinite(Function):
        @runtime
        def run(self):
            while True:
                pass

    with pytest.raises(ExecutionError, match="step_limit"):
        Interpreter(Infinite().to_ir(), config=ExecutionConfig(max_steps=20)).run()


def test_output_frames_do_not_keep_previous_values():
    class Maybe(Function):
        enabled: Input[bool]
        result: Output[int]

        @runtime
        def run(self):
            if self.enabled:
                self.result = 1

    session = Interpreter(Maybe().to_ir())
    assert session.run(inputs={"enabled": True}).outputs["result"] == 1
    with pytest.raises(ExecutionError, match="missing_output"):
        session.run(inputs={"enabled": False})


def test_uninitialized_read_and_division_failure_have_locations():
    class Uninitialized(Function):
        result: Output[int]

        @runtime
        def run(self):
            self.result += 1

    with pytest.raises(ExecutionError, match="uninitialized_read") as error:
        Interpreter(Uninitialized().to_ir()).run()
    assert error.value.diagnostics[0].source.path.endswith("runtime_test.py")

    class Division(Function):
        divisor: Input[float]
        result: Output[float]

        @runtime
        def run(self):
            self.result = 1 / self.divisor

    session = Interpreter(Division().to_ir())
    with pytest.raises(ExecutionError, match="numeric_error"):
        session.run(inputs={"divisor": 0})
    assert session.run(inputs={"divisor": 2}).outputs == {"result": 0.5}
    with pytest.raises(ExecutionError, match="numeric_error"):
        session.run(inputs={"divisor": float("inf")})


@pytest.mark.parametrize("inputs", [{"amount": True}, {"amount": 1.2}, {}, {"extra": 1}])
def test_inputs_are_typed_and_complete(inputs):
    with pytest.raises(ExecutionError):
        Interpreter(independent_accumulator()).run(inputs=inputs)


@pytest.mark.parametrize("config", [{"max_steps": 0}, {"max_steps": True}, {"max_call_depth": 101}])
def test_invalid_execution_budget(config):
    with pytest.raises(ValueError):
        ExecutionConfig(**config)


def test_json_ir_executes_without_frontend_or_backend_imports():
    document = to_json(independent_accumulator())
    script = """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.dsl", "sciloom.contrib")):
            raise ImportError("DSL and equipment targets are forbidden")
sys.meta_path.insert(0, Block())
from sciloom.core.ir import from_json
from sciloom.core.interpreter import Interpreter
assert Interpreter(from_json(sys.stdin.read())).run(inputs={"amount": 7}).outputs == {"result": 7}
"""
    subprocess.run([sys.executable, "-c", script], input=document, text=True, check=True)


def test_json_v1_is_not_silently_upgraded():
    from sciloom.core.ir import IRValidationError, from_dict, to_dict

    document = to_dict(independent_accumulator())
    document["format_version"] = 1
    with pytest.raises(IRValidationError, match="format_version"):
        from_dict(document)


def test_faults_preserve_prior_state_writes():
    class Partial(Function):
        divisor: Input[float]
        count: Var[int] = 0
        result: Output[float]

        @runtime
        def run(self):
            self.count += 1
            self.result = self.count / self.divisor

    session = Interpreter(Partial().to_ir())
    with pytest.raises(ExecutionError, match="numeric_error"):
        session.run(inputs={"divisor": 0})
    assert session.run(inputs={"divisor": 1}).outputs == {"result": 2.0}
