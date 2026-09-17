# CSV append semantics and native export measurements

## Evidence and implemented boundary

The primary APP's F46, `46_Export Wells Log.asfp`, repeatedly uses
`Chemspeed.SATaskExportCSV.1` with one text column. Its representative envelope is
`autosuite/corpus/type_templates/43_Chemspeed.SATaskExportCSV.1_representative.xml`.
Observed values are delimitermode=0, endlinecharacter=0, exportbehaviour=0,
changerowvar=1 and multiplelines=0. Column 1 evaluates log_txt, with variabletype
text and unit 1. The export result is an integer Macro variable.

Manual 2.47.1.1 section 3.7.9, printed pp. 93–96, distinguishes Append, New File
and Change Value. New File can overwrite existing content. It documents native
result 0 for success and 1 for a file error with a log message. It does not map
the XML number exportbehaviour=0 to a UI label. Repetition in F46 suggests append
intent, but cannot prove that numeric mapping, physical encoding or termination.

The subsequently received [Editor screenshots](34_EDITOR_SCREENSHOT_EVIDENCE.md)
15/16 and matching incomplete test.asfp now associate Append, Comma and CRLF
with the three zero fields **in that sample**. Its September 17 APP and product
version were not supplied. This label evidence does not establish file bytes,
repeated preservation, encoding or another profile's enums.

Consequently both public append forms receive `unsupported_csv_append`. The
try-form removes the default-fatal requirement but does not prove a safe append
mode or text encoding. There is no flag to bypass the gate. The native probes
below are measurement artifacts, not portable compiler output.

| Layer | Current evidence |
|---|---|
| Original XML | One text column, one mode combination, observed field order |
| Manual semantics | Append/new/change operations; parent Macro result variable; IO result 1 |
| Reference execution | UTF-8/comma/CRLF, captured typed row, repeated writes, explicit status and failure; tested through Python/IR/JSON |
| Static native probes | Six cases preserve the observed envelope and use typed status storage; compared with template 43 |
| Matching screenshot UI | Append/Comma/CRLF map to zero fields in the incomplete sample; product/profile unknown |
| Executor / re-export | Pending; no execution, file bytes or error propagation result asserted |

## Reference contract

AppendCsv captures path and ordered scalar values, encodes the complete row, then
calls the explicit FileService once. UTF-8 has no BOM; fields use comma separation
and doubled quotes, ending in CRLF. Booleans are lowercase; physical values are
canonical SI numbers. This is a reference byte profile, not a claim about native
AutoSuite output. Existing content must end at a complete physical record boundary;
the operation neither reads nor repairs it. Parent directories are not created.

OSError yields SciLoom IO_ERROR (4), distinct from native error code 1. Ordinary
append records the failed attempt and stops; try-append writes the status and
continues. An already-written prefix is retained. Invalid arguments, missing file
services, encoding failure and broken service implementations remain fatal even
in try mode. CsvAppendEvent describes the requested logical row and status, not
an assertion that a failed write left either all or none of its bytes.

## Reproducible native measurements

```bash
uv run python autosuite/tools/probe_csv_append.py --output-dir /tmp/sciloom-append-probes --host-directory C:/SciLoomAppendProbes
```

Use a fresh scratch directory for generation and a fresh Windows scratch
directory on the AutoSuite host. Never point these probes at real experiment
files: the profile's actual mode behavior is unverified and might overwrite. Copy only the
existing_file.csv seed before its first run; other destinations must be absent.
Do not create absent-parent for the IO case. Import into a disposable known-good
application and follow [Executor simulation](15_EXECUTOR_SIMULATION.md).

Run each probe twice without restoring its seed between runs. Record before/after
file hashes and complete bytes for each run, native result and before/after log
markers. For existing_file, verify whether the sentinel survives each run; for
new_file verify whether both records survive. Other cases isolate Unicode,
quotes, backslash, embedded newlines and empty text. The missing-parent case
checks status and continuation separately from fatal propagation.

The generated manifest includes source SHA, dirty-state flag, lockstep package
versions, target directory, input/artifact hashes and pending status. For a
reportable result generate from a clean commit and retain the manifest with the
Executor command, product/profile version, re-export and observed bytes. Observe
the Editor mode label on import/re-export to establish its enum mapping. The
[runtime failure gate](24_RUNTIME_FAILURE_GATE.md) remains separately required
before ordinary default-fatal append can compile.

No raw corpus file or manifest is changed by generation or comparison.

Use [receipt checks](35_NATIVE_MEASUREMENT_RECEIPTS.md) to associate hashes, seeds
and two-run continuity. pending_review does not unlock either append policy.
