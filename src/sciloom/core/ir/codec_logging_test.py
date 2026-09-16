"""Logging is an additive v4 statement with shared structural/semantic checks."""

from dataclasses import replace

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.diagnostics import IRValidationError, SourceSpan
from sciloom.core.interpreter import Interpreter
from sciloom.core.specialization import specialize
from sciloom.units import mL, rpm, s
from . import FunctionIR, Literal, LogValue, Program, ScalarType, from_dict, from_json, to_dict, to_json


def logged_program(kind, value):
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Record",
                body=(
                    LogValue(
                        node_id="record",
                        source=SourceSpan(path="recipe.py", line=12),
                        value=Literal(node_id="value", type=kind, value=value),
                        category=Literal(node_id="category", type=ScalarType.TEXT, value="recipe"),
                        stream=Literal(node_id="stream", type=ScalarType.TEXT, value="value"),
                    ),
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "kind,value,expected",
    [
        (ScalarType.INTEGER, 2, 2),
        (ScalarType.REAL, 1.5, 1.5),
        (ScalarType.BOOLEAN, False, False),
        (ScalarType.TEXT, "試料\n'\\", "試料\n'\\"),
        (ScalarType.VOLUME, 1e-6, 1 * mL),
        (ScalarType.DURATION, -2.0, -2 * s),
        (ScalarType.ROTATIONAL_SPEED, 5.0, 300 * rpm),
    ],
)
def test_direct_logging_roundtrip_execution_and_specialization(kind, value, expected):
    program = logged_program(kind, value)
    before = to_json(program)
    document = to_dict(program)
    assert document["format_version"] == 4
    assert document["functions"][0]["body"][0]["kind"] == "LogValue"
    restored = from_json(before)
    assert restored == program
    bindings = DeviceBindings()
    specialized = specialize(restored, bindings=bindings)
    assert validate_device_usage(specialized, bindings) == ()
    for candidate in (program, restored, specialized):
        (event,) = Interpreter(candidate).run().events
        assert (event.type, event.value, event.category, event.stream) == (kind, expected, "recipe", "value")
        assert type(event.value) is type(expected)
        assert event.source == SourceSpan(path="recipe.py", line=12)
    assert to_json(program) == before


@pytest.mark.parametrize("field", ["category", "stream"])
def test_log_labels_require_text(field):
    program = logged_program(ScalarType.INTEGER, 1)
    function = program.functions[0]
    record = replace(function.body[0], **{field: Literal(node_id=field, type=ScalarType.INTEGER, value=1)})
    with pytest.raises(IRValidationError, match="log_type"):
        to_json(replace(program, functions=(replace(function, body=(record,)),)))


def test_unknown_log_field_and_kind_are_not_silently_ignored():
    for key, value in (("future_option", True), ("kind", "FutureLogValue")):
        document = to_dict(logged_program(ScalarType.INTEGER, 1))
        document["functions"][0]["body"][0][key] = value
        with pytest.raises(IRValidationError):
            from_dict(document)
