"""For experiment authors: configure and request one explicit single-well transfer.

Run: ``uv run python examples/transfer_sample.py``
Output: ``AutoSuite transfer profile awaits native validation.``

Source and destination are runtime Zone inputs. Both flows and the air gap are
explicit. The developer transfer_sample_ir example supplies trusted reference
locations and tool capacity; it records intent without simulating liquid motion.
No AutoSuite transfer profile is available in this stage.
"""

from sciloom import Function, Input, LiquidHandler, Zone, log, mL, mL_per_min, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class TransferSample(Function):
    """Transfer 0.25 mL, then log only after the command succeeds."""

    liquid: LiquidHandler
    source: Input[Zone]
    destination: Input[Zone]

    @runtime
    def run(self) -> None:
        self.liquid.aspirate_flow = 1 * mL_per_min
        self.liquid.dispense_flow = 2 * mL_per_min
        self.liquid.air_gap = 0.05 * mL
        self.liquid.transfer(self.source, self.destination, 0.25 * mL)
        log("transfer complete", category="liquid", stream="experiment")


if __name__ == "__main__":
    try:
        TransferSample().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "missing_resource_binding" for d in error.diagnostics):
            raise
        print("AutoSuite transfer profile awaits native validation.")
    else:
        raise AssertionError("No native transfer profile has been validated.")
