"""For experiment authors: capture a barcode and a separate yes/no decision.

Run: ``uv run python examples/identify_sample.py``
Expected terminal output: ``AutoSuite dialog results remain gated.``

The function expresses supported SciLoom semantics. AutoSuite generation is
rejected until native result and termination evidence is available; this example
does not prompt, execute equipment or write an ASFP. The developer companion
``examples.developer.dialogs_ir`` demonstrates explicit reference responses.
"""

from sciloom import Function, Output, ask_yes_no, request_text, runtime, s
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class IdentifySample(Function):
    """Collect a label and an independent operator decision.

    Attributes:
        barcode: Accepted text, possibly empty.
        accepted: True for Yes and False for No; neither implies cancellation.
    """

    barcode: Output[str]
    accepted: Output[bool]

    @runtime
    def run(self) -> None:
        self.barcode = request_text("Scan barcode", timeout=30 * s)
        self.accepted = ask_yes_no("Use this sample?")


if __name__ == "__main__":
    try:
        IdentifySample().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        assert all(d.code == "unsupported_dialog_result" for d in error.diagnostics)
        print("AutoSuite dialog results remain gated.")
    else:
        raise AssertionError("Update this example only after native acceptance unlocks dialog results.")
