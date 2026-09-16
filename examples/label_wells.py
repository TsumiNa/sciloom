"""For experiment authors: store a sample label on selected wells.

Run: ``uv run python examples/label_wells.py``
Expected terminal output: ``label_wells.asfp``

The AutoSuite caller supplies rack and label. The function writes the same text
to all selected wells, then reads it back one well at a time. last_label is the
last text read, or an empty string for an empty rack. These are stored sample
metadata, not measured values. The complete package is label_wells.asfp beside
this file; deployment still requires Executor simulation.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, WellProperty, Zone, runtime
from sciloom_autosuite import AutoSuiteTarget


class LabelWells(Function):
    """Give selected wells the same sample identifier.

    Attributes:
        rack: Wells supplied by the runtime caller.
        label: Text to store on every selected well.
        well: Current single-well selection during readback.
        last_label: Last label read; empty when no wells are selected.
    """

    rack: Input[Zone]
    label: Input[str]
    well: Var[Zone] = Zone.empty()
    last_label: Output[str]

    def __init__(self) -> None:
        self.sample_label = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        self.sample_label[self.rack] = self.label
        self.last_label = ""
        for self.well in self.rack:
            self.last_label = self.sample_label.get(self.well, default="")


if __name__ == "__main__":
    path = LabelWells().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
