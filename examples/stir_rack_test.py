"""Execute the tutorial's stirring program and check both device branches."""

from pathlib import Path

import pytest

from examples.stir_rack import StirRack
from sciloom import rpm
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget

SHAKER = "resource:shaker"


@pytest.fixture
def compiled():
    target = AutoSuiteTarget(devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})
    return StirRack().compile(target=target)


def counter(result, program):
    function = next(f for f in program.functions if f.name == "CountStirs")
    return result.state[function.node_id][f"{function.node_id}:var:stirs"]


def test_enabled_rack_starts_at_the_speed_chosen_for_its_largest_sample(compiled):
    session = Interpreter(compiled.specialized_ir)

    fast = session.run(inputs={"volumes": [1.0, 2.5, 0.5], "enabled": True})
    assert [event.operation_id for event in fast.events] == ["sciloom.agitator.speed/v1", "sciloom.agitator.start/v1"]
    assert fast.resources[SHAKER].enabled
    assert fast.resources[SHAKER].applied_configuration == {"speed": 600 * rpm}

    gentle = session.run(inputs={"volumes": [1.0, 1.5], "enabled": True})
    assert gentle.resources[SHAKER].applied_configuration == {"speed": 300 * rpm}

    empty = session.run(inputs={"volumes": [], "enabled": True})
    assert empty.resources[SHAKER].applied_configuration == {"speed": 300 * rpm}
    assert counter(empty, compiled.specialized_ir) == 3


def test_disabled_rack_stops_without_counting(compiled):
    session = Interpreter(compiled.specialized_ir)
    started = session.run(inputs={"volumes": [3.0], "enabled": True})
    stopped = session.run(inputs={"volumes": [3.0], "enabled": False})

    assert [event.operation_id for event in stopped.events] == ["sciloom.agitator.stop/v1"]
    assert not stopped.resources[SHAKER].enabled
    assert stopped.resources[SHAKER].applied_configuration == started.resources[SHAKER].applied_configuration
    assert counter(started, compiled.specialized_ir) == counter(stopped, compiled.specialized_ir) == 1


def test_committed_package_carries_both_agitation_branches(compiled):
    package = compiled.artifact.content.decode("utf-8")
    assert Path(__file__).with_name("stir_rack.asfp").read_bytes() == compiled.artifact.content
    assert package.count("<switchon>1</switchon>") == 1
    assert package.count("<switchon>0</switchon>") == 1
