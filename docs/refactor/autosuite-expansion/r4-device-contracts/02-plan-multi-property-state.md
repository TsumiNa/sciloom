# R4.2: Preserve typed multi-property backend state

## Goal

Preserve typed multi-property backend state while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r4-explicit-command-effects-and-typed-configuration).
R4.1 reviewed and remotely merged.
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

Replace the backend's single speed storage assumption with resource/property keyed typed state and call transport. Keep private symbols outside Program. Prepare direct typed profile dispatch and physical-actuator conflict checks without publishing an unnecessary one-profile protocol. Use synthetic contributor cases to verify preservation, not as native profile evidence.

## Non-goals

No second source of semantic configuration, family-name fake physical identities, blanket same-zone rejection for distinct real actuators, or changing existing shaker identity seeds/output.

## Acceptance

Compare existing shaker ASFP baselines byte-for-byte. Test two properties with different types, capture before later assignments, nested calls, shared/distinct resources and saved versus applied snapshots. Preserve current location gates. Test actual-identity alias rejection separately from colocated different actuators.

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

Version: none, this revision records a plan and changes no shipped code.

Implementation expectation: PATCH, contained backend refactor preserving existing supported behavior.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
