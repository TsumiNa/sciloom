"""Python list programs retain list intent and agree with reference IR execution."""

from typing import Any
from pathlib import Path

import pytest

from sciloom import Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import ListGet, ListLength, ListLiteral, ListSet, ListType, ScalarType, from_json, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.contrib.autosuite import AutoSuiteTarget


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


def test_scale_values_preserves_high_level_lists_and_copy_semantics():
    function = ScaleValues()
    program = function.to_ir()
    kinds = {type(node) for node, _ in iter_nodes(program)}
    assert {ListLength, ListSet} <= kinds
    assert program.functions[0].variables[0].type == ListType(element_type=ScalarType.REAL)
    values = [1.0, 2.0, 3.0]
    result = Interpreter(from_json(to_json(program))).run(inputs={"values": values, "factor": 2.5})
    assert result.outputs["result"] == (2.5, 5.0, 7.5)
    assert values == [1.0, 2.0, 3.0]
    assert function.batch_size == 8
    assert Interpreter(program).run(inputs={"values": [], "factor": 2.0}).outputs["result"] == ()
    with pytest.raises(CompilationError, match="unsupported_list"):
        function.compile(target=AutoSuiteTarget())


def test_python_and_direct_ir_edit_programs_agree():
    direct = from_json((Path(__file__).resolve().parents[3] / "examples/developer/list_ir.json").read_text())

    class EditCopy(Function):
        values: Input[list[float]]
        result: Output[list[float]]

        @runtime
        def run(self):
            self.result = self.values
            self.result[0] = 9.0

    inputs = {"values": [1.0, 2.0]}
    assert Interpreter(EditCopy().to_ir()).run(inputs=inputs).outputs == Interpreter(direct).run(inputs=inputs).outputs


def test_schema_copies_mutable_defaults_and_sessions_preserve_separate_state():
    defaults = [1]

    class Counter(Function):
        values: Var[list[int]] = defaults
        result: Output[list[int]]

        @runtime
        def run(self):
            self.values[0] += 1
            self.result = self.values

    defaults.append(100)
    defaults[0] = 99
    assert Counter.model_fields["values"].default == (1,)
    first, second = Counter(), Counter()
    a, b = Interpreter(first.to_ir()), Interpreter(second.to_ir())
    snapshot = a.run()
    assert snapshot.outputs["result"] == (2,)
    assert a.run().outputs["result"] == (3,)
    assert b.run().outputs["result"] == (2,)
    assert snapshot.outputs["result"] == (2,)
    assert first.model_fields["values"].default == (1,)


def test_empty_defaults_runtime_literals_calls_and_output_isolation():
    class Child(Function):
        values: Input[list[float]]
        result: Output[list[float]]

        @runtime
        def run(self):
            self.result = self.values

    class Caller(Function):
        factor: Input[float]
        values: Var[list[float]] = []
        original: Output[list[float]]
        changed: Output[list[float]]
        empty: Output[list[float]]

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self):
            self.values = [1, self.factor * 2]
            self.original = self.child(self.values)
            self.values[0] = 9
            self.changed = self.values
            self.empty = self.child([])

    program = Caller().to_ir()
    assert any(isinstance(node, ListLiteral) for node, _ in iter_nodes(program))
    assert Interpreter(program).run(inputs={"factor": 3.0}).outputs == {"original": (1.0, 6.0), "changed": (9.0, 6.0), "empty": ()}


def test_inherited_list_defaults_are_reused_without_renormalization():
    class Base(Function):
        values: Var[list[int]] = [1]
        result: Output[list[int]]

        @runtime
        def run(self):
            self.values[0] += 1
            self.result = self.values

    class Child(Base):
        pass

    class Redeclared(Base):
        values: Var[list[int]]

    for cls in (Child, Redeclared):
        assert cls.model_fields["values"].default == (1,)
        assert Interpreter(cls().to_ir()).run().outputs == {"result": (2,)}
    with pytest.raises(IRValidationError, match="Overriding runtime schema"):
        class Changed(Base):
            values: Var[list[int]] = [2]


def test_distinct_composed_instances_have_independent_list_state():
    class Counter(Function):
        values: Var[list[int]] = [0]
        result: Output[list[int]]
        @runtime
        def run(self):
            self.values[0] += 1
            self.result = self.values

    class Pair(Function):
        first: Output[list[int]]
        repeated: Output[list[int]]
        other: Output[list[int]]
        def __init__(self):
            self.one, self.two = Counter(), Counter()
        @runtime
        def run(self):
            self.first = self.one()
            self.repeated = self.one()
            self.other = self.two()

    assert Interpreter(Pair().to_ir()).run().outputs == {"first": (1,), "repeated": (2,), "other": (1,)}


def test_boolean_and_physical_lists_keep_their_element_meaning():
    class Values(Function):
        flags: Var[list[bool]] = [False]
        speeds: Var[list[RotationalSpeed]] = [60 * rpm]
        flag_output: Output[list[bool]]
        speed_output: Output[list[RotationalSpeed]]

        @runtime
        def run(self):
            self.flags[0] = True
            self.speeds[0] = 120 * rpm
            self.flag_output = self.flags
            self.speed_output = self.speeds

    assert Interpreter(Values().to_ir()).run().outputs == {"flag_output": (True,), "speed_output": (120 * rpm,)}


@pytest.mark.parametrize("annotation,default", [
    (list, []), (list[Any], []), (list[list[int]], []), (list[int], [True]),
    (list[float], [False]), (list[bool], [1]), (list[float], [float("nan")]),
    (list[int], (1,)), (list[RotationalSpeed], [1.0]),
])
def test_list_schema_rejects_unsupported_types_and_defaults(annotation, default):
    with pytest.raises(IRValidationError, match="class_schema"):
        type("Invalid", (Function,), {"__annotations__": {"values": Var[annotation]}, "values": default})


def test_bad_element_literal_and_boolean_index_fail_semantic_validation():
    class BadElements(Function):
        values: Output[list[float]]
        @runtime
        def run(self):
            self.values = [1.0, True]

    class BadIndex(Function):
        values: Var[list[int]] = [1]
        @runtime
        def run(self):
            self.values[False] = 2

    for function, code in [(BadElements(), "list_element_type"), (BadIndex(), "index_type")]:
        with pytest.raises(IRValidationError, match=code):
            function.to_ir()


@pytest.mark.parametrize("index", [-1, 1])
def test_python_index_writes_do_not_wrap_or_resize(index):
    class InvalidIndex(Function):
        values: Var[list[int]] = [1]
        def __init__(self):
            self.index = index
        @runtime
        def run(self):
            self.values[self.index] = 2

    with pytest.raises(ExecutionError, match="index_bounds"):
        Interpreter(InvalidIndex().to_ir()).run()


def test_shadowed_len_is_not_silently_treated_as_a_builtin():
    len = lambda values: 99
    class Shadowed(Function):
        values: Input[list[int]]
        result: Output[int]
        @runtime
        def run(self):
            self.result = len(self.values)

    with pytest.raises(IRValidationError, match="shadowed"):
        Shadowed().to_ir()


def test_length_assignment_index_reads_and_inferred_nonempty_literal():
    class Read(Function):
        values: Input[list[float]]
        length: Output[int]
        first: Output[float]
        literal_length: Output[int]
        @runtime
        def run(self):
            self.length = len(self.values)
            self.first = self.values[0]
            self.literal_length = len([1, 2.0])

    program = Read().to_ir()
    assert any(isinstance(node, ListGet) for node, _ in iter_nodes(program))
    assert Interpreter(program).run(inputs={"values": [7.0]}).outputs == {"length": 1, "first": 7.0, "literal_length": 2}


def test_list_methods_and_slicing_remain_unsupported():
    class Append(Function):
        values: Var[list[int]] = []
        @runtime
        def run(self):
            self.values.append(1)

    class Slice(Function):
        values: Input[list[int]]
        result: Output[list[int]]
        @runtime
        def run(self):
            self.result = self.values[:]

    class Pop(Function):
        values: Var[list[int]] = [1]
        @runtime
        def run(self):
            self.values.pop()

    class Remove(Function):
        values: Var[list[int]] = [1]
        @runtime
        def run(self):
            self.values.remove(1)

    class Clear(Function):
        values: Var[list[int]] = [1]
        @runtime
        def run(self):
            self.values.clear()

    class Comprehension(Function):
        values: Input[list[int]]
        result: Output[list[int]]
        @runtime
        def run(self):
            self.result = [x for x in self.values]

    class Iterate(Function):
        values: Input[list[int]]
        result: Output[int]
        @runtime
        def run(self):
            for x in self.values:
                self.result = x

    for function in (Append(), Slice(), Pop(), Remove(), Clear(), Comprehension(), Iterate()):
        with pytest.raises(IRValidationError, match="python_subset"):
            function.to_ir()


def test_indexed_function_output_binding_is_explicitly_unsupported():
    class Child(Function):
        value: Output[int]
        @runtime
        def run(self):
            self.value = 1

    class Caller(Function):
        values: Var[list[int]] = [0]
        def __init__(self):
            self.child = Child()
        @runtime
        def run(self):
            self.values[0] = self.child()

    with pytest.raises(IRValidationError, match="whole variables"):
        Caller().to_ir()


def test_empty_list_without_a_declared_element_context_is_rejected():
    class UntypedEmpty(Function):
        result: Output[int]
        @runtime
        def run(self):
            self.result = len([])

    with pytest.raises(IRValidationError, match="declared list element type"):
        UntypedEmpty().to_ir()
