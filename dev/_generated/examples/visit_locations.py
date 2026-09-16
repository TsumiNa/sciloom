"""For experiment authors: visit each selected well and count the visits.

Run: ``uv run python examples/visit_locations.py``
Expected terminal output: ``visit_locations.asfp``

The caller supplies a Zone when AutoSuite executes the generated function. A
selection of three wells produces count=3 and last containing the third well.
An empty selection produces count=0 and leaves the previous well unchanged;
on the first call that value is empty. No hardware is moved or started.

visit_locations.asfp is the complete generated companion. Sequential Macro XML
matches the supplied corpus; Executor simulation remains a separate check.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, Zone, runtime
from sciloom_autosuite import AutoSuiteTarget


class VisitLocations(Function):
    """Count wells in their selection order.

    Attributes:
        rack: Ordered wells supplied by the runtime caller.
        well: Current one-well selection; retained after the loop and across calls.
        count: Visits during this call, reset explicitly before iteration.
        last: Final saved well, including the previous value for an empty rack.
    """

    rack: Input[Zone]
    well: Var[Zone] = Zone.empty()
    count: Output[int]
    last: Output[Zone]

    @runtime
    def run(self) -> None:
        self.count = 0
        for self.well in self.rack:
            self.count += 1
        self.last = self.well


if __name__ == "__main__":
    path = VisitLocations().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
