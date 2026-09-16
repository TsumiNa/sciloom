"""Native timer scheduling and XML evidence, independently of Executor timing."""

import gzip
import xml.etree.ElementTree as ET

import pytest

from sciloom import Function, Input, Timer, hour, runtime, s, wait
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualClock
from sciloom.core.ir import from_json, to_json
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .target import AutoSuiteTarget


class Timed(Function):
    timer: Timer

    @runtime
    def run(self) -> None:
        self.timer.start()
        wait(2 * s)
        self.timer.wait_until(5 * s)
        self.timer.wait_until(1 * s)
        self.timer.start()
        self.timer.wait_until(2 * s)


class TimingWire(WireModel):
    """Assume documented elapsed semantics; this does not run a vendor clock."""

    def __init__(self, content):
        super().__init__(content)
        self.now = 0.0
        self.origins = {}
        self.waits = []

    def tasks(self, tasks, frame):
        for task in tasks:
            kind = task.attrib["typeid"]
            if kind == "Chemspeed.SATaskSetTimer.1":
                self.origins[task.findtext("timername")] = self.now
            elif kind == "Chemspeed.SATaskWait.1":
                duration = self.expression(task.findtext("time"), frame)
                assert task.findtext("timeunit") == "s"
                before = self.now
                if task.findtext("waitmode") == "2":
                    self.now = max(self.now, self.origins[task.findtext("timername")] + duration)
                else:
                    assert task.findtext("waitmode") == "0"
                    self.now += duration
                self.waits.append((before, self.now))
            else:
                super().tasks((task,), frame)


def test_timer_reset_and_elapsed_wait_schedule_match_reference():
    compiled = Timed().compile(target=AutoSuiteTarget())
    before = to_json(compiled.semantic_ir)
    assert compiled.semantic_ir == compiled.specialized_ir
    wire = TimingWire(compiled.artifact.content)
    wire.run()
    assert wire.now == 7
    assert wire.waits == [(0, 2), (2, 5), (5, 5), (5, 7)]
    clock = VirtualClock()
    Interpreter(from_json(before), environment=ReferenceEnvironment(clock=clock)).run()
    assert clock.monotonic() == wire.now
    assert to_json(compiled.semantic_ir) == before
    starts = wire.root.findall(".//*[@typeid='Chemspeed.SATaskSetTimer.1']")
    assert len({n.findtext("timername") for n in starts}) == 1
    assert len({n.findtext("id") for n in starts}) == 2
    macro = wire.root.find(".//*[@typeid='Chemspeed.SAMacroTask.1']")
    assert macro is not None  # Timer-only functions still own a native scope.


def test_composed_instances_receive_distinct_native_timer_names():
    class Caller(Function):
        def __init__(self):
            self.first = Timed()
            self.second = Timed()

        @runtime
        def run(self) -> None:
            self.first()
            self.second()

    wire = TimingWire(Caller().compile(target=AutoSuiteTarget()).artifact.content)
    wire.run()
    assert wire.now == 14
    assert len(wire.origins) == 2


def test_native_scope_rejection_preserves_broader_reference_semantics():
    class Joined(Function):
        timer: Timer
        enabled: Input[bool]

        @runtime
        def run(self) -> None:
            if self.enabled:
                self.timer.start()
            else:
                self.timer.start()
            self.timer.wait_until(5 * s)

    for enabled in (True, False):
        clock = VirtualClock()
        Interpreter(Joined().to_ir(), environment=ReferenceEnvironment(clock=clock)).run(inputs={"enabled": enabled})
        assert clock.monotonic() == 5
    with pytest.raises(CompilationError, match="unsupported_timer_scope"):
        Joined().compile(target=AutoSuiteTarget())


def test_parent_macro_timer_is_visible_in_descendant_wait():
    class Nested(Function):
        timer: Timer
        enabled: Input[bool]

        @runtime
        def run(self) -> None:
            self.timer.start()
            if self.enabled:
                self.timer.wait_until(5 * s)

    wire = TimingWire(Nested().compile(target=AutoSuiteTarget()).artifact.content)
    wire.run({"enabled": True})
    assert wire.now == 5


def test_nested_reset_is_rejected_even_when_there_is_no_wait():
    class Reset(Function):
        timer: Timer
        enabled: Input[bool]

        @runtime
        def run(self) -> None:
            self.timer.start()
            if self.enabled:
                self.timer.start()

    result = Interpreter(Reset().to_ir(), environment=ReferenceEnvironment(clock=VirtualClock())).run(
        inputs={"enabled": True}
    )
    assert len(result.events) == 2
    with pytest.raises(CompilationError, match="unsupported_timer_scope"):
        Reset().compile(target=AutoSuiteTarget())


@pytest.mark.parametrize("duration", [-1 * s, 80_000 * hour])
def test_out_of_range_literal_is_rejected(duration):
    class Outside(Function):
        def __init__(self):
            self.duration = duration

        @runtime
        def run(self) -> None:
            wait(self.duration)

    with pytest.raises(CompilationError, match="wait_duration"):
        Outside().compile(target=AutoSuiteTarget())


@pytest.mark.requires_corpus
def test_wait_and_timer_envelopes_match_primary_app_with_explicit_cancel_override():
    native = ET.fromstring(gzip.decompress(corpus_file("app/config20260909_polymerization.app").read_bytes()))
    generated = ET.fromstring(Timed().compile(target=AutoSuiteTarget()).artifact.content)
    for kind, mode in (
        ("Chemspeed.SATaskSetTimer.1", None),
        ("Chemspeed.SATaskWait.1", "0"),
        ("Chemspeed.SATaskWait.1", "2"),
    ):
        source = next(
            n for n in native.iter() if n.get("typeid") == kind and (mode is None or n.findtext("waitmode") == mode)
        )
        output = next(
            n for n in generated.iter() if n.get("typeid") == kind and (mode is None or n.findtext("waitmode") == mode)
        )
        assert [c.tag for c in output] == [c.tag for c in source]
        for child in source:
            if child.tag not in {
                "id",
                "edittime",
                "name",
                "description",
                "time",
                "timeunit",
                "timername",
                "cancelwait",
            }:
                assert output.findtext(child.tag) == (child.text or "")
        if mode is not None:
            assert output.findtext("cancelwait") == "0"  # Manual option, not the observed corpus default.
            assert output.findtext("timeunit") == "s"
