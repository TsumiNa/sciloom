"""The first lesson generates the documented package and requests one start."""

from pathlib import Path

from examples.tutorial.start_shaker import StirRack
from sciloom import rpm
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


def test_fixed_speed_start_and_companion():
    result = StirRack().compile(
        target=AutoSuiteTarget(
            devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
        ),
    )
    assert result.artifact.content == Path(__file__).with_name("start_shaker.asfp").read_bytes()
    snapshot = Interpreter(result.specialized_ir).run(inputs={})
    assert [event.operation_id for event in snapshot.events] == [
        "sciloom.agitator.speed/v1",
        "sciloom.agitator.start/v1",
    ]
    configured, started = (event.state for event in snapshot.events)
    assert configured.configuration == {"speed": 300 * rpm}
    assert not configured.enabled
    assert configured.applied_configuration == {}
    assert started.enabled
    assert started.applied_configuration == {"speed": 300 * rpm}
