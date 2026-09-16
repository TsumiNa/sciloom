"""For experiment authors: label each selected well and append a dated text record.

Run: ``uv run python examples/label_sample_log.py``
Terminal output: ``AutoSuite workflow awaits CSV and location validation.``

After explicit OK acknowledgement, the procedure trims the supplied label, reads
the wall clock once and forms directory/YYYY-MM-DD_HHMMSS.csv. Each selected well
gets the label; its stored label is read back and appended with its display name
as one CSV text cell. The row count is logged after all appends succeed.

The same timestamp may be reused: this is append, not unique-name allocation.
An empty rack creates no file. Failures preserve earlier property writes and
completed/partial file writes. No retry, rollback or automatic directory creation
is implied. Compilation currently rejects this workflow and writes no ASFP.
See developer/runtime_workflows_ir.py for deterministic reference execution.
"""

from sciloom import Function, Input, Output, Var, WellProperty, Zone, csv, log, notify, now_text, runtime, text, zones
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class LabelSampleLog(Function):
    """Save sample metadata and append one captured record per selected well.

    Attributes:
        rack: Ordered wells supplied by the runtime caller.
        label: Batch label, trimmed before storage.
        directory: Existing runtime output directory.
        path: Timestamped destination, not guaranteed unique.
        count: Completed records in this invocation, reset each call.
        well: Current one-well selection.
        cleaned: Captured label after trimming.
        stamp: Single wall-clock read for the whole invocation.
        record: Label read back from stored metadata.
        sample_label: Stored sample_ID text property.
    """

    rack: Input[Zone]
    label: Input[str]
    directory: Input[str]
    path: Output[str]
    count: Output[int]
    well: Var[Zone] = Zone.empty()
    cleaned: Var[str] = ""
    stamp: Var[str] = ""
    record: Var[str] = ""

    def __init__(self) -> None:
        self.sample_label = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        notify("Samples are ready. Confirm to label and record them.")
        self.cleaned = text.trim(self.label)
        self.stamp = now_text("%Y-%m-%d_%H%M%S")
        self.path = self.directory + "/" + self.stamp + ".csv"
        self.count = 0
        for self.well in self.rack:
            self.sample_label[self.well] = self.cleaned
            self.record = self.sample_label.get(self.well, default="")
            csv.append_row(self.path, values=(zones.well_name(self.well) + ":" + self.record,))
            self.count += 1
        log(self.count, category="samples", stream="records")


if __name__ == "__main__":
    try:
        LabelSampleLog().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(
            d.code not in {"unsupported_csv_append", "unsupported_zone_cardinality"} for d in error.diagnostics
        ):
            raise
        print("AutoSuite workflow awaits CSV and location validation.")
    else:
        raise AssertionError("Update the example after native CSV and location checks are verified.")
