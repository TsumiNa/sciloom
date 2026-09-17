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

## Required entry for every next preflight

Record date/stage, current main SHA and versions, predecessor merge/CI/review,
facts inspected, discrepancy class A/B/C/D, affected contract sections/plans,
decision and why intent is preserved, required human response (if D), and
remaining native evidence. Record tests after completion separately from this
entry. Never prefill future acceptance as passed.

## Version

Version: none, planning decisions and preflight history only.
