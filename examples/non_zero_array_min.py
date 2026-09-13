"""Experiment-author example: compile a numeric Non Zero Array Min function.

Run: uv run python examples/non_zero_array_min.py
Output:
    non_zero_array_min.asfp

The complete generated package is beside this file. For input [0, 4, 2, 0],
the algorithm returns 2; empty/all-zero input returns the sentinel 999999.
The developer tests verify these results with the reference interpreter.

Source: autosuite/extracted/latest_app/functions/51_Non Zero Array Min.asfp,
extracted from config20260909_polymerization.app. This numeric adaptation removes
volume units, retains the numeric 1e-8 threshold and 999999 sentinel, and uses
nested conditions to express short-circuit intent. It does not model physical
volume conversions. Compilation is not AutoSuite Executor simulation.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, runtime
from sciloom_autosuite import AutoSuiteTarget


class NonZeroArrayMin(Function):
    """Find the smallest value above the threshold, capped at the sentinel.

    Attributes:
        values: Dimensionless numeric samples.
        minimum: Smallest qualifying value, or 999999 if none is smaller.
        index: Internal position, explicitly reset for every invocation.
    """

    values: Input[list[float]]
    minimum: Output[float]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.minimum = 999999.0
        self.index = 0
        while self.index < len(self.values):
            if self.values[self.index] > 1e-8:
                if self.values[self.index] < self.minimum:
                    self.minimum = self.values[self.index]
            self.index += 1


if __name__ == "__main__":
    path = NonZeroArrayMin().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
