# R6.1: Typed command locations and transfer quantities

## Goal

Typed command locations and transfer quantities while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r6-location-arguments-and-bounded-transfer).
R5 implementation PRs merged or implemented/gated. Native transfer requires its own valid profile and proof for any runtime guards used.
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

Allow existing ZoneType in CommandParameter while preserving property type boundaries. Add FlowRate and Length values and their narrow arithmetic/unit APIs. Update source declarations, argument validation, specialization and explicit consumer handling without changing old scalar/list serialization.

## Non-goals

No list[Zone], arbitrary record/dict parameters, property locations, new result-command framework or string-encoded coordinates.

## Acceptance

Test Zone source/IR/JSON argument round trips, argument identity and capture order, scalar/list baseline bytes, immutable Zone values, rejection of unsupported property/argument types, flow/length finite values and unit conversions. AutoSuite unknown commands remain explicitly rejected.

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

Version: MINOR, adds typed location command arguments and physical quantities.
Keep workspace versions lockstep; choose exact from/to versions from the current baseline after implementation.
Reassess after final review if the shipped scope changes. No publication.
