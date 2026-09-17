"""Barcode source/direct IR/JSON agree without claiming native acceptance."""

from pathlib import Path

import pytest

from sciloom import s
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError
from sciloom.core.interpreter import (
    DialogEvent,
    DialogOutcome,
    DialogResponse,
    Interpreter,
    LogEvent,
    QueuedDialogResponses,
    ReferenceEnvironment,
    WellProperties,
    WellPropertyWriteEvent,
)
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom_autosuite import AutoSuiteTarget
from .capture_barcode import CaptureBarcode
from .developer.barcode_ir import build_program


def programs():
    return (CaptureBarcode().to_ir(), build_program(), from_json(to_json(build_program())))


def environment(response):
    return ReferenceEnvironment(
        locations=LocationDirectory(wells=(Well(identity="a", name="A1"), Well(identity="b", name="B1"))),
        properties=WellProperties(),
        dialogs=QueuedDialogResponses([response]),
    )


@pytest.mark.parametrize("value", ["S-001", "", "試料 'A'"])
def test_accepted_barcode_is_written_and_logged_in_order(value):
    for program in programs():
        env = environment(DialogResponse(outcome=DialogOutcome.ACCEPTED, value=value))
        result = Interpreter(program, environment=env).run(inputs={"well": Zone(well_ids=("a",))})
        assert result.outputs == {"barcode": value}
        assert env.properties.snapshot() == {("a", "sample_ID"): value}
        assert [type(e) for e in result.events] == [DialogEvent, WellPropertyWriteEvent, LogEvent]
        assert [e.value for e in result.events] == [value, value, value]
        assert result.events[0].message == "Barcode for A1"
        with pytest.raises(CompilationError, match="unsupported_dialog_result"):
            compile_ir(program, target=AutoSuiteTarget())


@pytest.mark.parametrize(
    "response",
    [
        DialogResponse(outcome=DialogOutcome.CANCELLED),
        DialogResponse(outcome=DialogOutcome.STOPPED),
        DialogResponse(outcome=DialogOutcome.TIMED_OUT),
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value="late", elapsed=30 * s),
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value=True),
    ],
)
def test_failure_prevents_property_and_log(response):
    for program in programs():
        env = environment(response)
        with pytest.raises(ExecutionError, match="dialog_"):
            Interpreter(program, environment=env).run(inputs={"well": Zone(well_ids=("a",))})
        assert env.properties.snapshot() == {}
        assert len(env.events) == 1 and isinstance(env.events[0], DialogEvent)


@pytest.mark.parametrize("ids", [(), ("a", "b"), ("missing",)])
def test_invalid_location_fails_before_consuming_response(ids):
    for program in programs():
        env = environment(DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"))
        with pytest.raises(ExecutionError):
            Interpreter(program, environment=env).run(inputs={"well": Zone(well_ids=ids)})
        assert env.dialogs.remaining == 1 and env.events == () and env.properties.snapshot() == {}


def test_json_companion_is_current():
    path = Path(__file__).parent / "developer/barcode_ir.json"
    assert path.read_text() == to_json(build_program())
