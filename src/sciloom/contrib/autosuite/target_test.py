"""Vendor restrictions must not constrain target-independent authoring."""

import pytest

from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import Call, FunctionIR, Program, from_json, to_json, validate
from .target import AutoSuiteTarget


def test_list_ir_compiles_to_array_parameters():
    from sciloom.core.ir import ListType, ScalarType, Variable, VariableRole

    variable = Variable(
        node_id="values",
        owner_id="f",
        name="values",
        role=VariableRole.INPUT,
        type=ListType(element_type=ScalarType.REAL),
    )
    program = Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="ListInput", variables=(variable,)),)
    )
    assert validate(program) == ()
    assert b"<isarray>1</isarray>" in compile_ir(program, target=AutoSuiteTarget()).artifact.content


@pytest.mark.parametrize("indirect", [False, True])
def test_recursion_is_legal_ir_but_illegal_for_autosuite(indirect):
    first = FunctionIR(node_id="a", name="A", body=(Call(node_id="call:a", function_id="b" if indirect else "a"),))
    second = FunctionIR(node_id="b", name="B", body=(Call(node_id="call:b", function_id="a"),))
    program = Program(entry_function_id="a", functions=(first, second) if indirect else (first,))
    assert validate(program) == ()
    assert from_json(to_json(program)) == program
    with pytest.raises(CompilationError, match="recursive_call"):
        compile_ir(program, target=AutoSuiteTarget())


def test_unknown_vendor_version():
    with pytest.raises(ValueError):
        AutoSuiteTarget(version="unknown")


def test_unverified_short_circuit_is_rejected_explicitly():
    from sciloom import Function, Output, runtime

    class Logical(Function):
        result: Output[bool]

        @runtime
        def run(self):
            self.result = False and (1 / 0 > 0)

    with pytest.raises(CompilationError, match="unsupported_short_circuit"):
        Logical().compile(target=AutoSuiteTarget())
