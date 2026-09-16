"""For experiment authors: record supplied sample names and volumes.

Run: ``uv run python examples/record_values.py``
Terminal output: ``record_values.asfp``

Calling the generated function with sample="A" and amount=1 mL records
recipe/sample="A", followed by A/volume=1 mL. These are supplied values, not
instrument measurements. Compilation writes the complete record_values.asfp
companion beside this source; it does not execute the log operations.
"""

from pathlib import Path

from sciloom import Function, Input, Volume, log, runtime
from sciloom_autosuite import AutoSuiteTarget


class RecordValues(Function):
    """Record a sample label and its supplied volume.

    Attributes:
        sample: Label used as the volume log's category.
        amount: Volume supplied by the runtime caller.
    """

    sample: Input[str]
    amount: Input[Volume]

    @runtime
    def run(self) -> None:
        log(self.sample, category="recipe", stream="sample")
        log(self.amount, category=self.sample, stream="volume")


if __name__ == "__main__":
    path = RecordValues().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
