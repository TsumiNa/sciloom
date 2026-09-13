"""Experiment-author example: compile a list-copying and scaling function.

Run: uv run python examples/scale_values.py
Output:
    scale_values.asfp

The full generated package is the same-name .asfp companion. Input [1, 2, 3]
with factor 2.5 produces [2.5, 5, 7.5], leaving the input unchanged. Reference
execution and emitted-task scheduling are checked in developer tests; real
AutoSuite Executor acceptance remains a separate platform gate.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, runtime
from sciloom_autosuite import AutoSuiteTarget


class ScaleValues(Function):
    """Copy input values and multiply each element by a factor.

    Attributes:
        values: Input numeric list.
        factor: Scale factor.
        result: Independent scaled list.
        index: Internal loop position.
    """

    values: Input[list[float]]
    factor: Input[float]
    result: Output[list[float]]
    index: Var[int] = 0
    batch_size: int = 8

    @runtime
    def run(self) -> None:
        self.result = self.values
        self.index = 0
        while self.index < len(self.result):
            self.result[self.index] *= self.factor
            self.index += 1


if __name__ == "__main__":
    path = ScaleValues().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
