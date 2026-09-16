"""Notification structure, typing and direct/JSON reference behavior."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom.core.bindings import DeviceBindings
from sciloom.core.configuration import validate_device_usage
from sciloom.core.diagnostics import ExecutionError, IRValidationError, SourceSpan
from sciloom.core.interpreter import AcknowledgementEvent, Interpreter, QueuedAcknowledgements, ReferenceEnvironment
from sciloom.core.specialization import specialize
from . import FunctionIR, Literal, Notify, Program, ScalarType, from_dict, from_json, to_dict, to_json


def notification_program():
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="Confirm",
                body=(
                    Notify(
                        node_id="notify",
                        source=SourceSpan(path="recipe.py", line=5),
                        message=Literal(node_id="message", type=ScalarType.TEXT, value="試料 ready?"),
                    ),
                ),
            ),
        ),
    )


def test_direct_json_and_specialized_notification_keep_v4_and_sources():
    program = notification_program()
    canonical = to_json(program)
    document = to_dict(program)
    assert document["format_version"] == 4
    assert document["functions"][0]["body"][0]["kind"] == "Notify"
    restored = from_json(canonical)
    assert restored == program
    selected = specialize(restored, bindings=DeviceBindings())
    assert validate_device_usage(selected, DeviceBindings()) == ()
    for candidate in (program, restored, selected):
        environment = ReferenceEnvironment(acknowledgements=QueuedAcknowledgements([True]))
        (event,) = Interpreter(candidate, environment=environment).run().events
        assert event == AcknowledgementEvent(
            node_id="notify", source=SourceSpan(path="recipe.py", line=5), message="試料 ready?"
        )
        with pytest.raises(FrozenInstanceError):
            event.message = "changed"
    assert to_json(program) == canonical


def test_explicit_shared_responses_but_separate_histories():
    responses = QueuedAcknowledgements([True])
    first = ReferenceEnvironment(acknowledgements=responses)
    second = ReferenceEnvironment(acknowledgements=responses)
    result = Interpreter(notification_program(), environment=first).run()
    with pytest.raises(ExecutionError, match="acknowledgement_required"):
        Interpreter(notification_program(), environment=second).run()
    assert first.events == result.events
    assert second.events == ()
    independent = ReferenceEnvironment(acknowledgements=QueuedAcknowledgements([True]))
    assert Interpreter(notification_program(), environment=independent).run().events == result.events


@pytest.mark.parametrize("change", ["type", "field", "kind"])
def test_notification_rejects_wrong_type_and_unknown_structure(change):
    document = to_dict(notification_program())
    node = document["functions"][0]["body"][0]
    if change == "type":
        node["message"].update(type="integer", value=42)
    elif change == "field":
        node["timeout"] = 5
    else:
        node["kind"] = "FutureNotify"
    with pytest.raises(IRValidationError):
        from_dict(document)
