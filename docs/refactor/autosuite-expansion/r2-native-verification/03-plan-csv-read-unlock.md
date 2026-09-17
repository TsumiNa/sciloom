# R2.3: Accept verified literal CSV reads

## Goal

Accept verified literal CSV reads while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r2-evidence-and-native-unlocking).
R2.1 merged; exact capability receipts accepted; no other implementation PR open. Default-fatal policies additionally require relevant R2.2 propagation proof.
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

Conditional PR: compare native parsing, literal versus expression treatment, scalar conversion, column statuses and failure behavior against current ReadCsv semantics. Unlock only demonstrated modes/types and version/profile; reuse existing public read APIs and tests.

## Non-goals

No rewrite of reference CSV semantics, expression execution from input text, automatic malformed-data recovery or broad decoder aliases.

## Acceptance

Require native receipts for current probe cases, row/header/column behavior and exact values/status aggregation. Ordinary default-fatal forms depend on R2.2's relevant propagation evidence; try forms still need literal/typed conversion proof. Keep other forms rejected. Run reference/source/JSON/native mapping regressions.

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

Version: MINOR, enables verified native CSV read forms.
Keep workspace versions lockstep; choose exact from/to versions from the current baseline after implementation.
Reassess after final review if the shipped scope changes. No publication.
