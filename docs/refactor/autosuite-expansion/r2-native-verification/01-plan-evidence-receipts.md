# R2.1: Organize native measurement receipts

## Goal

Organize native measurement receipts while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r2-evidence-and-native-unlocking).
R1.2 merged. Unlock PRs additionally require the receipts below and no other implementation PR open.
Current code status: implemented in this PR; review/merge pending. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Distill screenshot/XML/manual findings into autosuite/docs and link exact evidence identifiers. Update the CSV UI mapping statement without claiming byte behavior. Reuse existing failure/CSV generators and manifests; add only missing receipt validation needed to associate exact version, hashes, controls and outputs. Keep all gates unchanged.

## Non-goals

No public compiler unlock, uploaded raw evidence, parallel generator framework or user-supplied receipt bypass.

## Acceptance

Check receipt completeness and mismatched/dirty inputs, version/profile association and missing-control handling. Run tools tests, docs checks and read-only corpus audit. Verify screenshot ASFP is labeled incomplete and September 17 APP profile unknown. Preserve pending native status when no host measurement exists.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

The checkout-only validate_native_receipt module reuses the existing three case
directories/manifests; it verifies clean-source association, actual file hashes,
product/profile, complete controls and two CSV runs with byte continuity. Complete
receipts remain pending_review; contradictory measurements are retained for human
review. No compiler source or public author API changes. The receipt format and
CLI are documented in autosuite/docs/35_NATIVE_MEASUREMENT_RECEIPTS.md; screenshot
facts and exact image hashes are in 34_EDITOR_SCREENSHOT_EVIDENCE.md.

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Initial local acceptance: 30 focused receipt tests; 1046 total core/target/example/tools
tests; 97 website tests; Ruff/format, mypy (132 shipped source files), strict docs
build, smoke, recipe and read-only corpus audit passed. All 182 local links in
33 plan/new reference documents resolve. CLI help and synthetic complete/error
paths ran; no actual host receipt or native pass is claimed.

Review clarification: all 50 tools tests (including 33 receipt cases), Ruff and
format pass after exact argv-length coverage. Version decision is unchanged.

Version: none, only internal evidence documentation, tests and checkout tooling;
both distributed packages remain 0.5.0. No native unlock or publication.
