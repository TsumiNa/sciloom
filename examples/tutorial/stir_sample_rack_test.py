"""Reference behaviour and generated package for this lesson."""

from pathlib import Path

from examples.tutorial.stir_sample_rack import StirRack
from sciloom import rpm
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


def session():
    compiled = StirRack().compile(
        target=AutoSuiteTarget(
            devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
        ),
    )
    assert compiled.artifact.content == Path(__file__).with_name("stir_sample_rack.asfp").read_bytes()
    return Interpreter(compiled.specialized_ir)


def test_new_input_list_resets_loop_and_empty_list_selects_low_speed():
    runtime = session()
    volumes = [1.0, 2.5, 0.5]
    first = runtime.run(inputs={"volumes": volumes, "enabled": True})
    assert first.resources["resource:shaker"].applied_configuration == {"speed": 600 * rpm}
    assert volumes == [1.0, 2.5, 0.5]
    for values, speed in (([1.5], 300), ([3.5], 600), ([], 300)):
        later = runtime.run(inputs={"volumes": values, "enabled": True})
        assert later.resources["resource:shaker"].applied_configuration == {"speed": speed * rpm}
    stopped = runtime.run(inputs={"volumes": [], "enabled": False})
    assert not stopped.resources["resource:shaker"].enabled
    assert first.resources["resource:shaker"].applied_configuration == {"speed": 600 * rpm}
