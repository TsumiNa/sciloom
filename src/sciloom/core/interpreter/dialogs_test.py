"""Finite explicit dialog responses cannot invent values or mutable history."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom import s
from .dialogs import DialogOutcome, DialogResponse, QueuedDialogResponses


def test_queue_copies_responses_and_preserves_empty_text_and_false():
    supplied = [
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value=""),
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False),
    ]
    responses = QueuedDialogResponses(supplied)
    supplied.clear()
    assert responses.remaining == 2
    first = responses.respond()
    assert first.value == "" and first.elapsed == 0 * s
    with pytest.raises(FrozenInstanceError):
        first.value = "changed"
    assert responses.respond().value is False
    with pytest.raises(LookupError):
        responses.respond()
    assert responses.remaining == 0


@pytest.mark.parametrize("value", [None, 0, 1, [], {}])
def test_accepted_response_requires_exact_text_or_bool(value):
    with pytest.raises(TypeError):
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value=value)


@pytest.mark.parametrize("outcome", [DialogOutcome.CANCELLED, DialogOutcome.STOPPED, DialogOutcome.TIMED_OUT])
def test_failed_outcomes_never_carry_a_fallback(outcome):
    assert DialogResponse(outcome=outcome).value is None
    with pytest.raises(ValueError):
        DialogResponse(outcome=outcome, value="default")


def test_elapsed_outcome_and_queue_entry_validation():
    with pytest.raises(ValueError):
        DialogResponse(outcome=DialogOutcome.CANCELLED, elapsed=-1 * s)
    with pytest.raises(TypeError):
        DialogResponse(outcome=DialogOutcome.CANCELLED, elapsed=1)
    with pytest.raises(ValueError):
        DialogResponse(outcome="invented")
    with pytest.raises(TypeError):
        QueuedDialogResponses([True])
    assert DialogResponse(outcome="cancelled").outcome == DialogOutcome.CANCELLED
