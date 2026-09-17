"""Author example: calculate typed flow and clearance without moving liquid.

Run: uv run python examples/transfer_settings.py
Output: AutoSuite flow/length encoding awaits native validation.

The declared calculation has reference results of 1e-6 m3/s and 0.002 metres
for factor=60. The developer transfer_values_ir example executes that calculation.
Native transfer needs an independently evidenced deployment profile.
"""

from sciloom import FlowRate, Function, Input, Length, Output, mL_per_min, mm, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class TransferSettings(Function):
    factor: Input[float]
    flow: Output[FlowRate]
    clearance: Output[Length]

    @runtime
    def run(self) -> None:
        self.flow = self.factor * mL_per_min
        self.clearance = 2 * mm


if __name__ == "__main__":
    try:
        TransferSettings().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not all(d.code == "unsupported_transfer_quantity" for d in error.diagnostics):
            raise
        print("AutoSuite flow/length encoding awaits native validation.")
