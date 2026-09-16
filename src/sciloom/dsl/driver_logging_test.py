"""Runtime logs capture typed values once, preserving order and source locations."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom import Agitator, Function, Input, Var, Volume, log, mL, rpm, runtime
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import DeviceEvent, Interpreter, LogEvent, ReferenceEnvironment
from sciloom.core.ir import ScalarType, from_json, to_json


class RecordVolumes(Function):
    amount: Input[Volume]
    category: Input[str]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.index = 0
        while self.index < 2:
            log(self.amount, category=self.category, stream="volume")
            self.amount = self.amount + 1 * mL
            self.index += 1


def test_python_json_loops_capture_values_and_keep_history():
    original = RecordVolumes().to_ir()
    document = to_json(original)
    for program in (original, from_json(document)):
        environment = ReferenceEnvironment()
        session = Interpreter(program, environment=environment)
        first = session.run(inputs={"amount": 1 * mL, "category": "試料"})
        second = session.run(inputs={"amount": 3 * mL, "category": "next"})
        assert [e.value for e in first.events] == [1 * mL, 2 * mL]
        assert [e.value for e in second.events] == [3 * mL, 4 * mL]
        assert all(e.type == ScalarType.VOLUME and e.stream == "volume" for e in first.events)
        assert all(e.category == "試料" and e.source.path == __file__ for e in first.events)
        assert environment.events == first.events + second.events
        with pytest.raises(FrozenInstanceError):
            first.events[0].value = 9 * mL
    assert to_json(original) == document


def test_log_order_across_child_calls_and_device_actions():
    class Child(Function):
        @runtime
        def run(self) -> None:
            log(True, category="child", stream="ready")

    class Parent(Function):
        shaker: Agitator
        enabled: Input[bool]

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self) -> None:
            if self.enabled:
                self.shaker.speed = 300 * rpm
                log(300 * rpm, category="recipe", stream="speed")
                self.shaker.start()
                self.child()
                self.shaker.stop()

    session = Interpreter(Parent().to_ir())
    assert session.run(inputs={"enabled": False}).events == ()
    events = session.run(inputs={"enabled": True}).events
    assert [type(e) for e in events] == [DeviceEvent, LogEvent, DeviceEvent, LogEvent, DeviceEvent]
    assert events[1].value == 300 * rpm
    assert events[3].value is True


def test_failed_log_does_not_append_or_continue():
    class Failed(Function):
        values: Input[list[str]]
        divisor: Input[float]

        @runtime
        def run(self) -> None:
            log("before", category="run", stream="status")
            log(1 / self.divisor, stream=self.values[1], category=self.values[0])
            log("after", category="run", stream="status")

    session = Interpreter(Failed().to_ir())
    with pytest.raises(ExecutionError, match="numeric_error"):
        session.run(inputs={"values": [], "divisor": 0.0})
    assert [e.value for e in session.environment.events] == ["before"]
    with pytest.raises(ExecutionError, match="index") as failure:
        session.run(inputs={"values": [], "divisor": 1.0})
    assert failure.value.diagnostics[0].node_id == session.program.functions[0].body[1].category.node_id
    assert [e.value for e in session.environment.events] == ["before", "before"]


def test_marker_alias_and_host_guard():
    record = log

    class Alias(Function):
        @runtime
        def run(self) -> None:
            record(3, category="recipe", stream="count")

    assert Interpreter(Alias().to_ir()).run().events[0].value == 3
    with pytest.raises(TypeError, match="runtime"):
        log(1, category="host", stream="count")


def test_log_rejects_lists_wrong_names_and_result_use():
    class ListValue(Function):
        @runtime
        def run(self) -> None:
            log([1.0], category="recipe", stream="values")

    class BadCategory(Function):
        @runtime
        def run(self) -> None:
            log(1, category=2, stream="value")

    class MissingKeyword(Function):
        @runtime
        def run(self) -> None:
            log(1, category="recipe")

    class Result(Function):
        value: Var[int] = 0

        @runtime
        def run(self) -> None:
            self.value = log(1, category="recipe", stream="count")

    for instance in (ListValue(), BadCategory(), MissingKeyword(), Result()):
        with pytest.raises(IRValidationError):
            instance.to_ir()


def test_shadowed_log_is_never_executed():
    def log(*args, **kwargs):
        raise AssertionError("Source analysis must not execute user functions.")

    class Shadowed(Function):
        @runtime
        def run(self) -> None:
            log(1, category="recipe", stream="count")

    with pytest.raises(IRValidationError):
        Shadowed().to_ir()
