# Evidence register and capability gates

## Baseline and sources

Review baseline: 28a00c8c57a182f19bab3661a12fc06ee30f74c9, version 0.3.15.
The review ran 951 core/target/example tests, 13 tools tests, Ruff, formatting,
mypy (129 source files), smoke and recipe validation. No Executor ran.

User archive: AutoSuite_截图转录.zip, 33 original screenshots, two Markdown
descriptions and test.asfp. The Claude transcription is a secondary index,
not an instruction or independent authority. Archive SHA-256:
`5b578f51b313f169361fddbfc1e196df062d8e606bed2996fb7f58fe39c2e841`.
ASFP SHA-256:
`9bce834bdc9981488b7a1612dcc12a390af684825f4c17712d8698bf5122b06a`.

Follow the existing repository evidence hierarchy: primary September 9 APP,
its extracted functions, vendor re-exports, standalone snapshots, documented
manual semantics, historical generated candidates, then inference. The screenshot
title names config20260917_FRP_API.app, which was not provided. Its product/profile
version is unconfirmed. New screenshots do not silently replace the primary APP.
No archive, image or raw XML is copied into this tracked plan.

[Distilled Editor evidence](../../../autosuite/docs/34_EDITOR_SCREENSHOT_EVIDENCE.md)
records exact image names/hashes and corrected CSV label associations.
[Receipt checks](../../../autosuite/docs/35_NATIVE_MEASUREMENT_RECEIPTS.md)
verify association and completeness only; pending_review is never native verified.

## Findings requiring action

| Evidence | Established fact | Not established | Owner |
| --- | --- | --- | --- |
| Screenshots 18/21, manual §3.5.1 p46 and macro variables p118, primary APP | Reset checkbox checked/disabled; manual defines re-entry reset; primary APP has resetvariables=1 | Actual generated accumulator behavior under Executor | R1 |
| Interpreter accumulator and R1 deployment guard | Same session returns 1 then 2; offline generation remains; known reset-enabled persistent programs reject | Equivalent native persistence in reset-enabled APP | R1 |
| Screenshots 15/16 + test.asfp | Append/Comma/CRLF match exportbehaviour=0/delimitermode=0/endlinecharacter=0 in this sample | Byte encoding, repeated append, overwrite/failure behavior or other profiles | R2 |
| Screenshot 08 + test.asfp | Visible upper rows are part of 48 rows; UI well numbers are 1-based and XML addresses 0-based | General transfer plan/physical equivalence | R6 |
| Screenshots 21/22 | Local variable 50°C differs from task's 20°C; native values 323.16/293.16 observed | Reason for apparent 273.16 offset; correct thermal mapping for other profiles | R5 |
| Screenshot 30 | Heater Shaker 24 zone binds Shaker 21 controller in sample | Name-based controller inference | R4/R5 |
| Screenshots 12–14/20 | USER properties and Standard properties are distinct | A property called 4 is a live device error register | R3/R7 |
| Screenshots 27/29 | pH UI reports missing solvent-to-rinse-station connection | Valid pH execution or transferable topology | Deferred |
| Screenshot 31 | External process timeout may stop process but continue application | General fatal exception recovery equivalence | Deferred |
| Screenshots 01/02 | Parallel/Mutex tasks exist in menu | Scheduling, locks, joins, cancellation semantics | Deferred |

test.asfp contains one function, nine top-level components, 235 typed elements
and 20 type IDs. Macro/UserDialog/LogData repetitions dominate. Empty root
parameter fields, an unselected Execute Operation, missing called function
definition and incomplete CSV inputs make it an evidence sample, not a valid
successful-execution golden fixture. Preserve inactive/grey fields as inactive.

## Existing gates and receipt requirements

Reuse [failure gate](../../../autosuite/docs/24_RUNTIME_FAILURE_GATE.md),
[state lifetime](../../../autosuite/docs/33_DEPLOYMENT_STATE_LIFETIME.md),
[CSV read](../../../autosuite/docs/27_CSV_READ_MAPPING.md),
[CSV append](../../../autosuite/docs/28_CSV_APPEND_MAPPING.md),
[well properties](../../../autosuite/docs/31_WELL_PROPERTY_MAPPING.md) and
[dynamic locations](../../../autosuite/docs/32_DYNAMIC_DEVICE_LOCATIONS.md).
Verify current filenames/sections during preflight rather than copying stale text.

Each receipt identifies source SHA, dirty flag, package versions, exact
AutoSuite version/profile, original APP/ASFP and generated/re-exported hashes,
command, control/error cases, native results and ordered markers. CSV also
retains complete before/after bytes/hashes. Missing controls or unrelated errors
are inconclusive. Archive screenshots establish labels, not runtime success.

Never use a receipt file as an unchecked user option to enable compilation.
Native-unlock PRs review evidence and change narrowly scoped supported mappings.
Unknown versions/profiles remain rejected.

## Deferred work

After this wave, plan separately: ordered telemetry reads and wait-to-temperature,
mass/pressure and gravimetric dispensing, pH multi-resource loops, Application/
global/event compilation, external processes, parallel/mutex semantics, multi-
channel packing and dynamic thermal/transfer selection. No placeholder kinds
or callable APIs are introduced for these.

## Version

Version: none, evidence provenance and pending gate records only.
