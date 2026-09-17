# R2.4: Accept verified CSV append

## Goal

Accept verified CSV append while preserving the accepted semantic contract.

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

Conditional PR: test current six append cases twice with exact before/after bytes and status/marker traces. Incorporate UI enum proof as label evidence only. Unlock narrowly when append preservation, encoding and each selected error policy match the existing AppendCsv contract.

## Non-goals

No overwrite-as-append, silent encoding substitution, file repair/implicit directory creation or try-policy bypass for missing byte evidence.

## Acceptance

Verify sentinel preservation, two appended records, Unicode, quotes, line endings, empty values and missing-parent outcomes. Default-fatal forms need relevant R2.2 acceptance. If target bytes cannot match the contract, report class D alternatives; do not change existing v4 meanings to fit the platform.

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

Implementation expectation: MINOR, enables verified native CSV append forms.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
