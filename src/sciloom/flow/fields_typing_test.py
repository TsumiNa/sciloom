"""Native field aliases retain values and runtime decorators retain signatures."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


@pytest.mark.parametrize("valid", [True, False])
def test_native_declaration_type_contract(tmp_path, valid):
    source = """
from collections.abc import Callable
from math import floor
from typing import assert_type
from sciloom import Agitator, Duration, Function, Input, Output, RotationalSpeed, Timer, Var, Volume, WellProperty, Zone, at, log, mL, minute, notify, now_text, rpm, runtime, s, text, wait, zones
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import Program

class Scale(Function):
    factor: Input[float]
    values: Input[list[float]]
    result: Output[list[float]]
    index: Var[int] = 0
    flags: Var[list[bool]] = [True]
    speeds: Var[list[RotationalSpeed]] = [60 * rpm]
    agitator: Agitator
    name: Input[str]
    labels: Var[list[str]] = ["A"]
    amount: Input[Volume]
    elapsed: Var[Duration] = 1 * minute
    amounts: Var[list[Volume]] = [1 * mL]
    timer: Timer
    location: Var[Zone] = Zone.empty()
    label = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        assert_type(self.factor, float)
        with at(self.agitator, self.location):
            self.agitator.start()
        self.label[self.location] = "A"
        assert_type(self.label.get(self.location), str)
        assert_type(self.label.get(self.location, default=""), str)
        assert_type(self.location, Zone)
        assert_type(zones.find(self.name), Zone)
        assert_type(zones.combine(self.location, Zone.empty()), Zone)
        assert_type(zones.well_name(self.location), str)
        assert_type(len(self.location), int)
        assert_type(self.location[0], Zone)
        for self.location in zones.fragments(self.location, size=2):
            assert_type(self.location, Zone)
        for self.location in self.location:
            assert_type(self.location, Zone)
        assert_type(self.index, int)
        assert_type(self.values, list[float])
        assert_type(self.name, str)
        assert_type(self.labels, list[str])
        assert_type(self.amount, Volume)
        assert_type(self.amount / mL, float)
        assert_type(self.factor * mL, Volume)
        assert_type(self.elapsed - 1 * s, Duration)
        assert_type(abs(self.amount), Volume)
        assert_type(abs(self.elapsed), Duration)
        assert_type(abs(self.index), int)
        assert_type(abs(self.factor), float)
        assert_type(floor(self.factor), int)
        assert_type(round(self.factor), int)
        self.amount = self.amount + 1 * mL
        self.elapsed = self.elapsed / 2
        self.name = text.trim(self.name)
        self.name = text.split_part(self.name, ",", 0)
        self.result = self.values
        self.result[self.index] *= self.factor
        self.agitator.speed = self.speeds[0]
        self.agitator.start()
        self.agitator.stop()

        notify(self.name)
        notify(message="Ready?")
        self.name = now_text("%Y-%m-%d")
        assert_type(now_text(format="%H%M%S"), str)
        assert_type(self.timer, Timer)
        self.timer.start()
        wait(self.elapsed)
        self.timer.wait_until(duration=5 * s)
        log(self.amount, category=self.name, stream="volume")
        log(self.elapsed, category="recipe", stream="time")
        log(self.factor, category="recipe", stream="factor")

callback: Callable[[], None] = Scale().run
def check_inputs(program: Program, values: list[float], flags: list[bool], speeds: list[RotationalSpeed]) -> None:
    Interpreter(program).run(inputs={"values": values, "flags": flags, "speeds": speeds})
"""
    if not valid:
        source += """
wrong_callback: Callable[[int], str] = Scale().run
class Bad(Function):
    label = WellProperty("sample_ID", str)
    invalid_label = WellProperty("bad", int)
    timer: Timer
    location: Var[Zone] = 1
    amount: Var[Volume] = 1.0
    elapsed: Var[Duration] = 1 * mL
    factor: Input[float]
    name: Input[str]
    labels: Var[list[str]] = ["A", 3]
    index: Var[int] = "text"
    values: Var[list[float]] = [1.0, "text"]
    agitator: Agitator
    @runtime
    def run(self) -> None:
        with at(self.agitator, "rack"):
            pass
        with at(self.factor, self.location):
            pass
        self.label[self.location] = 3
        self.label.get(self.location, default=3)
        self.label.get("rack")
        self.amount = self.elapsed
        self.location = "rack"
        zones.combine(self.location, 0)
        self.location["0"]
        zones.fragments(self.location, size="2")
        self.amount = self.amount + self.elapsed
        floor(self.amount)
        round(self.elapsed)
        abs(self.name)
        notify(3)
        now_text(3)
        wait(2)
        self.timer.wait_until(2)
        self.timer.start(1)
        self.factor = now_text("%Y")
        log(self.values, category="recipe", stream="values")
        log(self.factor, category=3, stream="factor")
        self.factor = "text"
        self.name = 3
        text.trim(3)
        self.index = 1.5
        self.values = ["text"]
        self.agitator.speed = 1.0
        self.agitator.start()
        self.agitator.stop()
        self.index = "still checked after stop"
"""
    path = tmp_path / "declaration_contract.py"
    path.write_text(textwrap.dedent(source))
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(root / "pyproject.toml"),
            "--cache-dir",
            str(tmp_path / "cache"),
            str(path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if valid:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert result.stdout.count(" error: ") == 37, result.stdout
        for code in ("[assignment]", "[list-item]"):
            assert code in result.stdout
