"""Timer examples keep their artifacts reproducible and device intent explicit."""

from pathlib import Path

from sciloom import rpm
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualClock, WaitEvent
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from .developer.timing_ir import build_program
from .timed_agitation import TimedAgitation


def test_timed_agitation_companion_and_five_second_reference_behavior():
    compiled = TimedAgitation().compile(
        target=AutoSuiteTarget(
            devices={
                "shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
            }
        )
    )
    assert compiled.artifact.content == Path(__file__).with_name("timed_agitation.asfp").read_bytes()
    for program in (compiled.specialized_ir, from_json(to_json(compiled.specialized_ir))):
        clock = VirtualClock()
        result = Interpreter(program, environment=ReferenceEnvironment(clock=clock)).run()
        assert clock.monotonic() == 5
        assert [(e.started_at, e.finished_at) for e in result.events if isinstance(e, WaitEvent)] == [(0, 2), (2, 5)]
        shaker = result.resources["resource:shaker"]
        assert not shaker.enabled
        assert shaker.applied_configuration["speed"] == 300 * rpm
        assert len(result.resources) == 1


def test_direct_timer_json_companion():
    path = Path(__file__).with_name("developer") / "timing_ir.json"
    assert path.read_text(encoding="utf-8") == to_json(build_program())
    clock = VirtualClock()
    Interpreter(from_json(path.read_text(encoding="utf-8")), environment=ReferenceEnvironment(clock=clock)).run()
    assert clock.monotonic() == 5
