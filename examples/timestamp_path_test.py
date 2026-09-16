"""Learning artifacts match their source and deterministic reference behavior."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualWallClock
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteTarget
from .developer.wall_time_ir import build_program
from .timestamp_path import TimestampPath


def test_timestamp_path_and_companion():
    program = TimestampPath().to_ir()
    clock = VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone(timedelta(hours=9))))
    for candidate in (program, from_json(to_json(program))):
        result = Interpreter(candidate, environment=ReferenceEnvironment(wall_clock=clock)).run(
            inputs={"directory": "results"}
        )
        assert result.outputs == {"stamp": "2026-09-16_140506", "path": "results/2026-09-16_140506.csv"}
        assert len(result.events) == 1
    companion = Path(__file__).with_name("timestamp_path.asfp")
    assert TimestampPath().compile(target=AutoSuiteTarget()).artifact.content == companion.read_bytes()


def test_developer_wall_time_companion():
    companion = Path(__file__).with_name("developer") / "wall_time_ir.json"
    program = build_program()
    assert to_json(program) == companion.read_text(encoding="utf-8")
    assert from_json(companion.read_text(encoding="utf-8")) == program
