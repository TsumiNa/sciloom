"""Native field aliases retain values and runtime decorators retain signatures."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("valid", [True, False])
def test_native_declaration_type_contract(tmp_path, valid):
    source = """
from collections.abc import Callable
from typing import assert_type
from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import Program

class Scale(Function):
    factor: Input[float]
    values: Input[list[float]]
    result: Output[list[float]]
    index: Var[int] = 0
    flags: Var[list[bool]] = [True]
    speeds: Var[list[RotationalSpeed]] = [60 * rpm]
    agitator = Agitator("mixer")

    @runtime
    def run(self) -> None:
        assert_type(self.factor, float)
        assert_type(self.index, int)
        assert_type(self.values, list[float])
        self.result = self.values
        self.result[self.index] *= self.factor
        self.agitator.set_speed(self.speeds[0])
        self.agitator.stop()

callback: Callable[[], None] = Scale().run
def check_inputs(program: Program, values: list[float], flags: list[bool], speeds: list[RotationalSpeed]) -> None:
    Interpreter(program).run(inputs={"values": values, "flags": flags, "speeds": speeds})
"""
    if not valid:
        source += """
wrong_callback: Callable[[int], str] = Scale().run
class Bad(Function):
    factor: Input[float]
    index: Var[int] = "text"
    values: Var[list[float]] = [1.0, "text"]
    agitator = Agitator("mixer")
    @runtime
    def run(self) -> None:
        self.factor = "text"
        self.index = 1.5
        self.values = ["text"]
        self.agitator.set_speed(1.0)
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
        assert result.stdout.count(" error: ") == 8, result.stdout
        for code in ("[assignment]", "[list-item]", "[arg-type]"):
            assert code in result.stdout
