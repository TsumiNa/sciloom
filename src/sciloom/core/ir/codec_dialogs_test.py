"""Typed dialog nodes preserve their ordered results through JSON v4."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.device_locations import validate_device_locations
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import (
    DialogOutcome,
    DialogResponse,
    Interpreter,
    QueuedDialogResponses,
    ReferenceEnvironment,
)
from sciloom.core.specialization import specialize
from sciloom.core.timing import validate_timer_usage
from . import (
    AskYesNo,
    FunctionIR,
    Literal,
    Program,
    Reference,
    RequestText,
    ScalarType,
    Variable,
    VariableRole,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def dialog_program():
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Identify",
                variables=(
                    Variable(node_id="text", owner_id="f", name="text", type=ScalarType.TEXT, role=VariableRole.OUTPUT),
                    Variable(
                        node_id="answer", owner_id="f", name="answer", type=ScalarType.BOOLEAN, role=VariableRole.OUTPUT
                    ),
                ),
                body=(
                    RequestText(
                        node_id="request",
                        target=Reference(node_id="text_target", symbol_id="text"),
                        message=Literal(node_id="prompt", type=ScalarType.TEXT, value="Barcode"),
                    ),
                    AskYesNo(
                        node_id="ask",
                        target=Reference(node_id="answer_target", symbol_id="answer"),
                        message=Reference(node_id="captured", symbol_id="text"),
                        timeout=Literal(node_id="deadline", type=ScalarType.DURATION, value=5.0),
                    ),
                ),
            ),
        ),
    )


def test_direct_json_specialized_dialogs_and_frozen_events():
    program = dialog_program()
    canonical = to_json(program)
    document = to_dict(program)
    assert document["format_version"] == 4
    assert [node["kind"] for node in document["functions"][0]["body"]] == ["RequestText", "AskYesNo"]
    restored = from_json(canonical)
    assert restored == program
    selected = specialize(restored, bindings=DeviceBindings())
    for candidate in (program, restored, selected):
        assert validate_device_usage(candidate, DeviceBindings()) == ()
        assert validate_device_locations(candidate, DeviceBindings()) == ()
        assert validate_timer_usage(candidate) == ()
        environment = ReferenceEnvironment(
            dialogs=QueuedDialogResponses(
                [
                    DialogResponse(outcome=DialogOutcome.ACCEPTED, value="A"),
                    DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False),
                ]
            )
        )
        result = Interpreter(candidate, environment=environment).run()
        assert result.outputs == {"text": "A", "answer": False}
        assert result.events[1].message == "A"
        with pytest.raises(FrozenInstanceError):
            result.events[0].value = "changed"
    assert to_json(program) == canonical


@pytest.mark.parametrize("change", ["type", "target", "owner", "message", "timeout", "field", "kind"])
def test_dialog_wire_and_semantic_errors_rejected(change):
    document = to_dict(dialog_program())
    function = document["functions"][0]
    node = function["body"][1]
    if change == "type":
        function["variables"][1]["type"] = "text"
    elif change == "target":
        node["target"]["symbol_id"] = "missing"
    elif change == "owner":
        function["variables"][1]["owner_id"] = "elsewhere"
    elif change == "message":
        node["message"]["symbol_id"] = "answer"
    elif change == "timeout":
        node["timeout"]["type"] = "real"
    elif change == "field":
        node["default"] = False
    else:
        node["kind"] = "FutureDialog"
    with pytest.raises(IRValidationError):
        from_dict(document)
