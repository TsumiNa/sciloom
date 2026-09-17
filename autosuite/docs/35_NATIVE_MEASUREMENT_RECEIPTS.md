# Read-only native measurement receipt checks

## Meaning

validate_native_receipt checks association and completeness. It never executes
Executor, writes files, edits corpus/manifests or enables compiler operations.
Its only successful native status is **pending_review**. A complete receipt may
describe behavior contradicting SciLoom; reviewers must assess that behavior
before any narrow unlock PR. Hashes associate bytes, not the truth of claims.
The [single contract](../../docs/refactor/autosuite-expansion/01-contract.md#r2-evidence-and-native-unlocking)
specifies this checkout-only API. No real receipt arrived in R2.1. Unit-test
receipts are explicitly synthetic and stay in temporary test directories.

Retain the original manifest and files from a **clean** checkout:

| Suite | Existing generator | Required cases / runs per receipt |
| --- | --- | --- |
| runtime_failure | probe_runtime_failure.py | All 9 cases; one run each, including three successful controls |
| csv_read | probe_csv_read.py | All 14 cases; two runs each, including successful integer controls |
| csv_append | probe_csv_append.py | All 6 cases; two runs each, without restoring the seed |

Additional failure repetitions use another complete receipt. Case names come from
existing generators. Historical source versions are allowed if both packages are
lockstep and match the manifest. source_dirty must be exactly false: never edit
a dirty manifest into a clean-source claim. Regenerate after committing.
Follow existing [failure](24_RUNTIME_FAILURE_GATE.md), [read](27_CSV_READ_MAPPING.md)
and [append](28_CSV_APPEND_MAPPING.md) host procedures. Files enter corpus through
the team's human-managed process; this tool does not install or modify evidence.

## Receipt format 1

Place receipt.json alongside its received evidence tree. Required fields:

| Field | Meaning |
| --- | --- |
| receipt_format | Integer 1 |
| suite | runtime_failure, csv_read or csv_append; matches CLI selection |
| manifest_sha256 | Exact original manifest byte digest |
| source_commit | Exact 40-character source commit from manifest |
| package_versions | Exact sciloom and sciloom-autosuite versions from manifest |
| product_version | Actual native product version; checker currently supports 2.47.1.1 |
| profile | autosuite-2.47.1.1 serialization profile; matches product and every APP |
| configuration_notes | Installed configuration/profile, error-function setup, logging, host procedure and warnings |
| cases | Complete case records, each with name and runs |

File references have `path` (relative filename) and `sha256` (actual lowercase
digest). Generated files resolve beside the manifest; received files beside
receipt.json. Absolute paths, path escape and symlink escape reject. Keep the
original APP filename so its command basename can be matched; directories may differ.

Each run contains:

| Field | Meaning |
| --- | --- |
| number | 1, then 2 for CSV |
| app | Hashed actual gzip APP with product/reset settings; CSV repetitions use identical APP bytes |
| reexport | Hashed native Editor ASFP re-export with functions XML root |
| command | Actual argv array: `["AutoSuiteExecutor.exe", "C:/Probes/entry/probe.app", "/r", "/sim", "100", "/s", "/c"]`; format 1 checks this exact simulation option sequence |
| exit_code | Actual integer process exit code, not a success inference |
| log | Hashed nonempty complete raw native log/task trace |
| observations | Hashed structured JSON transcription described below |
| csv_before, csv_after | CSV suites: hashed copies of exact bytes, or explicit null when absent; empty files are real files, not null |

Observations require `outcome` (completed/failed/stopped/timed_out), ordered string
`markers`, Boolean `stopped`, `native_error` (observed text or explicit null),
`values` (array of actual values) and nonempty `notes`. CSV also requires integer
`native_status`. Read values have one element per imported column; array columns
contain complete arrays, not lengths. Keep raw traces beside this transcription:
the checker cannot prove human transcription accuracy.

An **illustrative observations fragment**, not an actual native result:

```json
{
  "outcome": "completed",
  "markers": ["before", "after"],
  "native_status": 0,
  "stopped": false,
  "native_error": null,
  "values": [12],
  "notes": "Replace with actual observations and associate the raw trace."
}
```

Failure controls require their full successful sequence plus host.after. Failed
or unobservable controls are inconclusive and reject. A passing entry test is
not child/loop evidence. Contradictory failure observations stay visible for review;
exit codes or missing markers cannot independently prove fatal behavior.

CSV read's control must observe integer 12 and result 0. First input bytes match
the generated data and stay unchanged. Append's first before-file is absent or
matches the sentinel seed. In both suites, second before-file matches first
after-file. Retain complete second after-bytes even if they show overwrite,
corruption, partial writes or unexpected encoding. Continuity is not append proof.

## Invocation

From repository root, with real received files at these example paths:

```console
uv run python -m autosuite.tools.validate_native_receipt --suite runtime_failure --manifest scratch/failure/manifest.json --receipt received/failure/receipt.json
```

Expected output **only for a complete associated receipt**:

```text
Complete receipt: 9 cases; native status: pending_review.
```

Invalid/missing/inconclusive data exits 2 with a reason and writes nothing.
Help is runnable without native evidence:

```console
uv run python -m autosuite.tools.validate_native_receipt --help
```

Then review native errors, continuation, values, full bytes and re-export changes
against the exact capability contract. Record contradictions or narrower supported
modes. A source declaration, matching label or machine check cannot replace that
review. The compiler neither imports this tool nor reads these receipts; all
failure/CSV gates remain unchanged in R2.1.
