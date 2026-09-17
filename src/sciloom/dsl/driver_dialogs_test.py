"""Dialog results are ordered effects with explicit, finite responses."""

import pytest

from sciloom import Duration, Function, Input, Output, Var, ask_yes_no, log, request_text, runtime, s
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import (
    DialogEvent,
    DialogOutcome,
    DialogResponse,
    Interpreter,
    LogEvent,
    QueuedDialogResponses,
    ReferenceEnvironment,
    VirtualClock,
)
from sciloom.core.ir import from_json, to_json


class IdentifySample(Function):
    barcode: Output[str]
    accepted: Output[bool]

    @runtime
    def run(self) -> None:
        self.barcode = request_text("Barcode", timeout=10 * s)
        self.accepted = ask_yes_no("Use " + self.barcode + "?")
        log(self.barcode, category="sample", stream="barcode")


def test_results_json_empty_text_false_and_explicit_clock():
    program = IdentifySample().to_ir()
    canonical = to_json(program)
    for candidate in (program, from_json(canonical)):
        clock = VirtualClock(start=7)
        responses = QueuedDialogResponses(
            [
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value="", elapsed=2 * s),
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False),
            ]
        )
        environment = ReferenceEnvironment(dialogs=responses, clock=clock)
        result = Interpreter(candidate, environment=environment).run()
        assert result.outputs == {"barcode": "", "accepted": False}
        assert [type(e) for e in result.events] == [DialogEvent, DialogEvent, LogEvent]
        assert [e.value for e in result.events] == ["", False, ""]
        assert result.events[0].timeout == 10 * s
        assert result.events[0].elapsed == 2 * s
        assert result.events[0].source.path == __file__
        assert result.events[1].message == "Use ?"
        assert responses.remaining == 0
        assert clock.monotonic() == 7
    assert to_json(program) == canonical


class RetainValue(Function):
    value: Var[str] = "unchanged"

    @runtime
    def run(self) -> None:
        log(self.value, category="test", stream="before")
        self.value = request_text("Replace", timeout=5 * s)
        log("after", category="test", stream="after")


@pytest.mark.parametrize(
    "response,code,outcome",
    [
        (DialogResponse(outcome=DialogOutcome.CANCELLED), "dialog_cancelled", DialogOutcome.CANCELLED),
        (DialogResponse(outcome=DialogOutcome.STOPPED), "dialog_stopped", DialogOutcome.STOPPED),
        (DialogResponse(outcome=DialogOutcome.TIMED_OUT), "dialog_timeout", DialogOutcome.TIMED_OUT),
        (
            DialogResponse(outcome=DialogOutcome.ACCEPTED, value="late", elapsed=5 * s),
            "dialog_timeout",
            DialogOutcome.TIMED_OUT,
        ),
        (
            DialogResponse(outcome=DialogOutcome.ACCEPTED, value="late", elapsed=6 * s),
            "dialog_timeout",
            DialogOutcome.TIMED_OUT,
        ),
        (DialogResponse(outcome=DialogOutcome.ACCEPTED, value=True), "dialog_response_type", DialogOutcome.ACCEPTED),
    ],
)
def test_failure_retains_destination_and_stops_later_effects(response, code, outcome):
    responses = QueuedDialogResponses([response, response])
    environment = ReferenceEnvironment(dialogs=responses)
    session = Interpreter(RetainValue().to_ir(), environment=environment)
    for attempt in range(2):
        with pytest.raises(ExecutionError) as error:
            session.run()
        diagnostic = error.value.diagnostics[0]
        assert diagnostic.code == code
        assert diagnostic.source.path == __file__
        assert [type(e) for e in environment.events] == [LogEvent, DialogEvent] * (attempt + 1)
        assert environment.events[-2].value == "unchanged"
        event = environment.events[-1]
        assert event.outcome == outcome and event.error_code == code and event.value is None
        assert event.node_id == diagnostic.node_id
    assert responses.remaining == 0


@pytest.mark.parametrize(
    "responses,code",
    [
        (None, "missing_environment_service"),
        (QueuedDialogResponses(), "dialog_response_required"),
    ],
)
def test_missing_or_exhausted_service_never_invents_a_response(responses, code):
    environment = ReferenceEnvironment(dialogs=responses)
    session = Interpreter(RetainValue().to_ir(), environment=environment)
    with pytest.raises(ExecutionError, match=code):
        session.run()
    assert [e.value for e in environment.events] == ["unchanged"]


@pytest.mark.parametrize(
    "response,reason",
    [
        (DialogResponse(outcome=DialogOutcome.CANCELLED), "operator cancelled"),
        (DialogResponse(outcome=DialogOutcome.STOPPED), "operator selected Stop"),
        (DialogResponse(outcome=DialogOutcome.TIMED_OUT), "Dialog timed out"),
        (DialogResponse(outcome=DialogOutcome.ACCEPTED, value="Yes"), "requires bool, received str"),
    ],
)
def test_failure_diagnostic_describes_actual_cause_without_inventing_deadline(response, reason):
    class Choose(Function):
        answer: Output[bool]

        @runtime
        def run(self) -> None:
            self.answer = ask_yes_no("Continue?")

    environment = ReferenceEnvironment(dialogs=QueuedDialogResponses([response]))
    with pytest.raises(ExecutionError) as error:
        Interpreter(Choose().to_ir(), environment=environment).run()
    message = error.value.diagnostics[0].message
    assert reason in message
    assert "Configured timeout" not in message and "deadline" not in message
    assert "No result was assigned" in message


def test_arguments_are_captured_in_order_once_before_response(monkeypatch):
    from sciloom.core.interpreter import runtime as interpreter_runtime

    class Capture(Function):
        messages: Input[list[str]]
        timeout: Input[Duration]
        result: Output[str]

        @runtime
        def run(self) -> None:
            self.result = request_text(self.messages[0], timeout=self.timeout)

    program = Capture().to_ir()
    node = program.functions[0].body[0]
    evaluated = []
    original = interpreter_runtime.evaluate

    def track(session, expression, frame):
        evaluated.append(expression.node_id)
        return original(session, expression, frame)

    monkeypatch.setattr(interpreter_runtime, "evaluate", track)
    responses = QueuedDialogResponses([DialogResponse(outcome=DialogOutcome.ACCEPTED, value="A")])
    environment = ReferenceEnvironment(dialogs=responses)
    session = Interpreter(program, environment=environment)
    with pytest.raises(ExecutionError, match="index"):
        session.run(inputs={"messages": [], "timeout": 0 * s})
    assert evaluated == [node.message.node_id]
    assert responses.remaining == 1 and environment.events == ()
    evaluated.clear()
    with pytest.raises(ExecutionError, match="dialog_timeout_value"):
        session.run(inputs={"messages": ["prompt"], "timeout": 0 * s})
    assert evaluated == [node.message.node_id, node.timeout.node_id]
    assert responses.remaining == 1 and environment.events == ()
    evaluated.clear()
    result = session.run(inputs={"messages": ["prompt"], "timeout": 1 * s})
    assert evaluated == [node.message.node_id, node.timeout.node_id]
    assert result.outputs == {"result": "A"}
    assert result.events[0].message == "prompt"


def test_alias_none_timeout_child_loop_and_session_order():
    read = request_text
    no_timeout = None

    class Child(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = read(message="Child", timeout=no_timeout)

    class Parent(Function):
        count: Var[int] = 0
        value: Output[str]
        accepted: Output[bool]

        def __init__(self):
            self.child = Child()
            self.timeout = None

        @runtime
        def run(self) -> None:
            self.count = 0
            self.value = ""
            while self.count < 2:
                self.value = self.child()
                self.count += 1
            self.accepted = ask_yes_no("Continue?", timeout=self.timeout)

    responses = QueuedDialogResponses(
        [DialogResponse(outcome=DialogOutcome.ACCEPTED, value=value) for value in ("A", "B", True, "C", "D", False)]
    )
    environment = ReferenceEnvironment(dialogs=responses)
    session = Interpreter(Parent().to_ir(), environment=environment)
    first = session.run()
    second = session.run()
    assert first.outputs == {"value": "B", "accepted": True}
    assert second.outputs == {"value": "D", "accepted": False}
    assert [e.value for e in environment.events] == ["A", "B", True, "C", "D", False]
    assert environment.events == first.events + second.events
    assert all(e.timeout is None for e in environment.events)


def test_invalid_author_forms_and_types_are_rejected():
    class Discarded(Function):
        @runtime
        def run(self) -> None:
            request_text("prompt")

    class Nested(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text("prompt") + "suffix"

    class Chained(Function):
        a: Output[str]
        b: Output[str]

        @runtime
        def run(self) -> None:
            self.a = self.b = request_text("prompt")

    class WrongResult(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = ask_yes_no("prompt")

    class WrongMessage(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text(1)

    class WrongTimeout(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text("prompt", timeout=1)

    class Unpacked(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text(*("prompt",))

    class MissingMessage(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text()

    for model in (Discarded, Nested, Chained, WrongResult, WrongMessage, WrongTimeout, Unpacked, MissingMessage):
        with pytest.raises(IRValidationError):
            model().to_ir()
    for marker in (request_text, ask_yes_no):
        with pytest.raises(TypeError):
            marker("prompt")


@pytest.mark.parametrize("outcome", [DialogOutcome.CANCELLED, DialogOutcome.STOPPED, DialogOutcome.TIMED_OUT])
def test_child_failure_prevents_caller_property_write_and_device_action(outcome):
    from sciloom import Agitator, WellProperty, Zone, rpm
    from sciloom.core.interpreter import DeviceEvent, WellProperties
    from sciloom.core.locations import LocationDirectory, Well

    class Child(Function):
        value: Output[str]

        @runtime
        def run(self) -> None:
            self.value = request_text("Barcode")

    class Workflow(Function):
        shaker: Agitator
        selection: Input[Zone]
        value: Var[str] = ""

        def __init__(self):
            self.child = Child()
            self.barcode = WellProperty("barcode", str)

        @runtime
        def run(self) -> None:
            self.shaker.speed = 600 * rpm
            self.shaker.start()
            self.value = self.child()
            self.barcode[self.selection] = self.value
            self.shaker.stop()
            log(self.value, category="sample", stream="barcode")

    responses = QueuedDialogResponses([DialogResponse(outcome=outcome)])
    properties = WellProperties()
    environment = ReferenceEnvironment(
        dialogs=responses,
        properties=properties,
        locations=LocationDirectory(wells=(Well(identity="a", name="A"),)),
    )
    with pytest.raises(ExecutionError, match="dialog_"):
        Interpreter(Workflow().to_ir(), environment=environment).run(inputs={"selection": Zone(well_ids=("a",))})
    assert properties.snapshot() == {}
    # The completed start remains; failure neither stops the device nor reaches the caller's stop.
    assert [type(e) for e in environment.events] == [DeviceEvent, DeviceEvent, DialogEvent]
