"""Notification responses gate subsequent effects and retain captured messages."""

import pytest

from sciloom import Function, Input, Var, log, notify, runtime
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import (
    AcknowledgementEvent,
    Interpreter,
    LogEvent,
    QueuedAcknowledgements,
    ReferenceEnvironment,
)
from sciloom.core.ir import from_json, to_json


class ConfirmSample(Function):
    label: Input[str]
    confirmations: Var[int] = 0

    @runtime
    def run(self) -> None:
        log("before", category="recipe", stream="status")
        notify(message="Confirm " + self.label)
        self.label = "changed"
        self.confirmations += 1
        log(self.confirmations, category="recipe", stream="confirmed")


def test_confirmation_and_json_capture_order_and_session_state():
    program = ConfirmSample().to_ir()
    before = to_json(program)
    for candidate in (program, from_json(before)):
        responses = QueuedAcknowledgements([True, True])
        environment = ReferenceEnvironment(acknowledgements=responses)
        session = Interpreter(candidate, environment=environment)
        first = session.run(inputs={"label": "A"})
        assert [type(e) for e in first.events] == [LogEvent, AcknowledgementEvent, LogEvent]
        assert first.events[1].message == "Confirm A"
        assert first.events[1].source.path == __file__
        assert first.events[2].value == 1
        second = session.run(inputs={"label": "B"})
        assert second.events[1].message == "Confirm B"
        assert second.events[2].value == 2
        assert responses.remaining == 0
        assert environment.events == first.events + second.events
        with pytest.raises(ExecutionError, match="acknowledgement_required"):
            session.run(inputs={"label": "C"})
        assert environment.events == first.events + second.events + (environment.events[-1],)
        assert environment.events[-1].value == "before"
    assert to_json(program) == before


@pytest.mark.parametrize(
    "environment,code",
    [
        (None, "missing_environment_service"),
        (ReferenceEnvironment(acknowledgements=QueuedAcknowledgements()), "acknowledgement_required"),
    ],
)
def test_missing_response_stops_before_following_assignment(environment, code):
    session = Interpreter(ConfirmSample().to_ir(), environment=environment)
    with pytest.raises(ExecutionError) as error:
        session.run(inputs={"label": "A"})
    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == code
    assert diagnostic.source.path == __file__
    assert len(session.environment.events) == 1
    assert session.environment.events[0].value == "before"
    assert diagnostic.node_id == session.program.functions[0].body[1].node_id


def test_bad_message_fails_before_consuming_response():
    class InvalidIndex(Function):
        messages: Input[list[str]]

        @runtime
        def run(self) -> None:
            notify(self.messages[0])

    responses = QueuedAcknowledgements([True])
    environment = ReferenceEnvironment(acknowledgements=responses)
    with pytest.raises(ExecutionError, match="index"):
        Interpreter(InvalidIndex().to_ir(), environment=environment).run(inputs={"messages": []})
    assert responses.remaining == 1
    assert environment.events == ()


def test_notification_marker_alias_and_wrong_type():
    confirm = notify

    class Alias(Function):
        @runtime
        def run(self) -> None:
            confirm("Ready?")

    assert Alias().to_ir().functions[0].body[0].message.value == "Ready?"

    class WrongType(Function):
        @runtime
        def run(self) -> None:
            notify(42)

    class MissingArgument(Function):
        @runtime
        def run(self) -> None:
            notify()

    for instance in (WrongType(), MissingArgument()):
        with pytest.raises(IRValidationError):
            instance.to_ir()


def test_child_calls_and_branches_consume_only_executed_confirmations():
    class Child(Function):
        @runtime
        def run(self) -> None:
            notify("Child ready")

    class Parent(Function):
        enabled: Input[bool]
        index: Var[int] = 0

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self) -> None:
            self.index = 0
            while self.index < 2:
                if self.enabled:
                    self.child()
                self.index += 1
            log(self.index, category="recipe", stream="count")

    responses = QueuedAcknowledgements([True, True, True])
    environment = ReferenceEnvironment(acknowledgements=responses)
    session = Interpreter(Parent().to_ir(), environment=environment)
    skipped = session.run(inputs={"enabled": False})
    assert len(skipped.events) == 1
    assert responses.remaining == 3
    completed = session.run(inputs={"enabled": True})
    assert [type(e) for e in completed.events] == [AcknowledgementEvent, AcknowledgementEvent, LogEvent]
    snapshot = environment.events
    with pytest.raises(ExecutionError, match="acknowledgement_required"):
        session.run(inputs={"enabled": True})
    assert responses.remaining == 0
    assert environment.events[:-1] == snapshot
    assert isinstance(environment.events[-1], AcknowledgementEvent)


def test_result_binding_and_extra_arguments_are_rejected():
    class AssignResult(Function):
        result: Var[str] = ""

        @runtime
        def run(self) -> None:
            self.result = notify("Ready?")

    class ExtraArgument(Function):
        @runtime
        def run(self) -> None:
            notify("Ready?", timeout=5)

    class Unpacked(Function):
        @runtime
        def run(self) -> None:
            notify(*("Ready?",))

    for instance in (AssignResult(), ExtraArgument(), Unpacked()):
        with pytest.raises(IRValidationError):
            instance.to_ir()
