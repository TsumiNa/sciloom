"""For experiment authors: capture a barcode for exactly one known well.

Run: ``uv run python examples/capture_barcode.py``
Output: ``AutoSuite barcode workflow awaits native dialog validation.``

The well-name query validates a single known well before requesting input. An
accepted string, including empty text, is saved as sample_ID and logged. Cancel,
Stop or timeout prevents the write and log. Compilation remains gated; the
developer barcode_ir example supplies explicit reference services and responses.
"""

from sciloom import Function, Input, Output, Var, WellProperty, Zone, log, request_text, runtime, s, zones
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class CaptureBarcode(Function):
    """Associate a supplied operator label with one known well.

    Attributes:
        well: Exactly one well; checked before interaction.
        barcode: Accepted text.
        well_name: Captured display name used in the prompt.
        sample_id: Stored metadata declaration.
    """

    well: Input[Zone]
    barcode: Output[str]
    well_name: Var[str] = ""

    def __init__(self) -> None:
        self.sample_id = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        self.well_name = zones.well_name(self.well)
        self.barcode = request_text("Barcode for " + self.well_name, timeout=30 * s)
        self.sample_id[self.well] = self.barcode
        log(self.barcode, category="samples", stream="barcode")


if __name__ == "__main__":
    try:
        CaptureBarcode().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(
            d.code not in {"unsupported_dialog_result", "unsupported_zone_cardinality"} for d in error.diagnostics
        ):
            raise
        print("AutoSuite barcode workflow awaits native dialog validation.")
    else:
        raise AssertionError("Update only after native interaction and location acceptance.")
