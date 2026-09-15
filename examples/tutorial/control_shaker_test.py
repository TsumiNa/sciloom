"""Reference behaviour and generated package for this lesson."""

from pathlib import Path

from examples.tutorial.control_shaker import StirRack
from sciloom import rpm
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


def session():
    compiled = StirRack().compile(
        target=AutoSuiteTarget(
            devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
        ),
    )
    assert compiled.artifact.content == Path(__file__).with_name("control_shaker.asfp").read_bytes()
    return Interpreter(compiled.specialized_ir)


def test_speed_input_and_stop_preserve_the_saved_configuration():
    runtime = session()
    started = runtime.run(inputs={"speed": 450 * rpm, "enabled": True})
    stopped = runtime.run(inputs={"speed": 0 * rpm, "enabled": False})
    state = stopped.resources["resource:shaker"]
    assert started.resources["resource:shaker"].applied_configuration == {"speed": 450 * rpm}
    assert not state.enabled
    assert state.configuration == state.applied_configuration == {"speed": 450 * rpm}
    assert [e.operation_id for e in stopped.events] == ["sciloom.agitator.stop/v1"]
    zero = runtime.run(inputs={"speed": 0 * rpm, "enabled": True})
    assert zero.resources["resource:shaker"].enabled
    assert zero.resources["resource:shaker"].applied_configuration == {"speed": 0 * rpm}
