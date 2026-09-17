# R3.1: Typed dialog results across source and JSON

## Goal

Typed dialog results across source and JSON while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r3-ordered-text-and-yesno-results).
R2.1 merged. Native implementation does not require CSV unlocking; any necessary failure mechanism requires its own native proof.
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

Implement request_text/ask_yes_no, whole-RHS lowering, RequestText/AskYesNo nodes, explicit queued responses and ordered immutable outcome events exactly as in the contract. Wire both result types through validation, specialization, traversal and interpreter; explicitly reject new nodes in AutoSuite until verified.

## Non-goals

No Notify changes, fallback answers, recoverable cancellation branches, implicit prompt, expression embedding or device-measurement API.

## Acceptance

Test text/bool destinations, False and empty-text successes, wrong response type, missing/exhausted service, timeout boundary, cancellation/Stop, unchanged destination after failure and no later effects. Test capture order, child/loop use, copied response snapshots, source/IR/JSON parity and old v4 bytes.

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

Implementation expectation: MINOR, adds result-bearing operator interactions.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
