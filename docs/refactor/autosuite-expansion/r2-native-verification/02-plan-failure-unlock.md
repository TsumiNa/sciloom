# R2.2: Accept verified native failure propagation

## Goal

Accept verified native failure propagation while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r2-evidence-and-native-unlocking).
R2.1 merged; exact capability receipts accepted; no other implementation PR open.
Current code status: pending. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Conditional PR: evaluate existing nine failure/control probes across entry, child and loop, including caller-after markers. Scope any guard unlock to verified control flow, primitive, version and profile. Update corresponding target rejection tests and evidence matrix, not all guard-dependent capabilities at once.

## Non-goals

No error-latch substitute, broad unchecked flag, removal of unrelated CSV/location/value gates or acceptance based on exit status alone.

## Acceptance

Require matching source/artifact/APP receipts, successful controls, correct native failure and absence of all forbidden later markers. Inspect re-exports. Add regression tests for the exact unlocked path and retained rejection outside it. If behavior contradicts fatal semantics, stop under class D rather than weaken it.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: MINOR, enables a previously rejected native capability.
Keep workspace versions lockstep; choose exact from/to versions from the current baseline after implementation.
Reassess after final review if the shipped scope changes. No publication.
