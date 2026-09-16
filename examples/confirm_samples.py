"""For experiment authors: request confirmation before recording a ready sample.

Run: ``uv run python examples/confirm_samples.py``
Terminal output: ``confirm_samples.asfp``

When AutoSuite calls the generated function with sample="A", it displays
"Sample A is ready. Confirm to continue." Only after OK does it record
recipe/confirmed="A". Compilation writes confirm_samples.asfp beside this file;
it does not display a dialog or execute the experiment.
"""

from pathlib import Path

from sciloom import Function, Input, log, notify, runtime
from sciloom_autosuite import AutoSuiteTarget


class ConfirmSamples(Function):
    """Ask the operator to acknowledge a sample before the next step.

    Attributes:
        sample: Label included in the message and subsequent log.
    """

    sample: Input[str]

    @runtime
    def run(self) -> None:
        notify("Sample " + self.sample + " is ready. Confirm to continue.")
        log(self.sample, category="recipe", stream="confirmed")


if __name__ == "__main__":
    path = ConfirmSamples().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
