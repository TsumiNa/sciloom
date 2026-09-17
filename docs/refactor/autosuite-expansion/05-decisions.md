# Decisions and implementation reassessments

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

## Required entry for every next preflight

Record date/stage, current main SHA and versions, predecessor merge/CI/review,
facts inspected, discrepancy class A/B/C/D, affected contract sections/plans,
decision and why intent is preserved, required human response (if D), and
remaining native evidence. Record tests after completion separately from this
entry. Never prefill future acceptance as passed.

## Version

Version: none, planning decisions and preflight history only.
