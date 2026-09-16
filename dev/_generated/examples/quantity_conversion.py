"""Calculate an amount and a time difference using explicit units.

Run: ``uv run python examples/quantity_conversion.py``
Terminal output: ``quantity_conversion.asfp``

For amount=1 mL, extra_ml=2 and elapsed=90 s, reference execution returns
total=3 mL, total_ml=3 and difference=-30 s (subject to floating rounding).
Compilation writes the complete same-name ASFP companion beside this file.
"""

from pathlib import Path

from sciloom import Duration, Function, Input, Output, Volume, minute, mL, runtime
from sciloom_autosuite import AutoSuiteTarget


class QuantityConversion(Function):
    """Add a requested volume and calculate a time difference.

    Attributes:
        amount: Starting volume supplied by the caller.
        extra_ml: Number of millilitres to add.
        elapsed: Supplied elapsed time.
        total: Combined volume.
        total_ml: Combined volume expressed as a plain number of millilitres.
        difference: One minute minus the supplied elapsed time.
    """

    amount: Input[Volume]
    extra_ml: Input[float]
    elapsed: Input[Duration]
    total: Output[Volume]
    total_ml: Output[float]
    difference: Output[Duration]

    @runtime
    def run(self) -> None:
        self.total = self.amount + self.extra_ml * mL
        self.total_ml = self.total / mL
        self.difference = 1 * minute - self.elapsed


if __name__ == "__main__":
    path = QuantityConversion().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
