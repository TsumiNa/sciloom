# R1.1: Read-only deployment facts and reports

## Goal

Read-only deployment facts and reports while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r1-deployment-conditions-and-review-artifacts).
R0 merged.
Current code status: implemented; merged #104. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Add immutable deployment facts, status/report records and layout APP-byte provenance as specified in the contract. Parse gzip APP without writes, preserve unknown settings, reject malformed or contradictory settings, and keep manually constructed layouts usable with unknown provenance. Introduce the shared assessment function without changing core Target/Artifact.

## Non-goals

No compile rejection integration yet; no native reset conclusion, APP edits, state migration or deployment-driven device discovery.

## Acceptance

Test valid/missing/invalid/duplicate reset values, unsupported product version classification, exact-byte hashes, same/different/unknown layout provenance, malformed input and immutable reports. Corpus fixtures are optional; use small synthetic APPs outside corpus. Existing JSON and ASFP bytes remain unchanged.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

Local acceptance (2026-09-18): 982 core/target/example tests and 13 tools tests
passed; 97 website tests and strict build passed. Ruff/format and mypy (130 source
files) passed, as did smoke, recipe validation, read-only corpus audit and all
42 CI example/syntax commands. Existing example companions were unchanged.
Native reset behavior remains unmeasured. Production target integration is R1.2.

PR #104 review corrected the version diagnostic to show the bare expected native
product version rather than the internal target ID. Its regression, all 31
deployment tests, Ruff/format and mypy passed. Scope and version remain unchanged.

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: MINOR 0.3.15 → 0.4.0, adding public deployment facts/report records and
layout source provenance. Both workspace packages change together; no publication.
