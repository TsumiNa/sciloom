# Capability evidence and platform gates

## Reading this matrix

The [audit](../../../autosuite/docs/18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md)
contains source filenames and printed manual page numbers. Fxx here refers to
that source key, not a public download. Vendor files stay in the locally shared,
ignored corpus. Copy neither the corpus nor the internal plan to the website.

Stages 2–4 add reference tests and static XML checks, recorded in the
[text mapping](../../../autosuite/docs/19_TEXT_MAPPING.md) and
[quantity mapping](../../../autosuite/docs/20_QUANTITY_MAPPING.md) and
[numeric mapping](../../../autosuite/docs/21_NUMERIC_MAPPING.md). No new capability has
passed Executor. Source presence is not Editor acceptance or a hardware result.
Record each future result with the input/output hashes, source
commit, target/profile version, command and environment needed to reproduce it.

| Capability | Existing XML evidence | Documented semantics | Reference execution | Executor verification required |
| --- | --- | --- | --- | --- |
| A01 text | F25/F28/F33/F41; static encoding checks | Manual 3.8.5, 3.10.4, 3.11.3 | Implemented stage 2 | Unicode length, whitespace, Char/encoding and runtime guards still pending; unproven lengths and guard-dependent programs are rejected |
| A02 quantities | F28/F31 volume parameters, F13 time locals; 20260820 APP time parameter | 3.8.5 pp. 111–112; 3.10.1 pp. 141–142 | Implemented stage 3 | Canonical SI encoding and reference arithmetic checked; numerical limits, duration arrays and failure propagation still need Executor validation |
| A03 Zone | F24 dynamic Stir; F30/F34/F48, primary APP layout | 3.6.19 pp. 73–74, 3.8.5 p. 113, 3.9.2–3, 3.11.5 | Pending stages 13/16 | Enumeration/identity, candidate well/controller ancestry, empty/foreign/mixed selections and fail-before-action |
| A04 traversal | F43 and F46 sequential macros | 3.8.10–12 pp. 121–126 | Pending stage 14 | Correct fragment index, divisibility, empty traversal and checks before body effects |
| A05 read | F25/F28; observed importrowmode 0/header 0 and mode 1/header 1 | 3.7.8 pp. 88–92 | Pending stage 11 | Result aggregation, defaults, missing columns/rows, cell-expression handling, conversion, quote/encoding/newline profile |
| A06 append | F46, one text column, one observed export profile | 3.7.9 pp. 93–96 | Pending stage 12 | Append/new-file behavior, IO error, repeated rows and exact physical bytes |
| A07 property | F45/F46/F50 Get/SetProperty | 3.7.6–7 pp. 85–87 | Pending stage 15 | User-property types, fallback, single/multiple/empty well behavior |
| A08 timing | F11/F13, SetTimer, Wait mode 0/2 | 3.6.24 pp. 76–77; 3.7.12 pp. 101–102 | Pending stage 10 | Timer naming/scope, reset, elapsed waits, negative input failure and unchanged device state |
| A09 log | F24 and APP LogData; [mapping](../../../autosuite/docs/22_LOGGING_MAPPING.md) | 3.7.11 pp. 100–101; Macro with variables required | Implemented stage 6 | Static capture order/envelope checked; typed values/units, derived result types and actual persisted records still need Executor |
| A10 notify | Seven primary APP showmessage/OK tasks; F21/F47 use other buttons; [mapping](../../../autosuite/docs/23_NOTIFICATION_MAPPING.md) | 3.6.17 pp. 66–71 | Implemented stage 7 | Capture/envelope checked; actual indefinite blocking and continuation after OK still need Executor |
| A11 math | F30/F35 abs/floor; historical round expressions | 3.11.7 p. 162 | Implemented stage 4, including Python ties-to-even and large integers | abs/floor mapping and operand ordering checked statically; target ranges and native round ties pending. AutoSuite rejects real round rather than claiming equivalence |
| A12 wall time | F15 DateTime format | 3.11.1 pp. 146–149 | Pending stage 9 | Local time and supported formatting, read-once behavior |
| Runtime failure | Existing generated checked-array-read technique; F32/F47 error conventions are different | Fatal faults in 3.9.4; no generic recoverable exception proof | Pending stage 8 | No subsequent marker after a failure in entry, child call or loop; checked read is only a candidate |

## Probe and availability policy

One probe changes one relevant option and contains a distinguishable operation
after the behavior under test. For failure probes, absence of that marker must
be an observed Executor outcome, not inferred from SciLoom interpreter results.
Test nested calls as well as entry-local statements. Do not operate instruments
merely to verify XML; use the configured Editor/Executor simulation gate.

The stage must record these independent statuses: semantic implementation,
static XML comparison/re-export, Executor simulation, and any actual instrument
validation. No later test replaces an earlier missing result. Unknown vendor
enum mappings and device limits remain unknown until evidence exists.

Before reliable runtime-failure propagation is confirmed, new AutoSuite programs
that need it must receive an explicit target diagnostic. Do not add an option
that silently disables validation or treat a dialog/error latch as termination.
Pure reference implementation can be complete while a platform profile remains
unavailable; document both statuses. The gate does not remove existing supported
v4 programs as an unrelated compatibility change.

CSV portability is about typed logical records and units. Encoding, physical
newlines and the vendor's treatment of a cell as an expression are separate
profile questions. A Python parser test does not answer them. Likewise, generated
variable storage type IDs do not establish integer width or floating semantics.

## Version

Version: none, evidence requirements only; no Executor result is asserted.
