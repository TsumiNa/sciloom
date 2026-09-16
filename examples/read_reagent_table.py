"""For experiment authors: select a reagent name and its volume column.

Run: ``uv run python examples/read_reagent_table.py``
Terminal output: ``AutoSuite CSV compilation awaits parser and failure validation.``

The function reads the selected reagent heading, experiment IDs and volume data.
reagent_index is zero-based among reagents; the first CSV column holds IDs.
Numeric cells in the selected column are millilitres. A missing/invalid volume
uses zero; a missing file stops execution instead of using that cell default.

The sample data is read_reagent_table.csv beside this source. Reference execution
is demonstrated separately in developer/csv_read_ir.py. AutoSuite currently
rejects these reads: its cell-expression and error behavior are not yet verified
against this contract. Running this script writes no ASFP and operates no device.
"""

from sciloom import Function, Input, Output, Volume, csv, mL, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class ReadReagentTable(Function):
    """Read one reagent's heading and an aligned experiment/volume table.

    Attributes:
        path: CSV file provided by the runtime caller.
        reagent_index: Zero-based reagent choice, after the experiment-ID column.
        reagent_name: Heading of the selected reagent column.
        ids: Experiment identifiers from data rows.
        volumes: Millilitre cells converted to Volume values, with zero fallback.
    """

    path: Input[str]
    reagent_index: Input[int]
    reagent_name: Output[str]
    ids: Output[list[str]]
    volumes: Output[list[Volume]]

    @runtime
    def run(self) -> None:
        (self.reagent_name,) = csv.read_row(
            self.path,
            row=0,
            header=False,
            columns=(csv.Column(index=self.reagent_index + 1, value_type=str),),
        )
        self.ids, self.volumes = csv.read_columns(
            self.path,
            header=True,
            columns=(
                csv.Column(index=0, value_type=str, default=""),
                csv.Column(index=self.reagent_index + 1, value_type=Volume, unit=mL, default=0 * mL),
            ),
        )


if __name__ == "__main__":
    try:
        ReadReagentTable().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "unsupported_csv_semantics" for d in error.diagnostics):
            raise
        print("AutoSuite CSV compilation awaits parser and failure validation.")
    else:
        raise AssertionError("Update this example when verified CSV compilation becomes available.")
