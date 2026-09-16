"""Environment ownership, chronological histories and missing-service failures."""

from dataclasses import FrozenInstanceError

import pytest

from sciloom import Agitator, Function, Input, Output, rpm, runtime
from sciloom.core.diagnostics import ExecutionError, SourceSpan
from sciloom.core.ir import Literal, ScalarType, from_json, to_json
from .environment import ReferenceEnvironment, _require_service
from .runtime import Interpreter
from .runtime_agitation_test import direct_agitation


def test_default_environments_and_device_state_are_session_owned():
    program = direct_agitation()
    before = to_json(program)
    first = Interpreter(program)
    second = Interpreter(program)
    assert first.environment is not second.environment
    first.run(inputs={"speed": 300 * rpm, "enabled": True})
    assert len(first.environment.events) == 2
    assert second.environment.events == ()
    stopped = second.run(inputs={"speed": 300 * rpm, "enabled": False})
    assert not stopped.resources["mixer"].enabled
    assert not stopped.resources["mixer"].configuration
    assert first.environment.events[-1].state.enabled
    assert to_json(program) == before


def test_explicit_environment_sharing_preserves_per_run_snapshots():
    environment = ReferenceEnvironment()
    program = from_json(to_json(direct_agitation()))
    first = Interpreter(program, environment=environment)
    second = Interpreter(program, environment=environment)
    assert first.environment is second.environment is environment
    started = first.run(inputs={"speed": 300 * rpm, "enabled": True})
    old_history = environment.events
    stopped = second.run(inputs={"speed": 600 * rpm, "enabled": False})
    restarted = first.run(inputs={"speed": 600 * rpm, "enabled": True})
    assert environment.events == started.events + stopped.events + restarted.events
    assert old_history == started.events
    assert len(old_history) == 2
    assert len(stopped.events) == 1
    assert not stopped.resources["mixer"].configuration  # Shared environment is not shared device state.
    assert old_history[-1].state.configuration["speed"] == 300 * rpm
    assert restarted.events[-1].state.configuration["speed"] == 600 * rpm
    with pytest.raises(TypeError):
        old_history[-1].state.configuration["speed"] = 900 * rpm
    with pytest.raises(FrozenInstanceError):
        old_history[-1].state.enabled = False


def test_failure_retains_completed_events_and_stops_later_operations():
    class Interrupted(Function):
        shaker: Agitator
        divisor: Input[float]
        result: Output[float]

        @runtime
        def run(self) -> None:
            self.shaker.speed = 300 * rpm
            self.shaker.start()
            self.result = 1.0 / self.divisor
            self.shaker.stop()

    environment = ReferenceEnvironment()
    session = Interpreter(Interrupted().to_ir(), environment=environment)
    with pytest.raises(ExecutionError, match="numeric_error"):
        session.run(inputs={"divisor": 0.0})
    failed_history = environment.events
    assert len(failed_history) == 2
    assert failed_history[-1].state.enabled
    completed = session.run(inputs={"divisor": 2.0})
    assert len(completed.events) == 3
    assert completed.outputs == {"result": 0.5}
    assert not completed.events[-1].state.enabled
    assert environment.events == failed_history + completed.events
    assert failed_history[-1].state.enabled


def test_missing_service_keeps_the_requesting_node_and_source():
    source = SourceSpan(path="experiment.py", line=17)
    request = Literal(node_id="request", source=source, type=ScalarType.TEXT, value="recipe.csv")
    with pytest.raises(ExecutionError) as error:
        _require_service(None, "files", request)
    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == "missing_environment_service"
    assert "files" in diagnostic.message
    assert diagnostic.node_id == "request"
    assert diagnostic.source is source
    supplied = object()
    assert _require_service(supplied, "files", request) is supplied
