"""The author and direct-IR confirmation examples preserve their companions."""

from pathlib import Path

import pytest

from sciloom.core.diagnostics import ExecutionError
from sciloom.core.interpreter import (
    AcknowledgementEvent,
    Interpreter,
    LogEvent,
    QueuedAcknowledgements,
    ReferenceEnvironment,
)
from sciloom.core.ir import to_json
from sciloom_autosuite import AutoSuiteTarget
from .confirm_samples import ConfirmSamples
from .developer.confirmation_ir import build_program


def test_confirmation_examples_and_companions():
    example = ConfirmSamples()
    environment = ReferenceEnvironment(acknowledgements=QueuedAcknowledgements([True]))
    session = Interpreter(example.to_ir(), environment=environment)
    result = session.run(inputs={"sample": "A"})
    confirmation, record = result.events
    assert isinstance(confirmation, AcknowledgementEvent)
    assert confirmation.message == "Sample A is ready. Confirm to continue."
    assert isinstance(record, LogEvent) and record.value == "A"
    with pytest.raises(ExecutionError, match="acknowledgement_required"):
        session.run(inputs={"sample": "B"})
    assert environment.events == result.events
    root = Path(__file__).parent
    assert example.compile(target=AutoSuiteTarget()).artifact.content == (root / "confirm_samples.asfp").read_bytes()
    assert to_json(build_program()) == (root / "developer/confirmation_ir.json").read_text(encoding="utf-8")
