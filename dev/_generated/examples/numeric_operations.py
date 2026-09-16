"""Experiment-author example: calculate whole portions and a volume difference.

Run from the repository root::

    uv run python examples/numeric_operations.py

Terminal output::

    numeric_operations.asfp

With amount=2.5*mL and reference=3*mL, the generated function returns
whole_portions=2 and difference=0.5*mL (subject to floating rounding).
One portion is 1 mL here; this is a calculation, not a liquid-transfer operation.
The complete generated package is beside this file as numeric_operations.asfp.
"""

from math import floor
from pathlib import Path

from sciloom import Function, Input, Output, Volume, mL, runtime
from sciloom_autosuite import AutoSuiteTarget


class CalculatePortions(Function):
    """Calculate the number of whole 1 mL portions and distance from a reference.

    Attributes:
        amount: Supplied volume to divide into portions.
        reference: Volume used for comparison.
        whole_portions: Number rounded down after conversion to millilitres.
        difference: Absolute volume difference from the reference.
    """

    amount: Input[Volume]
    reference: Input[Volume]
    whole_portions: Output[int]
    difference: Output[Volume]

    @runtime
    def run(self) -> None:
        self.whole_portions = floor(self.amount / mL)
        self.difference = abs(self.amount - self.reference)


if __name__ == "__main__":
    path = CalculatePortions().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
