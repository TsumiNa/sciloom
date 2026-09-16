# Read and append CSV records

Use explicit columns to read a reagent heading or a column of sample volumes.
CSV reads are available in Python source, JSON and reference execution. AutoSuite
compilation currently reports `unsupported_csv_semantics`: its cell conversion
and error behavior still need platform validation.

```python
from sciloom import Function, Input, Output, Volume, csv, mL, runtime

class ReadVolumes(Function):
    path: Input[str]
    ids: Output[list[str]]
    volumes: Output[list[Volume]]

    @runtime
    def run(self) -> None:
        self.ids, self.volumes = csv.read_columns(
            self.path,
            header=True,
            columns=(
                csv.Column(index=0, value_type=str),
                csv.Column(index=1, value_type=Volume, unit=mL, default=0 * mL),
            ),
        )
```

For `id,volume` followed by `A,1.5` and `B,`, this reads IDs A and B, with
volumes 1.5 mL and 0 mL. Lists have the same length and are independent copies.
The full [reagent-table example](../../examples/read-reagent-table.md) also selects
a reagent column at runtime.

## Select rows and columns

| Call | Results |
|---|---|
| `csv.read_row(path, row=0, header=False, columns=(...))` | One scalar per column |
| `csv.read_columns(path, header=True, columns=(...))` | One list per column |
| `csv.try_read_row(...)` | Integer status, then scalar results |
| `csv.try_read_columns(...)` | Integer status, then list results |

Always unpack the result tuple. For one column, write
`(self.name,) = csv.read_row(...)`. Each destination must be a declared runtime
field, and destinations cannot repeat.

Indices start at zero. With `header=True`, row zero is the first row **after**
the header. A header does not create fields or select columns by name. The path,
row, column indices and defaults can use runtime expressions. `header`, the
fixed tuple of inline `csv.Column` declarations, column types and units are
chosen before compilation. Physical columns require matching units; ordinary
scalar columns do not accept units.

An empty dataset produces empty lists. Requesting a row beyond the data produces
EOF. Negative or Boolean indices are invalid, not recoverable file statuses.
Read an entire result into fields before using it in calculations.

## Defaults and failures

A column default handles a missing or invalid **cell**, never a missing file.
Defaults already have their declared type: `default=3 * mL` remains 3 mL whatever
the input unit is. Without a default, bad data stops an ordinary read. No output
of that read is partially assigned. Earlier completed steps remain completed.

Use a try-form when the procedure needs to inspect an expected file/data failure:

```python
self.status, self.name = csv.try_read_row(
    self.path, row=0, header=False,
    columns=(csv.Column(index=0, value_type=str, default=""),),
)
if self.status == csv.OK:
    self.label = self.name
```

Here `status`, `name` and `label` must be declared runtime fields. Every column
in `try_read_row` needs a default; an entire failed read returns all defaults.
`try_read_columns` returns all empty lists on an entire failed read.

| Named status | Meaning |
|---|---|
| `csv.OK` | All requested data converted without defaults |
| `csv.DEFAULT_USED` | At least one cell used its explicit fallback |
| `csv.EOF` | Requested data row does not exist |
| `csv.INVALID_DATA` | Unhandled bad/missing cell, malformed record or invalid UTF-8 |
| `csv.IO_ERROR` | File could not be read |

These are SciLoom statuses, not AutoSuite result codes. A missing reference file
service, invalid path or invalid selector raises an execution error even in a
try-form.

## Current parsing profile

Reference execution reads UTF-8, optionally with a BOM. It uses comma separation,
double-quoted fields with doubled quotes, and LF or CRLF records. Quoted newlines
are preserved. Text cells retain their parsed contents; they are not evaluated.

Integers require ASCII decimal integer text. Reals and quantities accept decimal
or exponent notation and must be finite. Numeric conversion strips only spaces,
tabs, CR and LF. Booleans accept `true` or `false`, case-insensitively. Empty
numeric cells, `1+2`, integer `1.5`, `nan` and `inf` are invalid cells; a
declared default can handle them. Volume and Duration may be negative; rotational
speed may not.

The parser uses Python's strict CSV reader and its field-size limit. A row read
parses through the selected record; later malformed records are not inspected,
although UTF-8 decoding validates the whole file. All-column reads parse the
whole dataset. No transaction is promised if another process changes a file.

AutoSuite documents expression evaluation and integer truncation. Those are not
equivalent to these rules. No native import task is emitted until a mapping can
preserve conversion, defaults, complete result binding and failure propagation.

## Append one row

Append a label with `csv.append_row(self.path, values=(self.label,))`. Keep the
trailing comma for a one-cell tuple. Values can be runtime expressions; the
number and order of cells are fixed in the source. Scalars and physical quantities
are supported; lists and arbitrary objects are not.

This complete example returns a status so the caller can handle a file error:

<!-- example: csv-append -->
```python
from sciloom import Function, Input, Output, csv, runtime

class WriteLabel(Function):
    path: Input[str]
    label: Input[str]
    status: Output[int]

    @runtime
    def run(self) -> None:
        self.status = csv.try_append_row(self.path, values=(self.label,))
```

Calling it twice with label `sample,A` appends two records, each containing that
one text cell. `try_append_row` returns `csv.OK` or `csv.IO_ERROR`; ordinary
`append_row` stops on a file error. A failed write may already have written some
bytes. Neither form retries or removes them. A bad path, encoding failure or
missing reference file service remains an execution error even in the try-form.

Reference execution writes UTF-8 without BOM, comma-separated cells, doubled
quotes inside quoted fields, and a CRLF record terminator. Integers use decimal
text, Booleans use `true`/`false`, and finite floats use Python's round-trip text.
Quantities use canonical SI numbers: for example, `2 * mL` writes `2e-06`.
There is no header generation or parent-directory creation.

The destination is created if absent. Existing content must already end at a
complete CSV record boundary: the operation appends bytes without reading,
repairing or adding a separator to the old file. For example, appending `0` to
an unterminated file containing `2` produces `20`, not two rows.

AutoSuite currently reports `unsupported_csv_append` for both forms. Its observed
export mode, encoding and error behavior need verification before these operations
can compile. See the [author example](../../examples/append-sample-log.md) or
[reference execution example](../../examples/csv-append-ir.md).
