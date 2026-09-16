"""For experiment authors: append one sample label as a CSV record.

Run: ``uv run python examples/append_sample_log.py``
Terminal output: ``AutoSuite CSV append awaits mode and encoding validation.``

The runtime caller supplies a file path and label. append_row captures the label
once, then appends one record; a file error stops subsequent steps. Parent
directories must exist and an existing file must end at a complete CSV record.
There is no automatic header, retry or rollback of partial writes.

AutoSuite's observed numeric export mode is not yet confirmed as append rather
than overwrite. This script checks the compilation diagnostic and writes no
ASFP. See developer/csv_append_ir.py for reference execution and JSON.
"""

from sciloom import Function, Input, csv, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class AppendSampleLog(Function):
    """Append the supplied label without changing existing records.

    Attributes:
        path: Runtime destination with an existing parent directory.
        label: Sample text, encoded as one CSV cell.
    """

    path: Input[str]
    label: Input[str]

    @runtime
    def run(self) -> None:
        csv.append_row(self.path, values=(self.label,))


if __name__ == "__main__":
    try:
        AppendSampleLog().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "unsupported_csv_append" for d in error.diagnostics):
            raise
        print("AutoSuite CSV append awaits mode and encoding validation.")
    else:
        raise AssertionError("Update this example when verified append compilation becomes available.")
