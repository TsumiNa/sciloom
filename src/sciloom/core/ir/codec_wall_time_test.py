"""Wall-clock reads keep ordering and strict, additive JSON v4 structure."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.diagnostics import IRValidationError, SourceSpan
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualWallClock, WallTimeEvent
from sciloom.core.specialization import specialize
from . import (
    FunctionIR,
    Program,
    ReadWallTime,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def clock_program():
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Stamp",
                variables=(
                    Variable(
                        node_id="stamp", owner_id="f", name="stamp", type=ScalarType.TEXT, role=VariableRole.OUTPUT
                    ),
                ),
                body=(
                    ReadWallTime(
                        node_id="read",
                        source=SourceSpan(path="recipe.py", line=8),
                        target=Reference(node_id="destination", symbol_id="stamp"),
                        format="%Y-%m-%d_%H%M%S",
                    ),
                ),
            ),
        ),
    )


def test_direct_json_specialized_clock_read_and_immutable_event():
    program = clock_program()
    canonical = to_json(program)
    document = to_dict(program)
    assert document["format_version"] == 4
    assert document["functions"][0]["body"][0]["kind"] == "ReadWallTime"
    restored = from_json(canonical)
    assert restored == program
    selected = specialize(restored, bindings=DeviceBindings())
    assert validate_device_usage(selected, DeviceBindings()) == ()
    for candidate in (program, restored, selected):
        environment = ReferenceEnvironment(wall_clock=VirtualWallClock(datetime(2026, 9, 16, tzinfo=timezone.utc)))
        result = Interpreter(candidate, environment=environment).run()
        assert result.outputs == {"stamp": "2026-09-16_000000"}
        (event,) = result.events
        assert event == WallTimeEvent(
            node_id="read",
            source=SourceSpan(path="recipe.py", line=8),
            format="%Y-%m-%d_%H%M%S",
            value="2026-09-16_000000",
        )
        with pytest.raises(FrozenInstanceError):
            event.value = "changed"
    assert to_json(program) == canonical


@pytest.mark.parametrize("change", ["format", "format_type", "target", "owner", "type", "field", "kind"])
def test_invalid_clock_structure_and_semantics_are_rejected(change):
    document = to_dict(clock_program())
    function = document["functions"][0]
    node = function["body"][0]
    if change == "format":
        node["format"] = "%z"
    elif change == "format_type":
        node["format"] = 3
    elif change == "target":
        node["target"]["symbol_id"] = "missing"
    elif change == "owner":
        function["variables"][0]["owner_id"] = "elsewhere"
    elif change == "type":
        function["variables"][0]["type"] = "integer"
    elif change == "field":
        node["timezone"] = "UTC"
    else:
        node["kind"] = "FutureClock"
    with pytest.raises(IRValidationError):
        from_dict(document)
