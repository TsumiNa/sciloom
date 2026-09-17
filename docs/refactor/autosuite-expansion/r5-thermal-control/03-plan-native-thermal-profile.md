# R5.3: Bind an evidenced fixed thermal profile

## Goal

Bind an evidenced fixed thermal profile while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R5.2 reviewed and remotely merged.
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

Before implementation finalize the exact immutable profile constructor and binding example in the contract using a valid export, installed physical identity, control mode/ranges and conversion measurements. Add typed Heat/Cool payload adaptation at the minimal shared backend seam demonstrated by this second profile.

## Non-goals

No guessed thermal profile, automatic firmware support, copying dormant fields as active settings, dynamic thermal selection, telemetry or portable 273.16 conversion.

## Acceptance

Measure exact 0/20/50/negative Celsius inputs and nonzero gradient, inspect original/re-export payloads and Executor markers. Verify fixed binding, range validation, start/stop and colocated distinct actuators. If evidence is absent, implement diagnostic/probe documentation only and retain native rejection; finalize constructor before any profile code.

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

Version: MINOR, adds verified thermal profile support; reassess to none for tooling/docs-only gated scope.
Keep workspace versions lockstep; choose exact from/to versions from the current baseline after implementation.
Reassess after final review if the shipped scope changes. No publication.
