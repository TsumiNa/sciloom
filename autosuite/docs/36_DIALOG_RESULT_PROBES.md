# Result-bearing dialogs: native measurements and remaining gates

**Code: probes implemented; compiler gated. Native status: pending.** No Executor
result is recorded here. RequestText/AskYesNo reference semantics are available;
all AutoSuite compilation and direct emission of those nodes remain rejected.

## Received evidence

The user-supplied Editor archive and its exact hashes are recorded in
[the screenshot evidence register](34_EDITOR_SCREENSHOT_EVIDENCE.md). Its native
test.asfp has SHA-256
`9bce834bdc9981488b7a1612dcc12a390af684825f4c17712d8698bf5122b06a`.
This package does not declare a product version or deployment profile. The
primary APP supplies ordinary OK dialogs, not this result-dialog evidence.

| Selected task ID in test.asfp | Observed fields | Limit |
| --- | --- | --- |
| `{A81CC6E9-0955-4426-8B55-B0BF65211699}` | askforinput, resultunit=text, okstop, result txtBarcode, timeout tMaxWaitTime, timeout answer txtDefaultAnswer | No proof of result bytes, empty input or termination |
| `{DCBC6267-E249-49AB-A45A-6326E5688DA8}` | showmessage, yesnostop, resultunit=1, Yes=1, No=0, indefinite wait | Integer result observation, not proof of portable bool/Stop behavior |

Both selected tasks have input validation disabled, post-dialog pause disabled
and softstopping=0. The older representative UserDialog template instead uses
softstopping=1 and no result. Do not combine those policies silently. The
empirical catalog establishes the ordered flat 41-field envelope, not complete
behavior. Manual 2.47.1.1 §3.6.17 (printed pp. 66–71) permits timeout answers and
continuation; this is insufficient for SciLoom's fatal timeout requirement.

## Generate isolated measurements

Use the received original ASFP and explicit task IDs; keep it outside generated
output. Do not edit evidence or treat the candidates as native re-exports.
From a clean checkout with lockstep dependencies, run:

```console
uv run python -m autosuite.tools.probe_dialog_results --source-asfp received/test.asfp --text-task-id '{A81CC6E9-0955-4426-8B55-B0BF65211699}' --choice-task-id '{DCBC6267-E249-49AB-A45A-6326E5688DA8}' --output-dir scratch/dialog-results
```

Expected: `Generated 30 native dialog probes; Executor status: pending.`
The paths are examples to replace with local paths. The generator requires a
fresh output directory outside corpus, validates exact task identity/envelope
and critical policy fields, then clones the selected payload into a compiled
device-free acknowledgement/logging shell. It substitutes fixed result names,
probe messages, wait durations, timeout sentinel expressions and deterministic
IDs. It compiles no gated result-bearing semantic node and exposes no target
bypass. Existing source-version checks are reused from the failure probes.

manifest.json records the clean/dirty commit, package versions, candidate target,
source file hash, source-declared product version (null when absent), unknown
profile, selected IDs and parsed task hashes, all generated ASFP hashes, exact
entry names, actions, expected semantic marker order and pending status. Parsed
task hashes use `ET.tostring(task, encoding="utf-8")`, including retained source
whitespace; the original file hash is the authority for source byte identity.
The candidate target is not a claim that the original source used that version.

| Kind | Actions in each context | Native recorded value |
| --- | --- | --- |
| Text | Enter S-001, accept empty text, close/cancel, Stop, wait for timeout | Text; timeout candidate supplies NATIVE_TIMEOUT |
| Choice | Yes, No, close/cancel, Stop, wait for timeout | Integer 1/0; timeout candidate supplies 0 |

Each action appears at entry, through a child call, and through a child call in
a two-iteration loop: 30 separate candidates. Timeout cases use 2 seconds; all
others use zero (documented indefinite wait). Successful loop controls require
two distinct accepted responses. Failed cases require no second interaction.
Timeout-answer values intentionally reveal vendor continuation; they are not
fallback implementations of the semantic contract. If the UI has no cancel or
close path, record it as unsupported, not equivalent to Stop or No.

## Host procedure and receipt

Use a disposable simulation APP with configured logs and compatible deployment.
Import **one candidate per fresh APP**; generated shells may share internal IDs.
Call the manifest's entry function, with a distinct host.before log before it
and host.after log after it. Re-export the imported function package before
running. Record APP reset setting explicitly; loop counters reset at entry,
and the result sentinel is not evidence of persistence.

Run visibly, omitting silent mode for this interactive suite:

```bat
AutoSuiteExecutor.exe dialog-probe.app /r /sim 100 /c
```

For every candidate, retain all of the following as one receipt directory:

1. Original generated manifest/ASFP with hashes, actual source commit and package
   versions; exact original source ASFP hash and its separately confirmed product
   version/profile. Dirty generation is not an acceptance receipt.
2. Exact imported APP bytes/hash, its product/profile version and reset setting,
   native re-export bytes/hash, and actual Executor argv, exit code and raw logs.
3. Ordered operator actions, displayed prompt, elapsed wait, return values and
   native error/termination. Preserve empty text as empty text. For choice,
   record native type/value, not only a converted Boolean assertion.
4. Complete marker order across function, caller, loop and host. For successful
   cases require the manifest's entire semantic_marker_order, one native.value
   between each dialog.before/dialog.after, then host.after. For failures require
   the prefix ending at dialog.before and **no** value, dialog.after, caller.after,
   later loop/host marker or other downstream action. Observe long enough to
   distinguish suspension from termination; exit code alone is insufficient.
5. For loop controls, both prompts and both responses; for failed loop cases,
   prove the remainder, next iteration and caller do not execute. For timeout,
   record whether NATIVE_TIMEOUT/0 is returned and execution continues. That
   contradicts fatal timeout support and must remain visible.

The existing failure/CSV receipt validator does not accept this interactive
suite. Do not relabel its manifest or add `/s` merely to fit another validator.
These receipts require review; generator success, XML parsing, UI screenshots,
a re-export or a reference test cannot individually certify native semantics.

## Reference workflow and unlock boundary

`examples/capture_barcode.py` expresses single-well validation → text request →
sample_ID write → log. `examples/developer/barcode_ir.py` provides equivalent
direct IR/JSON and explicit location/property/response services. Tests cover
normal/empty/non-ASCII text, absent/unknown/multiple wells before response
consumption, cancellation/Stop/timeout/wrong types with no write or log, and
unchanged target rejection. These tests perform no hardware I/O.

Only a later evidence-backed PR may map a proven variant to the semantic nodes.
Text, choice, cancellation, Stop and timeout each need their own proof across
all required contexts; none is inferred from another passing case. Other
versions/profiles and unproven policies stay rejected. If native behavior cannot
preserve the accepted contract, use the plan's material-difference procedure;
do not introduce a hidden global latch, default result or recovery mode.
