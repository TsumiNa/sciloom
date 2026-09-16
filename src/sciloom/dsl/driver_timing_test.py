"""Elapsed waits, timer reset and shared call time preserve ordered effects."""

import pytest

from sciloom import Agitator, Duration, Function, Input, Timer, Var, log, rpm, runtime, s, wait
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, TimerEvent, VirtualClock, WaitEvent
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteTarget


class Timed(Function):
    timer: Timer

    @runtime
    def run(self) -> None:
        self.timer.start()
        wait(2 * s)
        self.timer.wait_until(5 * s)
        self.timer.wait_until(3 * s)
        self.timer.start()
        self.timer.wait_until(1 * s)


def test_timer_reset_elapsed_wait_and_json_share_six_second_result():
    program = Timed().to_ir()
    before = to_json(program)
    for candidate in (program, from_json(before)):
        clock = VirtualClock(start=10)
        environment = ReferenceEnvironment(clock=clock)
        session = Interpreter(candidate, environment=environment)
        first = session.run()
        assert clock.monotonic() == 16
        assert [type(e) for e in first.events] == [TimerEvent, WaitEvent, WaitEvent, WaitEvent, TimerEvent, WaitEvent]
        assert [(e.started_at, e.finished_at) for e in first.events if isinstance(e, WaitEvent)] == [
            (10, 12),
            (12, 15),
            (15, 15),
            (15, 16),
        ]
        session.run()
        assert clock.monotonic() == 22
        assert first.events[0].started_at == 10
        assert len(environment.events) == 12
    assert to_json(program) == before


def test_child_waits_consume_parent_timer_time():
    class Child(Function):
        @runtime
        def run(self) -> None:
            wait(duration=4 * s)

    class Parent(Function):
        timer: Timer

        def __init__(self):
            self.child = Child()

        @runtime
        def run(self) -> None:
            self.timer.start()
            self.child()
            self.timer.wait_until(5 * s)

    clock = VirtualClock()
    result = Interpreter(Parent().to_ir(), environment=ReferenceEnvironment(clock=clock)).run()
    assert clock.monotonic() == 5
    assert [(e.started_at, e.finished_at) for e in result.events if isinstance(e, WaitEvent)] == [(0, 4), (4, 5)]


def test_negative_wait_leaves_clock_and_prior_effects_intact():
    class Pause(Function):
        duration: Input[Duration]

        @runtime
        def run(self) -> None:
            log("before", category="recipe", stream="status")
            wait(self.duration)
            log("after", category="recipe", stream="status")

    clock = VirtualClock()
    environment = ReferenceEnvironment(clock=clock)
    with pytest.raises(ExecutionError, match="wait_duration"):
        Interpreter(Pause().to_ir(), environment=environment).run(inputs={"duration": -1 * s})
    assert clock.monotonic() == 0
    assert [e.value for e in environment.events] == ["before"]
    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        Pause().compile(target=AutoSuiteTarget())


def test_previous_run_never_authorizes_wait_and_compile_checks_all_paths():
    class Conditional(Function):
        timer: Timer
        start: Input[bool]

        @runtime
        def run(self) -> None:
            if self.start:
                self.timer.start()
            self.timer.wait_until(1 * s)

    program = Conditional().to_ir()
    session = Interpreter(program, environment=ReferenceEnvironment(clock=VirtualClock()))
    session.run(inputs={"start": True})
    with pytest.raises(ExecutionError, match="timer_not_started"):
        session.run(inputs={"start": False})
    with pytest.raises(CompilationError, match="timer_not_started"):
        Conditional().compile(target=AutoSuiteTarget())


def test_zero_iteration_start_does_not_initialize_timer():
    class Loop(Function):
        timer: Timer
        index: Var[int] = 0

        @runtime
        def run(self) -> None:
            while self.index < 0:
                self.timer.start()
                self.index += 1
            self.timer.wait_until(1 * s)

    with pytest.raises(CompilationError, match="timer_not_started"):
        Loop().compile(target=AutoSuiteTarget())


def test_clock_service_is_required_even_for_zero_wait():
    class Zero(Function):
        @runtime
        def run(self) -> None:
            wait(0 * s)

    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(Zero().to_ir()).run()


def test_wait_captures_duration_and_preserves_running_device():
    class Stir(Function):
        shaker: Agitator
        duration: Input[Duration]

        @runtime
        def run(self) -> None:
            self.shaker.speed = 300 * rpm
            self.shaker.start()
            wait(self.duration)
            self.duration = 10 * s

    result = Interpreter(Stir().to_ir(), environment=ReferenceEnvironment(clock=VirtualClock())).run(
        inputs={"duration": 2 * s}
    )
    assert result.events[-1].duration == 2 * s
    assert result.resources["resource:shaker"].enabled
    assert result.resources["resource:shaker"].applied_configuration["speed"] == 300 * rpm


def test_distinct_composed_timers_and_sessions_are_independent():
    class Pair(Function):
        def __init__(self):
            self.first = Timed()
            self.second = Timed()

        @runtime
        def run(self) -> None:
            self.first()
            self.second()

    program = Pair().to_ir()
    assert len({r.node_id for r in program.resources}) == 2
    for _ in range(2):
        clock = VirtualClock()
        result = Interpreter(program, environment=ReferenceEnvironment(clock=clock)).run()
        assert clock.monotonic() == 12
        assert [e.started_at for e in result.events if isinstance(e, TimerEvent)] == [0, 5, 6, 11]


def test_failed_clock_advance_keeps_prior_effects_and_stops():
    class Overflow(Function):
        @runtime
        def run(self) -> None:
            log("before", category="recipe", stream="status")
            wait(1e308 * s)
            log("after", category="recipe", stream="status")

    clock = VirtualClock(start=1e308)
    environment = ReferenceEnvironment(clock=clock)
    with pytest.raises(ExecutionError, match="clock_error"):
        Interpreter(Overflow().to_ir(), environment=environment).run()
    assert clock.monotonic() == 1e308
    assert [e.value for e in environment.events] == ["before"]


def test_timing_calls_reject_wrong_types_arguments_and_expression_positions():
    class WrongUnit(Function):
        @runtime
        def run(self) -> None:
            wait(2 * rpm)

    class WrongStart(Function):
        timer: Timer

        @runtime
        def run(self) -> None:
            self.timer.start(1)

    class WrongWait(Function):
        timer: Timer

        @runtime
        def run(self) -> None:
            self.timer.wait_until(1 * s, duration=2 * s)

    class UnknownOperation(Function):
        timer: Timer

        @runtime
        def run(self) -> None:
            self.timer.stop()

    class Assigned(Function):
        result: Var[int] = 0

        @runtime
        def run(self) -> None:
            self.result = wait(1 * s)

    for model in (WrongUnit, WrongStart, WrongWait, UnknownOperation, Assigned):
        with pytest.raises(IRValidationError):
            model().to_ir()


def test_timer_start_requires_clock_even_without_a_wait():
    class Start(Function):
        timer: Timer

        @runtime
        def run(self) -> None:
            self.timer.start()

    environment = ReferenceEnvironment()
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(Start().to_ir(), environment=environment).run()
    assert environment.events == ()
