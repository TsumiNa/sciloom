"""Explicit copied OK responses are consumed once and never supplied by default."""

import pytest

from .acknowledgements import QueuedAcknowledgements


def test_responses_are_copied_and_consumed_once():
    supplied = [True, True]
    responses = QueuedAcknowledgements(supplied)
    supplied.clear()
    assert responses.remaining == 2
    assert responses.acknowledge("Ready?") is None
    assert responses.remaining == 1
    responses.acknowledge("")
    assert responses.remaining == 0
    with pytest.raises(LookupError):
        responses.acknowledge("Again?")
    assert responses.remaining == 0


@pytest.mark.parametrize("response", [False, 1, 0, "yes", None])
def test_only_explicit_true_responses_are_accepted(response):
    with pytest.raises(ValueError, match="True"):
        QueuedAcknowledgements([response])


def test_empty_queue_and_bad_message_never_acknowledge():
    empty = QueuedAcknowledgements()
    with pytest.raises(LookupError):
        empty.acknowledge("Confirm")
    responses = QueuedAcknowledgements([True])
    with pytest.raises(TypeError):
        responses.acknowledge(123)
    assert responses.remaining == 1
