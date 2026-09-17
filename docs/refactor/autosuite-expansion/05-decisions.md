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

## D016 — R4.2 preflight (2026-09-18)

Baseline da488c4b30c2d99474f2cfc2afa86b0d2e7f7c3d, packages 0.7.0. R4.1 #109
is remotely MERGED after all handbook feedback, 1140 code/tool/example tests,
98 website tests and four latest-head CI passes. The previous goal turn made
progress by completing that gate. The new branch is clean on fetched main.

Inspected private storage, capture, call binding, function list isolation,
selection ancestry and physical identity checks. Read serialization methods,
confirmed structures/mappings/goldens, catalog and applicable task templates,
plus agitation and array mapping evidence. Some representative templates are
historical minimal forms; existing FIXED/current mappings remain authoritative.

Class B implementation detail: retain scalar/list types per resource/property
key. Existing array I/O rewriting would otherwise introduce a second output
buffer and overwrite private device list state at return. Private device arrays
therefore receive their own whole-list capture/initialization and isolated call
input/output buffers with normal-return copyback. Preserve existing scalar
allocation order and identity seeds. No change to public Program or JSON.

Class A correction required by the plan: current target globally rejects repeated
zone names and core rejects overlapping wells across unrelated logical selections.
Use trusted physical identity for cross-resource conflicts; retain within-selection
well disjointness and APP ancestry validation. Different names cannot disguise
one actuator, and a repeated well alone is not proof of an actuator collision.
AutoSuite constructor checks reuse the resolved DeviceBindings identity rules
instead of maintaining a parallel bare-device-number conflict directory.
No family-prefixed fabricated identities or new plugin protocol is introduced.

Class C: no new native receipt/profile has arrived. New lifecycle emission and
dynamic selection remain rejected. Synthetic configuration transport tests are
compiler/wire-model evidence only, not new native profile acceptance. The
authority and R4.2 scope now state these boundaries before implementation.

## D017 — R5.1 preflight (2026-09-18)

Baseline 203df1a38b24cada61887d11fa709f4d17e47906, packages 0.7.1. R4.2 #110
is remotely MERGED after review 5239498885 (zero actionable/suppressed findings),
1144 code/tool/example tests, 98 website tests, 48 example commands and all four
latest-head CI checks. This goal turn made progress completing that gate.
Created the next branch only after fetching merged main.

Inspected unit values, source unit lowering, field/device declarations, typed
expression validation, JSON, reference coercion/snapshots, logging/CSV and target
encoding/guards. Existing multiplicative quantity rules cannot express affine
temperature safely: absolute subtraction changes dimension, scaling is invalid,
and a CSV unit represented by one literal cannot encode a Celsius offset.

Class B bounded refinement, recorded in the authority before implementation:
absolute source unit construction is literal-only; signed difference/rate unit
ratios follow existing conventions. Thermal CSV reads explicitly reject all
three new types rather than interpret temperatures as dimensionless numbers.
Logging and append retain canonical values. No new conversion API or wire model.
Keep existing quantity wire forms and arithmetic unchanged.

Class C: there is no new native precision/re-export receipt. The observed 273.16
offset is insufficient to define exact thermal encoding or safe runtime range
checks. R5.1 therefore implements core/reference values and explicit AutoSuite
type rejection, as the plan permits; native mapping/profile remains R5.3 and
gated if evidence is still absent. Core uses 273.15, without vendor adjustment.
No class D semantic compromise or human decision is required.

## D018 — R5.1 review declaration-path coverage (2026-09-18)

Review 5239643141 has no inline threads and one suppressed actionable comment:
thermal device declaration mappings lack focused tests. Add six cases covering
all three scalar types as both properties and command arguments, including
homogeneous lists. Inspect the actual contributed typed contracts, round-trip
their complete Program through JSON and retain the built-in agitation contract.
Declaration bodies must not execute. Class A validation-coverage correction;
no interface or production behavior changes. Version remains MINOR 0.7.1 → 0.8.0.
Recheck latest-head CI and every review surface before merge.

## D019 — R5.2 preflight (2026-09-18)

Baseline c4abeb82f906b10c3c4a9f13fc3eab0475855247, lockstep 0.8.0. Previous goal
turn made progress: R4.2 #110 and R5.1 #111 are remotely MERGED. R5.1's suppressed
declaration test finding was fixed, 1279 tests and all four latest-head CI jobs
passed, with no unresolved thread. Current worktree was clean; R5.2 starts only
from fetched main after rechecking remote state.

Inspected Heater plan, operation registration/lowering, built-in contract
protection, definite configuration, fixed/candidate binding validation and
reference lifecycle snapshots. R4's defined effects already express both heater
commands and R5.1 supplies both property types. No new task or effect framework
is needed. Class A: define stable heater IDs in the authority and core, and use
the existing decorator/contracts without modifying Agitator or BaseDevice.

Class B scope enforcement: generic candidate binding would otherwise make a new
heater family eligible for dynamic selection automatically. The authority now
explicitly rejects heater/derived candidate bindings through the existing shared
binding-use validation, before compilation/reference execution. Fixed binding
and generic logical lifecycle behavior are retained; agitation selection is
unchanged. This implements the accepted fixed-only stage without a new capability
framework or changing prior JSON.

Class C: no new native export/precision receipt is present. Explicit reference
contributors demonstrate extension and fixed binding only, not a hardware profile.
AutoSuite thermal values/commands remain rejected. Fixed virtual waiting does
not establish measured temperature. No class D deviation requires interruption.

## D020 — R5.2 review: inherited startup requirements (2026-09-18)

Review 5239812251 / inline 4040162010 found a concrete bypass: a derived Heater
can override device-wide required_configuration with an empty tuple. Generic
APPLY_AND_ENABLE correctly obeys the concrete contract, so the initial family
declaration would then permit unconfigured startup. Class B correction preserving
the original mandatory two-setting intent: place temperature/ramp-rate IDs on
the protected start LifecycleCommandContract as explicit requirements as well.
Update the authority/scope before code. Existing R4 command/binding validation
then rejects missing writable settings and unconfigured start, even when the
derived device-wide list is empty. Do not change older family or generic effect
semantics. No new compatibility wrapper or JSON model is needed.

Two suppressed comments identify the same stale public device-contract reference.
Update shipped families, protected IDs and thermal value types there. Reassessed
Version remains MINOR 0.8.0 → 0.9.0; review fixes preserve the planned API meaning.

## D021 — R5.3 preflight and evidence-limited scope (2026-09-18)

Baseline 1711817937b702ab515656fd142cedf7ce98e6e6, lockstep 0.9.0. R5.2 #112
is remotely MERGED after review 5239812251, inherited-start requirement and both
suppressed documentation fixes, 1299 tests, 98 website tests and four successful
latest-head CI jobs (35259110478). The only review thread was replied to and
resolved. This goal turn made progress completing that gate; branch creation
followed fetching merged main.

Inspected primary gzip APP bytes, all eight SATaskSetTemperature payloads,
thermal encoding/validation rejection, fixed Heater examples, existing receipt
suites and the screenshot register. Primary APP SHA is recorded in doc 37. All
eight gradients are zero; six tasks use variable zones with blank controller
fields. An explicit on/off pair identifies thermostat 0.1 but supplies no exact
entered-temperature, nonzero-gradient or execution receipt. No new evidence or
Executor host is available; Q6/Q7/Q9 remain unresolved.

Class C, using R5.3's accepted fallback: deliver capture documentation and reuse
existing executable diagnostics. Do not invent a profile constructor, guess a
273.16 conversion, activate native emission or start a parallel receipt framework.
The exact immutable constructor remains an entry condition for a future unlock
PR. Core/reference behavior is unchanged and R6 may continue after this PR's
review/merge gate. Class A: refresh stale overview status sentences and links.
No class D semantic compromise or human decision is required.

## D022 — R5.3 review: traceable observations and status (2026-09-18)

Review 5239920819 / inline 4040252205 requests the six remaining task IDs and
their individual payload mappings. Record all eight, preserving repeated payloads
as distinct tasks. Both suppressed findings are also addressed: update the
canonical reference guide to 38 documents (00–37), and replace the authority's
outdated second-native-profile wording with an explicit future requirement.
Class A documentation corrections; no evidence is promoted to native acceptance.
Version remains none, packages 0.9.0; recheck links/docs and read-only corpus audit.

## D023 — R6 group / R6.1 preflight (2026-09-18)

Baseline d2032da38053aba54c0e7479a4b638a758af2823, lockstep 0.9.0. Previous goal
turn made progress: R5.2 #112 and R5.3 #113 are remotely MERGED. R5.3 review
5239920819 and both suppressed findings were addressed; latest-head CI
35260216562 passed all four jobs, the thread is resolved, and main was fetched
before this branch. Local checks included 26 thermal gate tests, 98 website tests,
strict docs, examples and read-only corpus audit. Native receipts remain absent.

Inspected typed contract/schema conversion, device declaration and argument
lowering, field defaults, quantity arithmetic, specialization, reference coercion,
CSV unit scaling and native encoding guards. Existing CommandParameter and
PropertyContract share scalar/list types, but only command parameters may gain
ZoneType. The source already orders named arguments by the declared signature;
keep old wire forms and property boundaries. Class A: reuse those mechanisms.

Class B bounded completion of the quantity contract before code: flow/length
use existing signed multiplicative arithmetic, scalar/list fields and canonical
logging/CSV append; explicit matching units also allow reference CSV reads through
the existing scale-only contract. No new CSV interface or dimensional inference.
Unknown command reference execution remains rejected in R6.1; argument capture
and transfer action ordering become executable with R6.2's defined effect.

Class C: native transfer profile/precision/guard evidence is absent. New quantity
encoding is explicitly rejected in AutoSuite, including direct emitter paths,
until the evidence-backed adapter stage. Add exact author/contributor examples
to the authority now and runnable counterparts during R6.1. No placeholder
LiquidHandler API is shipped before its semantics. No class D deviation.

## D024 — R6.2 preflight (2026-09-18)

Baseline dd7e4eb816cdc4ab409d5896264c5ec30edec08a, lockstep 0.10.0. The previous
goal turn made progress by implementing and remotely merging R6.1 #114. Review
5240080940 had no actionable/suppressed comments or threads; its broad concern
was answered with full regression evidence. All four latest-head CI jobs
35261240293 passed, alongside 1399 local tests, 98 website tests and 55 examples.
This branch follows a fresh main fetch and clean-worktree check.

Inspected binding validation and all binding consumers, configuration fixed
points, specialization, runtime argument evaluation, location services and event
snapshots. Typed Zone/FlowRate now express the planned signature directly.
Class A: add one protected LiquidHandler contract and recognize its explicit
transfer ID; do not create another IR statement or lifecycle effect.

Class B bounded details, recorded in the authority before code: the new binding
record wraps one fixed DeviceBinding and exposes its facts to existing consumers;
transfer requires it and rejects candidate selection. All three family settings
are mandatory even if a derived profile narrows its device-wide requirements.
The known transfer effect also requires any additional concrete requirements.
Successful transfer updates last-applied configuration while preserving enabled
state; it never invents a start/stop or liquid inventory. Arguments are evaluated
once in signature order even for reordered direct-IR/JSON argument tuples.
Allowed-well identity membership is checked against explicit reference locations
at the requesting operation; constructing a binding does not access equipment.

Class C: no new native tool/channel/calibration/rinse receipt exists. Keep native
transfer and quantity rejection, and publish only a reference contributor example.
No class D change to lifetime, fault behavior, old JSON or scope is needed.

## Required entry for every next preflight

Record date/stage, current main SHA and versions, predecessor merge/CI/review,
facts inspected, discrepancy class A/B/C/D, affected contract sections/plans,
decision and why intent is preserved, required human response (if D), and
remaining native evidence. Record tests after completion separately from this
entry. Never prefill future acceptance as passed.

## Version

Version: none, planning decisions and preflight history only.
