"""External clock reads are ordered assignments, never duplicated expressions."""

from datetime import datetime, timezone

import pytest

from sciloom import Function, Input, Output, Var, log, now_text, runtime
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, LogEvent, ReferenceEnvironment, VirtualWallClock, WallTimeEvent
from sciloom.core.ir import from_json, to_json

DATE_FORMAT = "%Y-%m-%d"


class Stamp(Function):
    stamp: Output[str]
    filename: Output[str]

    def __init__(self):
        self.format = "%Y-%m-%d_%H%M%S"

    @runtime
    def run(self) -> None:
        log("before", category="recipe", stream="status")
        self.stamp = now_text(format=self.format)
        self.filename = self.stamp + ".csv"
        log(self.stamp, category="recipe", stream="stamp")


def test_runtime_read_capture_json_and_explicit_clock_changes():
    program = Stamp().to_ir()
    before = to_json(program)
    for candidate in (program, from_json(before)):
        clock = VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone.utc))
        environment = ReferenceEnvironment(wall_clock=clock)
        session = Interpreter(candidate, environment=environment)
        first = session.run()
        assert first.outputs == {"stamp": "2026-09-16_140506", "filename": "2026-09-16_140506.csv"}
        assert [type(e) for e in first.events] == [LogEvent, WallTimeEvent, LogEvent]
        assert first.events[1].value == first.events[2].value == first.outputs["stamp"]
        assert first.events[1].source.path == __file__
        clock.set(datetime(2026, 9, 17, tzinfo=timezone.utc))
        second = session.run()
        assert second.outputs["stamp"] == "2026-09-17_000000"
        assert environment.events == first.events + second.events
        assert first.events[1].value == "2026-09-16_140506"
    assert to_json(program) == before


def test_each_read_occurs_once_in_loop_and_even_for_literal_only_format():
    class CountingClock:
        calls = 0

        def now(self):
            self.calls += 1
            return datetime(2026, 9, self.calls, tzinfo=timezone.utc)

    class Repeated(Function):
        stamp: Output[str]
        index: Var[int] = 0

        @runtime
        def run(self) -> None:
            self.stamp = now_text("")
            self.index = 0
            while self.index < 2:
                self.stamp = now_text("%d")
                self.index += 1

    clock = CountingClock()
    result = Interpreter(Repeated().to_ir(), environment=ReferenceEnvironment(wall_clock=clock)).run()
    assert result.outputs["stamp"] == "03"
    assert [e.value for e in result.events] == ["", "02", "03"]
    assert clock.calls == 3


def test_missing_or_bad_clock_stops_without_overwriting_state():
    class Read(Function):
        stamp: Var[str] = "unchanged"

        @runtime
        def run(self) -> None:
            log(self.stamp, category="recipe", stream="before")
            self.stamp = now_text("%Y")
            log("after", category="recipe", stream="status")

    class BadClock:
        calls = 0

        def now(self):
            self.calls += 1
            return datetime(2026, 9, 16)

    for clock, code in ((None, "missing_environment_service"), (BadClock(), "wall_clock_error")):
        environment = ReferenceEnvironment(wall_clock=clock)
        session = Interpreter(Read().to_ir(), environment=environment)
        for attempt in range(2):
            with pytest.raises(ExecutionError) as error:
                session.run()
            diagnostic = error.value.diagnostics[0]
            assert diagnostic.code == code
            assert diagnostic.source.path == __file__
            assert [e.value for e in environment.events] == ["unchanged"] * (attempt + 1)
        if clock is not None:
            assert clock.calls == 2


def test_nested_reads_runtime_formats_and_wrong_destinations_are_rejected():
    class Nested(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = now_text("%Y") + ".csv"

    class DynamicFormat(Function):
        format: Input[str]
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = now_text(self.format)

    class WrongDestination(Function):
        stamp: Output[int]

        @runtime
        def run(self) -> None:
            self.stamp = now_text("%Y")

    for model in (Nested, DynamicFormat, WrongDestination):
        with pytest.raises(IRValidationError):
            model().to_ir()


def test_alias_and_closure_formats_in_child_calls_share_explicit_clock():
    clock_read = now_text
    time_format = "%H%M%S"

    class Child(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = clock_read(time_format)

    class Parent(Function):
        date: Output[str]
        time: Output[str]

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self) -> None:
            self.date = now_text(DATE_FORMAT)
            self.time = self.child()

    environment = ReferenceEnvironment(
        wall_clock=VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone.utc))
    )
    result = Interpreter(Parent().to_ir(), environment=environment).run()
    assert result.outputs == {"date": "2026-09-16", "time": "140506"}
    assert [e.format for e in result.events] == [DATE_FORMAT, time_format]


@pytest.mark.parametrize("failure", [OSError("clock unavailable"), "not a datetime"])
def test_clock_provider_failure_retains_prior_effects_and_stops(failure):
    class Clock:
        calls = 0

        def now(self):
            self.calls += 1
            if isinstance(failure, Exception):
                raise failure
            return failure

    clock = Clock()
    environment = ReferenceEnvironment(wall_clock=clock)
    with pytest.raises(ExecutionError, match="wall_clock_error"):
        Interpreter(Stamp().to_ir(), environment=environment).run()
    assert clock.calls == 1
    assert [e.value for e in environment.events] == ["before"]


def test_discarded_indexed_unpacked_and_augmented_clock_reads_are_rejected():
    class Discarded(Function):
        @runtime
        def run(self) -> None:
            now_text("%Y")

    class Indexed(Function):
        stamps: Var[list[str]] = [""]

        @runtime
        def run(self) -> None:
            self.stamps[0] = now_text("%Y")

    class Unpacked(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            (self.stamp,) = now_text("%Y")

    class Augmented(Function):
        stamp: Var[str] = ""

        @runtime
        def run(self) -> None:
            self.stamp += now_text("%Y")

    class WrongArguments(Function):
        stamp: Output[str]

        @runtime
        def run(self) -> None:
            self.stamp = now_text("%Y", format="%m")

    for model in (Discarded, Indexed, Unpacked, Augmented, WrongArguments):
        with pytest.raises(IRValidationError):
            model().to_ir()
