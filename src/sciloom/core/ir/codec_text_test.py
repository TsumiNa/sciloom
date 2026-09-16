"""Direct text IR and JSON share type checks and reference behavior."""

from dataclasses import replace

import pytest

from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import Interpreter
from . import (
    Assignment,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    TextLength,
    TextSplitPart,
    TextTrim,
    Variable,
    VariableRole,
    from_json,
    to_json,
)


def text_program():
    part = TextSplitPart(
        node_id="part",
        value=TextTrim(node_id="trim", value=Literal(node_id="text", type=ScalarType.TEXT, value=" a,,🧪 ")),
        delimiter=Literal(node_id="delimiter", type=ScalarType.TEXT, value=","),
        index=Literal(node_id="index", type=ScalarType.INTEGER, value=2),
    )
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="TextLength",
                variables=(
                    Variable(
                        node_id="out", owner_id="f", name="length", role=VariableRole.OUTPUT, type=ScalarType.INTEGER
                    ),
                ),
                body=(
                    Assignment(
                        node_id="assignment",
                        target=Reference(node_id="output", symbol_id="out"),
                        value=TextLength(node_id="length", value=part),
                    ),
                ),
            ),
        ),
    )


def test_direct_text_ir_round_trip_and_execution():
    program = text_program()
    restored = from_json(to_json(program))
    assert restored == program
    for candidate in (program, restored):
        assert Interpreter(candidate).run().outputs == {"length": 1}


@pytest.mark.parametrize(
    "field,kind,value,code",
    [
        ("value", ScalarType.INTEGER, 1, "text_type"),
        ("delimiter", ScalarType.BOOLEAN, False, "text_type"),
        ("index", ScalarType.BOOLEAN, True, "index_type"),
        ("value", ScalarType.TEXT, 1, "literal_type"),
    ],
)
def test_invalid_direct_text_types(field, kind, value, code):
    program = text_program()
    function = program.functions[0]
    assignment = function.body[0]
    length = assignment.value
    part = replace(length.value, **{field: Literal(node_id="invalid", type=kind, value=value)})
    program = replace(
        program, functions=(replace(function, body=(replace(assignment, value=replace(length, value=part)),)),)
    )
    with pytest.raises(IRValidationError, match=code):
        to_json(program)
