# R5.2: Fixed heater configuration and lifecycle

## Goal

Fixed heater configuration and lifecycle while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R5.1 reviewed and remotely merged.
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

Add Heater family properties and lifecycle contracts, author-to-IR lowering and reference state/events using R4. Require both temperature and ramp_rate explicitly. Provide source/IR/JSON warm-sample examples and mixed heater/shaker logical programs.

## Non-goals

No getters, wait-to-temperature, implicit start/stop, physical simulation or unsupported AutoSuite profile acceptance.

## Acceptance

Test incomplete/branch-dependent configuration, configuration changes while running, explicit reapply, stop retention, shared/cross-call state and separation from shaker properties. Confirm fixed wait only advances explicit virtual time and never claims measured temperature. Native-unavailable commands remain rejected.

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

Version: MINOR, adds the Heater author family and reference semantics.
Keep workspace versions lockstep; choose exact from/to versions from the current baseline after implementation.
Reassess after final review if the shipped scope changes. No publication.
