# R3.2: Map proven operator dialog outcomes

## Goal

Map proven operator dialog outcomes while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r3-ordered-text-and-yesno-results).
R3.1 reviewed and remotely merged.
Current code status: implemented/gated; review/merge pending. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Obtain minimal valid result-bearing native exports and generate bounded host probes using current tooling conventions. Map accepted text and yes/no outcomes only where cancellation/Stop/timeout policy can be preserved. Document unsupported variants and current gate reasons.

Preflight D012 selects implemented/gated tooling scope: exact source/task selectors,
validated flat payloads, thirty entry/child/loop probes, source/artifact hashes and
manual host receipts. Reuse compiled logging/control shells and existing source
provenance checks. No public native mapping is enabled without new evidence.
Include a runnable single-well barcode/property/log reference example and tests.

## Non-goals

No timeout default answer masquerading as termination, hidden global recovery state, silent weakened interaction or inferred human acknowledgement.

## Acceptance

Require downstream marker controls for accepted text, empty text, Yes, No, cancel, Stop and configured timeout, including child/loop use. Native-unverified forms remain rejected. Demonstrate barcode input to single-well metadata/log in reference execution now and native only when all constituent gates pass.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

Local acceptance (2026-09-18 Asia/Tokyo): 1113 code/example/tools tests and
97 documentation-tool tests passed, along with Ruff lint/format, mypy, strict
site build, smoke, recipe validation and 47 CI example/syntax commands. The
read-only corpus audit passed (271 files, 127 archive entries, 52 function XML
matches, 67 templates). Generation against the received test.asfp produced all
30 candidates in scratch; its exact source hash was retained and evidence was
not modified. This is generation/static/reference evidence only, not Executor.

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: none, only measurement tooling, examples, tests and documentation change;
both packages remain 0.6.0. No shipped native adapter or new public interface is
enabled, and all result-dialog gates remain intact. No tag or publication.
