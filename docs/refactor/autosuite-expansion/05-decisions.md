# Decisions and implementation reassessments

Dates in this log use Asia/Tokyo (JST, UTC+09:00), the working session's timezone.

## D001 — Accepted scope and defaults (2026-09-18)

User selected: first wave through fixed heating and simple liquid transfer;
native gates per capability; offline generation retained with explicit unchecked
deployment report; text/yes-no with termination on cancel/Stop/timeout;
temperature measurement/wait-to-temperature deferred; normal lockstep PATCH/
MINOR version rules instead of the earlier 0.3.x exception. No releases.

## D002 — R0 preflight (2026-09-18)

Baseline main 28a00c8c57a182f19bab3661a12fc06ee30f74c9, both packages 0.3.15.
No open PR or tracked work was present. R0 uses codex/autosuite-expansion-plans.
Existing hooks path is .githooks. Python source and existing plans confirm:

- AutoSuiteLayout currently lacks an APP source hash. Add optional provenance
  outside semantic Program for exact source comparison; manually constructed
  layouts remain usable but cannot claim provenance verification.
- A defaulted field added to an existing serialized command record would alter
  baseline output. Use a new command-contract variant for lifecycle effects;
  unchanged commands retain their existing wire shape.
- Generic core compilation has no vendor-specific report slot. Keep deployment
  assessment and review export in sciloom_autosuite; do not mutate the Target
  protocol or overload ordinary diagnostics with successful-report metadata.
- Existing runtime integration is merged (#102), despite historical stage wording.
  Reuse its services, samples and tests; native gates are still pending.
- Native thermal/transfer profiles cannot be finalized from incomplete test.asfp.
  Their evidence-dependent constructor/payload definitions are explicit entry
  gates, not invented profile names or capability claims.

Classification: B for private/API-detail choices preserving the accepted intent;
C for unavailable native profile evidence. No approved semantics were changed.
No source implementation begins until R0 review and remote merge.

## D003 — R0 review corrections (2026-09-18)

Review 5238315873 (GraphQL PRR_kwDOUVkARs8AAAABODpbYQ) identified a misleading
standalone transfer signature and requested fixed version transitions in future
stage plans. The signature now explicitly declares LiquidHandler.transfer with
self and its operation ID. Each pending stage records Version: none for this
planning-only revision and a separately labeled implementation expectation.
Before its implementation PR is reviewed, that stage must replace the decision
with the actual exact lockstep transition. This follows the user's explicit
instruction to decide concrete versions after implementation rather than
preallocate future version numbers; it overrides the review's contrary proposal.
Classification A/B, no semantic or scope change. Both packages remain 0.3.15.

## D004 — R1.1 preflight (2026-09-18)

Baseline e4e4c8229af86c8954b8a2e97c02b20471e77456, packages 0.3.15. R0 PR #103
is remotely MERGED; its two review findings were addressed and latest-head
CI passed. Existing layout code has no provenance, and the original primary
APP stores one direct root resetvariables element with text 1.

R1.1 adds immutable facts/report records and a private shared assessment function;
target integration and review export remain R1.2. Missing product/reset fields
remain unknown; duplicate or structured reset fields are invalid. A layout
source hash is optional for manual records and never affects codegen identity.
Report requirements/findings reuse immutable Diagnostic records rather than
inventing another diagnostic model; they stay outside CompileResult.diagnostics.
Class B detail refinement, no changed intent. Native state experiments remain C
pending; the current original APP is not modified.

## D005 — R1.2 preflight (2026-09-18)

Baseline f6352d5987a90a9c4276f0e8986873b0d6215b25, packages 0.4.0. R1.1 PR #104
is remotely MERGED after its version-diagnostic correction, resolved review and
all four latest-head CI jobs passed. No new native receipt has arrived.

CompileResult stores specialized IR and emitted bytes, not a binding snapshot.
The exporter therefore checks concrete resource contracts against explicitly
constructed target binding facts and compares complete deterministic emission
(whose identity includes every fixed profile) with the supplied artifact. It
does not call resolve_devices, specialize or compile_ir. It reuses structural,
binding, configuration, timing, location and target validators on selected IR;
remaining DeviceIf nodes are rejected. Core CompileResult remains unchanged.
The returned deployment report gains optional artifact_sha256 and
specialized_ir_sha256, populated only by checked review export; ordinary reports
leave these absent values as None. Class B detail refinement preserves intent.

State probes reuse existing source-provenance helpers and manifest conventions.
Fresh reference sessions specify initialization; actual APP restart and both
reset settings remain explicit host experiments (class C), never inferred from
reference success or generated XML. No APP is generated or modified.

## D006 — R1.2 CI portability correction (2026-09-18)

CI on PR #105 passed execution checks but found a changed example report digest
on Linux: normal source lowering retains absolute checkout paths. The developer
example now reuses examples/developer/source_paths.repository_relative before
compile_ir, like existing committed IR examples. A checkout-relocation regression
checks both complete companions. Production export still hashes exact canonical
input IR including source metadata; no JSON/API semantics change (class A).
Version remains 0.5.0. Latest-head CI must pass before merge.

## D007 — R1.2 review of concrete binding checks (2026-09-18)

Review PRR_kwDOUVkARs8AAAABOD5Y_g contained one suppressed finding: allow base
contract IDs in the exporter's concrete-ID check. That suggestion applies to
authored binding compatibility, already covered by validate_bindings, but not
to CompileResult.specialized_ir: specialize explicitly replaces each device
resource type with binding.contract.type_id. Relaxing the check would admit
unselected authored IR as a purported selected result. Keep the check and add
explicit regression assertions showing base-typed authoring compiles, becomes
concrete and exports successfully, while substituted authored IR rejects before
writing. Class A clarification; no interface change, version stays 0.5.0.

## D008 — R2.1 preflight (2026-09-18)

Baseline 6126bf7c9351713125601ba8ec224af8b45d3376, packages 0.5.0. R1.2 PR #105
is remotely MERGED after review response, regression coverage and all four
latest-head CI checks. Its local test baseline is now 1016 code/tools tests.
No Executor receipt or valid new thermal/transfer export has arrived.

Existing failure (9), CSV read (14) and CSV append (6) generators already supply
case identities, input/artifact hashes and source/version provenance. Reuse those
case directories and manifest formats. Add one read-only receipt validator,
not new generators: verify exact manifest/artifact hashes, clean source, lockstep
versions, APP product/profile association, all cases/controls, commands/logs and
two CSV runs with complete before/after files. Machine completeness ends at
pending_review and never changes compiler support. Contradictory observations
remain evidence for human review; an unobservable/failed control is inconclusive.
Class B tooling detail, class C for absent host evidence. R2.2–R2.4 stay pending;
after R2.1 merges proceed to independent R3.1 under the accepted sequence.

## D009 — R2.1 review clarification (2026-09-18)

Review 5238740731 requested explicit exact argv length. The shape check now says
seven entries, matching the already-exact documented option suffix; tests reject
short, extra and non-array commands. Accepted commands and native gates do not
change. The review overview also questioned September 18 dates: the session uses
Asia/Tokyo, so September 17 16:39 UTC is September 18 01:39 JST. Keep accurate
dates and state the timezone explicitly. Class A clarification; Version remains
none and both packages stay 0.5.0. Latest-head checks remain required before merge.

## D010 — R3.1 preflight (2026-09-18)

Baseline e496f577c96a81f6e7e3d2dcaaaaae1d270577d9, packages 0.5.0. R2.1 #106
is remotely MERGED after argv correction, timezone clarification, resolved
review and four latest-head CI passes. No native receipt has arrived; conditional
R2.2–R2.4 stay pending while the accepted independent R3.1 stage proceeds.

Existing Notify is a no-result OK acknowledgement with its own service/event.
ReadWallTime and CSV establish ordered assignment-result nodes; generic typed
traversal/schema need no second JSON model. Add independent dialog markers,
nodes and queue, updating every exhaustive consumer and explicitly rejecting
AutoSuite generation. The optional queue never prompts or advances virtual time.

Event detail refinement (class B): DialogEvent records operation name, captured
message/timeout, effective outcome, elapsed duration, successful value and
optional error_code. A late accepted response becomes TIMED_OUT. A consumed
wrong-type accepted response retains ACCEPTED as its response outcome but records
dialog_response_type and no successful value. Consumed failures become observable
before raising. Missing/exhausted services and invalid arguments consume nothing
and emit no dialog event. Queue entries are frozen/copied; non-accepted outcomes
have no value. No fallback, semantic deviation or native claim is introduced.

## D011 — R3.1 review diagnostics (2026-09-18)

Review 5238920846 identified a misleading shared failure message. Distinguish
operator cancellation, Stop, timeout and exact response-type mismatch; mention
configured timeout only when one exists. Add no-timeout regressions for all
four outcomes. Correct the acknowledgement-contract sentence in the public
handbook. Class A diagnostic/documentation correction; nodes, events, codes,
state retention and native gates are unchanged. Reassessed Version remains
MINOR 0.5.0 → 0.6.0; latest-head checks and resolved review are required.

## D012 — R3.2 preflight (2026-09-18)

Baseline df426a08e41bbd114f672e8f0922421351c86160, packages 0.6.0. R3.1 #107
is remotely MERGED after both review corrections, 1089 local tests and four
latest-head CI passes. The preceding turn made progress by completing that gate.
No Executor receipt arrived; result-dialog compilation remains rejected.

Read the serialization references, catalog, representative UserDialog template
and received test.asfp. Its barcode task A81CC6E9-0955-4426-8B55-B0BF65211699
uses askforinput/text/okstop with a timeout-answer expression. Its checklist
task DCBC6267-E249-49AB-A45A-6326E5688DA8 uses showmessage/yesnostop and 1/0
answers. The ASFP hash is 9bce834bdc9981488b7a1612dcc12a390af684825f4c17712d8698bf5122b06a;
it supplies no product version. These are structural observations, not proof of
termination or bool equivalence. The primary APP has no result-bearing dialog.

Class C: implement the permitted probe/docs scope, retain all native gates and
record native status pending. Class B measurement detail: use an explicitly
supplied source ASFP and exact text/choice task IDs, hash both source bytes and
selected payloads, and clone only a validated flat UserDialog envelope into
compiled device-free logging shells. Thirty cases cover text/empty/Yes/No,
window cancellation, Stop and timeout across entry/child/two-iteration loop.
Choice probes record native integer 1/0; they do not claim a bool adapter is
accepted. No portable-node compiler bypass is added. Host receipts must inspect
all marker/value ordering and re-export the exact candidates. Add the planned
single-well barcode/property/log reference workflow now; native remains gated.

## D013 — R3.2 review coverage and navigation (2026-09-18)

Review 5239084391 includes three actionable suppressed comments. Add the author
barcode example to the explicit mypy files, add its public Examples catalog row,
and bring the internal reference guide's count/range and supplemental links up
to date. Class A coverage/navigation corrections; no probe payload, reference
semantics or native gate changes. Reassessed Version remains none (packages 0.6.0).

## D014 — R4.1 preflight (2026-09-18)

Baseline 94610f7350234f7dbf341e22042b7338e1ef63d5, packages 0.6.0. R3.2 #108
is remotely MERGED after the three review corrections, 1113 local tests and four
latest-head CI passes. The preceding turn completed that gate. No native receipt
arrived; R2 unlocks and result dialogs remain gated while independent R4 proceeds.

Inspected device declarations, typed contracts/schema, binding trust, definite
configuration analysis, reference state and target rejection paths. Configuration
analysis currently recognizes only StartAgitation. Add the new contract variant
without modifying that built-in contract or ordinary command wire records.

Class A: the planned BenchAgitator example omitted the concrete profile's explicit
required_configuration declaration required by bind_device. Correct the example.
Class B: neither planned lifecycle effect defines any command-argument meaning;
both consume saved configuration/state. Initially require an empty typed
parameters tuple and reject lifecycle arguments, including direct IR. Preserve
ordinary typed command arguments for R6. This prevents accepting values whose
effect would otherwise be silently discarded, without changing any accepted
concrete apply/disable example. Update the authority and R4.1 acceptance first.
Explicit per-command property requirements remain separate from the concrete
device's requirements so inherited command IDs retain exactly one signature.
Class C: native profiles/effects are not unlocked by reference implementation.

## D015 — R4.1 review handbook consistency (2026-09-18)

Review 5239301901 identified a stale native-command guide and FAQ, plus a
suppressed comment about the user troubleshooting table. Update those public
pages to distinguish ordinary CommandContract operations (still unsupported in
reference execution) from explicit lifecycle effects carried by DeviceCommand.
Explain device-wide/apply requirements, explicit-only disable requirements and
the separate AutoSuite adapter gate. Keep the ordinary tutorial's real rejection
example and clarify its scope. Class A documentation correction; no behavior or
wire change. Reassessed Version remains MINOR 0.6.0 → 0.7.0. Latest-head CI and
resolved review remain required before merge.

## Required entry for every next preflight

Record date/stage, current main SHA and versions, predecessor merge/CI/review,
facts inspected, discrepancy class A/B/C/D, affected contract sections/plans,
decision and why intent is preserved, required human response (if D), and
remaining native evidence. Record tests after completion separately from this
entry. Never prefill future acceptance as passed.

## Version

Version: none, planning decisions and preflight history only.
