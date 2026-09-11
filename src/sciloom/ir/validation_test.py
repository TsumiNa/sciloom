"""Semantic tests independent of either Python lowering or AutoSuite XML."""

from dataclasses import replace

import pytest

from sciloom.ir import (
    Assignment,
    Binary,
    BinaryOp,
    Call,
    FunctionIR,
    If,
    Literal,
    Program,
    Reference,
    ScalarType,
    SourceSpan,
    Unary,
    UnaryOp,
    Variable,
    VariableRole,
    While,
    validate,
)


def test_function_call_binding(package):
    assert validate(package) == ()


def test_nested_control_flow():
    index = Variable(
        node_id="index",
        owner_id="fn",
        name="index",
        role=VariableRole.INTERNAL,
        type=ScalarType.INTEGER,
        initial=Literal(node_id="zero", type=ScalarType.INTEGER, value=0),
    )
    increment = Assignment(
        node_id="increment",
        target=Reference(node_id="dest", symbol_id="index"),
        value=Binary(
            node_id="plus",
            op=BinaryOp.ADD,
            left=Reference(node_id="read", symbol_id="index"),
            right=Literal(node_id="one", type=ScalarType.INTEGER, value=1),
        ),
    )
    loop = While(
        node_id="loop",
        condition=Binary(
            node_id="compare",
            op=BinaryOp.LESS,
            left=Reference(node_id="test", symbol_id="index"),
            right=Literal(node_id="three", type=ScalarType.INTEGER, value=3),
        ),
        body=(
            If(
                node_id="branch",
                condition=Unary(
                    node_id="not",
                    op=UnaryOp.NOT,
                    operand=Literal(node_id="false", type=ScalarType.BOOLEAN, value=False),
                ),
                then_body=(increment,),
            ),
        ),
    )
    program = Program(
        entry_function_id="fn",
        functions=(
            FunctionIR(
                node_id="fn",
                name="Counter",
                variables=(index,),
                body=(loop,),
            ),
        ),
    )
    assert validate(program) == ()
    bad_loop = replace(loop, condition=Literal(node_id="bad", type=ScalarType.INTEGER, value=1))
    bad_program = replace(program, functions=(replace(program.functions[0], body=(bad_loop,)),))
    assert "condition_type" in {d.code for d in validate(bad_program)}


def test_cross_function_reference_is_not_a_global(package):
    callee, caller = package.functions
    assignment = callee.body[0]
    callee = replace(
        callee,
        body=(
            replace(
                assignment,
                value=Reference(node_id="outside", symbol_id="var:result"),
            ),
        ),
    )
    diagnostics = validate(replace(package, functions=(callee, caller)))
    assert [d.code for d in diagnostics] == ["symbol_scope"]
    assert diagnostics[0].path == "$.functions[0].body[0].value"


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unknown"])
def test_invalid_call_bindings(package, problem):
    callee, caller = package.functions
    call = caller.body[0]
    binding = call.inputs[0]
    inputs = {
        "missing": (),
        "duplicate": (binding, replace(binding, value=replace(binding.value, node_id="extra"))),
        "unknown": (replace(binding, parameter_id="missing"),),
    }[problem]
    caller = replace(caller, body=(replace(call, inputs=inputs),))
    assert "call_binding" in {d.code for d in validate(replace(package, functions=(callee, caller)))}


def test_output_binding_checks_assignment_direction(package):
    callee, caller = package.functions
    integer = replace(
        caller.variables[0],
        type=ScalarType.INTEGER,
        initial=Literal(
            node_id="lit:initial",
            type=ScalarType.INTEGER,
            value=0,
        ),
    )
    diagnostics = validate(replace(package, functions=(callee, replace(caller, variables=(integer,)))))
    assert "type_mismatch" in {d.code for d in diagnostics}


@pytest.mark.parametrize("indirect", [False, True])
def test_recursion_is_a_target_policy(indirect):
    first = FunctionIR(
        node_id="a",
        name="A",
        body=(
            Call(
                node_id="call:a",
                function_id="b" if indirect else "a",
            ),
        ),
    )
    second = FunctionIR(node_id="b", name="B", body=(Call(node_id="call:b", function_id="a"),))
    package = Program(entry_function_id="a", functions=(first, second) if indirect else (first,))
    assert validate(package) == ()


def test_duplicate_ids_and_wrong_ownership(package):
    callee, caller = package.functions
    variable = replace(caller.variables[0], node_id="var:x", owner_id="fn:identity")
    diagnostics = validate(replace(package, functions=(callee, replace(caller, variables=(variable,)))))
    assert {"duplicate_id", "variable_owner"} <= {d.code for d in diagnostics}


def test_empty_package_and_dangling_callee(package):
    assert "entry_function" in {d.code for d in validate(Program(entry_function_id="absent"))}
    _, caller = package.functions
    diagnostics = validate(replace(package, functions=(caller,)))
    assert "unknown_function" in {d.code for d in diagnostics}


def test_boolean_is_not_integer(package):
    callee, caller = package.functions
    call = caller.body[0]
    argument = replace(
        call.inputs[0],
        value=Literal(
            node_id="wrong",
            type=ScalarType.INTEGER,
            value=True,
        ),
    )
    diagnostics = validate(
        replace(
            package,
            functions=(
                callee,
                replace(caller, body=(replace(call, inputs=(argument,)),)),
            ),
        )
    )
    assert "literal_type" in {d.code for d in diagnostics}


@pytest.mark.parametrize(
    "op,left,right,target,error",
    [
        (BinaryOp.ADD, 1, 2.5, ScalarType.REAL, None),
        (BinaryOp.DIVIDE, 4, 2, ScalarType.INTEGER, "type_mismatch"),
        (BinaryOp.DIVIDE, 4, 2, ScalarType.REAL, None),
        (BinaryOp.LESS, 1, 2.5, ScalarType.BOOLEAN, None),
        (BinaryOp.EQUAL, True, False, ScalarType.BOOLEAN, None),
        (BinaryOp.EQUAL, True, 1, ScalarType.BOOLEAN, "operator_type"),
        (BinaryOp.AND, True, False, ScalarType.BOOLEAN, None),
        (BinaryOp.OR, 0, 1, ScalarType.BOOLEAN, "operator_type"),
        (BinaryOp.ADD, True, 1, ScalarType.INTEGER, "operator_type"),
    ],
)
def test_expression_types(op, left, right, target, error):
    types = {int: ScalarType.INTEGER, float: ScalarType.REAL, bool: ScalarType.BOOLEAN}
    function = FunctionIR(
        node_id="fn",
        name="Expression",
        variables=(
            Variable(
                node_id="out",
                owner_id="fn",
                name="out",
                role=VariableRole.OUTPUT,
                type=target,
            ),
        ),
        body=(
            Assignment(
                node_id="assign",
                target=Reference(node_id="ref", symbol_id="out"),
                value=Binary(
                    node_id="binary",
                    op=op,
                    left=Literal(node_id="left", type=types[type(left)], value=left),
                    right=Literal(node_id="right", type=types[type(right)], value=right),
                ),
            ),
        ),
    )
    diagnostics = validate(Program(entry_function_id="fn", functions=(function,)))
    assert [d.code for d in diagnostics] == ([] if error is None else [error])


def test_initializer_role_and_source_diagnostic(package):
    callee, caller = package.functions
    source = SourceSpan(path="example.py", line=3, column=4)
    input_variable = replace(
        callee.variables[0],
        source=source,
        initial=Literal(
            node_id="init:input",
            type=ScalarType.REAL,
            value=0.0,
        ),
    )
    callee = replace(callee, variables=(input_variable, callee.variables[1]))
    diagnostics = validate(replace(package, functions=(callee, caller)))
    assert diagnostics[0].code == "initializer_role"
    assert diagnostics[0].source == source
    caller = replace(caller, variables=(replace(caller.variables[0], initial=None),))
    assert "missing_initializer" in {d.code for d in validate(replace(package, functions=(callee, caller)))}
