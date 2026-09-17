# R4.1: Explicit lifecycle command contracts

## Goal

Explicit lifecycle command contracts while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r4-explicit-command-effects-and-typed-configuration).
R3 implementation PRs merged or completed as implemented/gated. Recheck that R5's planned concrete thermal needs justify each abstraction.
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

Add the lifecycle command-contract variant and decorator options; preserve ordinary command contracts and dedicated agitation nodes. Resolve property requirements, validate inherited/conflicting contracts, analyze definite configuration through branches/calls/loops and execute trusted logical lifecycle effects. Add the independent contributor example from the contract.

## Non-goals

No method-name inference, dynamic code import, schema migration, arbitrary result values, general plugin registry or unknown command simulation.

## Acceptance

Prove unchanged old JSON bytes; new variant round trips; incomplete/conditional config rejection; apply snapshots; disable retains state; JSON trusted-contract mismatch rejection; ancestor consistency; child/shared resource behavior. Unknown ordinary commands remain rejected. Explicitly handle/reject the variant in every consumer.

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

Implementation expectation: MINOR, adds typed command effects and contributor declarations.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
