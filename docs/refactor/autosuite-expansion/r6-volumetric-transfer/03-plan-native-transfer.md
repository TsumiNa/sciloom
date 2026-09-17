# R6.3: Map one evidenced fixed-tool transfer

## Goal

Map one evidenced fixed-tool transfer while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r6-location-arguments-and-bounded-transfer).
R6.2 reviewed and remotely merged.
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

Before implementation complete the native constructor/binding example from a valid minimal transfer export with explicit tool/channel/calibration/position/rinse fields. Validate deployment connectivity and one-to-one well addresses. Emit a typed native transfer payload only for statically proven supported locations/parameters.

## Non-goals

No inactive-field defaults, silent no-rinse mode, multi-channel/multi-row plans, dynamic routing, auto-chunking or runtime guard bypass.

## Acceptance

Test UI-to-XML indexing only inside target mapping, one source/destination pair, channel identity, tool capacity, flow/depth limits, rinse route and same-APP deployment provenance. Compare valid templates/re-export and Executor simulation. Runtime selections requiring unverified checks remain rejected. Absent evidence means gated diagnostics/probes, not a fake public profile.

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

Implementation expectation: MINOR, adds verified single-pair native transfer support; reassess to none for tooling/docs-only gated scope.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
