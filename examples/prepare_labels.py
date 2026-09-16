"""For experiment authors: prepare sample labels from comma-separated text.

Run: uv run python examples/prepare_labels.py
Expected terminal output:
    prepare_labels.asfp

When the generated function receives name=" Sample A,extra ", it returns
label="Sample A_processed" and labels=["Sample A_processed", "ready"].
Compilation writes the procedure; it does not read samples or run hardware.
The complete generated function package is prepare_labels.asfp beside this file.
"""

from pathlib import Path

from sciloom import Function, Input, Output, runtime, text
from sciloom_autosuite import AutoSuiteTarget


class PrepareLabels(Function):
    """Clean a supplied name and prepare labels for later steps.

    Attributes:
        name: Supplied text; only the first comma-separated part is used.
        label: Cleaned first part with a suffix.
        labels: Independent list containing the label and a readiness label.
    """

    name: Input[str]
    label: Output[str]
    labels: Output[list[str]]

    @runtime
    def run(self) -> None:
        self.label = text.trim(self.name)
        self.label = text.split_part(self.label, ",", 0) + "_processed"
        self.labels = [self.label, "ready"]


if __name__ == "__main__":
    path = PrepareLabels().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
