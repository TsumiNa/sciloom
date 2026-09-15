"""Reference behaviour and generated package for this lesson."""

from pathlib import Path

from examples.tutorial.choose_stirring_speed import StirRack
from sciloom import rpm
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


def session():
    compiled = StirRack().compile(
        target=AutoSuiteTarget(
            devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
        ),
    )
    assert compiled.artifact.content == Path(__file__).with_name("choose_stirring_speed.asfp").read_bytes()
    return Interpreter(compiled.specialized_ir)


def test_volume_threshold_and_disabled_branch():
    runtime = session()
    for volume, speed in ((1.5, 300), (2.0, 600), (3.0, 600)):
        result = runtime.run(inputs={"volume": volume, "enabled": True})
        assert result.resources["resource:shaker"].applied_configuration == {"speed": speed * rpm}
    stopped = runtime.run(inputs={"volume": 1.0, "enabled": False})
    assert not stopped.resources["resource:shaker"].enabled
    assert [e.operation_id for e in stopped.events] == ["sciloom.agitator.stop/v1"]
