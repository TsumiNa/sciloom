"""List value semantics, persistence and checked indexing through real IR execution."""

from itertools import count

import pytest

from sciloom.core.diagnostics import ExecutionError
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    Call,
    FunctionIR,
    InputBinding,
    ListGet,
    ListLength,
    ListLiteral,
    ListSet,
    ListType,
    Literal,
    OutputBinding,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from sciloom.units import rpm
from .runtime import Interpreter


def nodes():
    sequence = count()

    def node(cls, **fields):
        return cls(node_id=f"n:{next(sequence)}", **fields)

    return node


def io_program(element=ScalarType.REAL, body_factory=None):
    n = nodes()
    kind = ListType(element_type=element)
    source = Variable(node_id="a", owner_id="f", name="values", role=VariableRole.INPUT, type=kind)
    result = Variable(node_id="b", owner_id="f", name="result", role=VariableRole.OUTPUT, type=kind)
    body = (
        body_factory(n, kind)
        if body_factory
        else (n(Assignment, target=n(Reference, symbol_id="b"), value=n(Reference, symbol_id="a")),)
    )
    return Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="Lists", variables=(source, result), body=body),)
    )


@pytest.mark.parametrize(
    "element,values,expected",
    [
        (ScalarType.INTEGER, [1, 2], (1, 2)),
        (ScalarType.REAL, [1, 2.5], (1.0, 2.5)),
        (ScalarType.BOOLEAN, [True, False], (True, False)),
        (ScalarType.ROTATIONAL_SPEED, [60 * rpm, 120 * rpm], (60 * rpm, 120 * rpm)),
        (ScalarType.REAL, [], ()),
    ],
)
def test_list_inputs_outputs_are_detached_readonly_values(element, values, expected):
    program = io_program(element)
    result = Interpreter(from_json(to_json(program))).run(inputs={"values": values})
    assert result.outputs["result"] == expected
    values.append(values[0] if values else 3)
    assert result.outputs["result"] == expected
    with pytest.raises(TypeError):
        result.outputs["result"] = ()


@pytest.mark.parametrize(
    "element,values",
    [
        (ScalarType.INTEGER, [True]),
        (ScalarType.INTEGER, [1.5]),
        (ScalarType.REAL, [False]),
        (ScalarType.REAL, [float("inf")]),
        (ScalarType.BOOLEAN, [1]),
        (ScalarType.REAL, [[1]]),
        (ScalarType.ROTATIONAL_SPEED, [1.0]),
        (ScalarType.REAL, [60 * rpm]),
        (ScalarType.REAL, "not a list"),
    ],
)
def test_bad_list_input_values_fail(element, values):
    with pytest.raises(ExecutionError):
        Interpreter(io_program(element)).run(inputs={"values": values})


def test_internal_list_persists_without_mutating_previous_snapshots_or_other_sessions():
    n = nodes()
    kind = ListType(element_type=ScalarType.INTEGER)
    initial = n(ListLiteral, type=kind, elements=(n(Literal, type=ScalarType.INTEGER, value=1),))
    state = Variable(
        node_id="state", owner_id="f", name="state", role=VariableRole.INTERNAL, type=kind, initial=initial
    )
    result = Variable(node_id="result", owner_id="f", name="result", role=VariableRole.OUTPUT, type=kind)
    function = FunctionIR(
        node_id="f",
        name="Persistent",
        variables=(state, result),
        body=(
            n(
                ListSet,
                target=n(Reference, symbol_id="state"),
                index=n(Literal, type=ScalarType.INTEGER, value=0),
                value=n(Literal, type=ScalarType.INTEGER, value=1),
                op=BinaryOp.ADD,
            ),
            n(Assignment, target=n(Reference, symbol_id="result"), value=n(Reference, symbol_id="state")),
        ),
    )
    program = Program(entry_function_id="f", functions=(function,))
    session = Interpreter(program)
    first = session.run()
    assert first.outputs["result"] == (2,)
    assert session.run().outputs["result"] == (3,)
    assert first.outputs["result"] == first.state["f"]["state"] == (2,)
    assert Interpreter(program).run().outputs["result"] == (2,)
    assert initial.elements[0].value == 1


def test_call_inputs_outputs_and_whole_assignments_do_not_alias():
    n = nodes()
    kind = ListType(element_type=ScalarType.REAL)

    def variable(id, owner, role):
        return Variable(node_id=id, owner_id=owner, name=id, role=role, type=kind)

    def ref(id):
        return n(Reference, symbol_id=id)

    def set_at(id, value):
        return n(
            ListSet,
            target=ref(id),
            index=n(Literal, type=ScalarType.INTEGER, value=0),
            value=n(Literal, type=ScalarType.REAL, value=value),
        )

    child = FunctionIR(
        node_id="child",
        name="MutateCopy",
        variables=(variable("x", "child", VariableRole.INPUT), variable("y", "child", VariableRole.OUTPUT)),
        body=(
            set_at("x", 9.0),
            n(Assignment, target=ref("y"), value=ref("x")),
        ),
    )
    caller = FunctionIR(
        node_id="caller",
        name="Caller",
        variables=(
            variable("a", "caller", VariableRole.INPUT),
            *(variable(id, "caller", VariableRole.OUTPUT) for id in ("b", "original", "copy")),
        ),
        body=(
            n(
                Call,
                function_id="child",
                inputs=(InputBinding(parameter_id="x", value=ref("a")),),
                outputs=(OutputBinding(parameter_id="y", target=ref("b")),),
            ),
            n(Assignment, target=ref("copy"), value=ref("b")),
            set_at("b", 11.0),
            n(Assignment, target=ref("original"), value=ref("a")),
        ),
    )
    program = Program(entry_function_id="caller", functions=(caller, child))
    assert Interpreter(program).run(inputs={"a": [1.0, 2.0]}).outputs == {
        "b": (11.0, 2.0),
        "copy": (9.0, 2.0),
        "original": (1.0, 2.0),
    }


def indexed_program(index, *, write=False, augmented=False, bad_rhs=False):
    n = nodes()
    kind = ListType(element_type=ScalarType.REAL)
    variables = (
        Variable(node_id="a", owner_id="f", name="values", role=VariableRole.INPUT, type=kind),
        Variable(node_id="b", owner_id="f", name="result", role=VariableRole.OUTPUT, type=ScalarType.REAL),
    )
    index_node = n(Literal, type=ScalarType.INTEGER, value=index)
    if write:
        rhs = n(Literal, type=ScalarType.REAL, value=9.0)
        if bad_rhs:
            rhs = n(Binary, op=BinaryOp.DIVIDE, left=rhs, right=n(Literal, type=ScalarType.INTEGER, value=0))
        body = (
            n(
                ListSet,
                target=n(Reference, symbol_id="a"),
                index=index_node,
                value=rhs,
                op=BinaryOp.ADD if augmented else None,
            ),
            n(Assignment, target=n(Reference, symbol_id="b"), value=n(Literal, type=ScalarType.REAL, value=1.0)),
        )
    else:
        body = (
            n(
                Assignment,
                target=n(Reference, symbol_id="b"),
                value=n(ListGet, value=n(Reference, symbol_id="a"), index=index_node),
            ),
        )
    return Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="Index", variables=variables, body=body),)
    ), index_node.node_id


@pytest.mark.parametrize("write", [False, True])
@pytest.mark.parametrize("values,index", [([], 0), ([1.0], -1), ([1.0], 1), ([1.0], 100)])
def test_index_bounds_never_wrap_or_grow(values, index, write):
    program, _ = indexed_program(index, write=write)
    with pytest.raises(ExecutionError, match="index_bounds"):
        Interpreter(program).run(inputs={"values": values})
    assert len(values) in (0, 1)


def test_augmented_index_is_evaluated_once():
    program, index_id = indexed_program(0, write=True, augmented=True)
    session = Interpreter(program)
    visited = []
    tick = session._tick

    def record(node):
        visited.append(node.node_id)
        tick(node)

    session._tick = record
    session.run(inputs={"values": [1.0]})
    assert visited.count(index_id) == 1


@pytest.mark.parametrize("augmented,code", [(False, "numeric_error"), (True, "index_bounds")])
def test_plain_and_augmented_writes_preserve_evaluation_order(augmented, code):
    program, _ = indexed_program(-1, write=True, augmented=augmented, bad_rhs=True)
    with pytest.raises(ExecutionError, match=code):
        Interpreter(program).run(inputs={"values": [1.0]})


def test_runtime_list_construction_and_length():
    def body(n, kind):
        return (
            n(
                Assignment,
                target=n(Reference, symbol_id="b"),
                value=n(
                    ListLiteral,
                    type=kind,
                    elements=(
                        n(ListLength, value=n(Reference, symbol_id="a")),
                        n(
                            ListGet,
                            value=n(Reference, symbol_id="a"),
                            index=n(Literal, type=ScalarType.INTEGER, value=0),
                        ),
                    ),
                ),
            ),
        )

    program = io_program(body_factory=body)
    assert Interpreter(program).run(inputs={"values": [7.0, 8.0]}).outputs["result"] == (2.0, 7.0)
