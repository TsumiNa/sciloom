# CSV reads: typed semantics and the native parsing gate

Stage 11 implements SciLoom CSV semantics in source/IR/JSON/reference execution.
AutoSuiteTarget rejects ReadCsv with `unsupported_csv_semantics`; it does not emit
an unchecked Import CSV task. JSON remains v4 and existing canonical programs
are unchanged. This page records why native task generation alone is insufficient.

## Evidence

| Source | What it establishes | What it does not establish |
|---|---|---|
| Primary APP and F28 `28_Load Reagent Table.asfp` | ImportCSV envelope; single-row text heading, then header-skipping text/volume arrays; `unit=ml` | Literal parsing, aggregate result precedence or atomic logical results |
| F25 `25_Import Csv Header.asfp` | Repeated row/header selection with explicit destination variables | General CSV dialect or error recovery |
| Type template 46, empirical catalog | Task child order and column fields | Executor acceptance of newly composed tasks |
| Manual 2.47.1.1 §3.7.8, printed pp. 88–92 | Parent Macro destinations, 1-based indices, headers, arrays for all rows, default SI values and native result codes | Complete quoting/encoding profile or mixed-failure aggregation |

The observed task fields, in order, are `description`, `name`, `edittime`,
`importfilepath`, `delimitermode`, `iswithheader`, `rowtoread`, `importresultvar`,
`importrowmode`, `columns`, `id`. Each column has `columnindex`,
`destinationvariable`, `defaultvalue`, `unit`. F28 uses delimiter mode 0,
row mode 0/header 0 for its heading and row mode 1/header 1 for arrays.

Public selectors are zero-based; a future mapping must add one **after capturing**
the runtime selector and validating its range. F28's reagent offset also skips
the ID column: the author uses `reagent_index + 1`, then native indexing adds one.
No column or header implicitly creates a SciLoom field.

## Known semantic differences

The manual says cells are evaluated as expressions. It also permits floating
values to be assigned to integers by truncation with a warning. SciLoom instead
parses literal typed data, rejects fractional integer cells, and uses explicit
defaults for cell failures. A numeric cell such as `1+2` therefore separates the
two behaviors. Native code 0 cannot prove the desired conversion occurred.

Native codes are 0 success, 1 type mismatch/default, 2 absent column/default,
3 EOF, 4 file error. SciLoom codes are a separate contract. The manual does not
specify precedence across mixed rows/columns; mapping one aggregate native code
to a portable outcome could hide an unhandled failure. A native file error can
record a result/log and continue. It is not proof of fatal propagation.

Physical input units and defaults must also be separated. A CSV value of `2` with
unit ml should become 2 mL, whereas a native default is documented as SI. The
reference implementation converts cell data using the explicit unit and does not
rescale a typed default. No native execution equivalence is asserted yet.

## Native measurement bundle

```console
uv run python autosuite/tools/probe_csv_read.py --output-dir /tmp/sciloom-csv-probes --host-directory C:/SciLoomProbes
```

Expected output: `Generated 14 native CSV probes; Executor status: pending.`
The tool creates fresh ASFP/data files and a hash manifest outside the corpus.
It places one evidence-shaped native Import CSV task in a compiled Macro shell;
this is a measurement artifact, **not** a bypass mode for compiling ReadCsv.
It does not create an APP, run Executor or control equipment.

The cases cover an integer control, fractional integer, numeric expression,
Unicode/quotes, UTF-8 BOM, Boolean, volume units, physical default, missing file,
EOF, mixed columns, mixed rows, header-only arrays and an F28-shaped recipe table.
The shell logs a before marker and, if execution continues, native status and
scalar values. Array cases log lengths; inspect complete array contents in the
configured host as well. Sentinel values reveal destinations left unchanged.

On the AutoSuite host, copy data to the named directory; ensure `missing_file.csv`
really is absent. Import each candidate into an isolated known-good application
and run the documented [Executor simulation](15_EXECUTOR_SIMULATION.md). Save
application/re-export/log hashes, exact source commit and dirty-state information,
package/platform versions, command/exit status, resulting values and continuation
markers. The manifest remains pending until these observations exist.

Before enabling compilation, resolve every parser/conversion difference for a
supported profile, check each column's policy using private buffers, and commit
destinations only after all checks. Ordinary failures also need the separate
[fatal propagation gate](24_RUNTIME_FAILURE_GATE.md). A warning, popup or skipped
task is not a replacement for stopping subsequent caller actions.

## Verification status

| Layer | Status |
|---|---|
| Reference typed conversion/defaults/atomic results | Implemented and tested |
| Python/direct IR/JSON equivalence | Tested; immutable v4 snapshots |
| Native task structure | Generated probes compared with corpus envelope when present |
| Editor/re-export | Pending |
| Executor conversion/result/continuation behavior | Pending; no Executor on this host |
| Portable AutoSuite CSV compilation | Rejected until the above contract can be met |

Collected questions remain RC-QA-001/002/003 in the runtime-capability Q&A. Corpus
files and their manifest are not changed by the implementation or probe tool.
