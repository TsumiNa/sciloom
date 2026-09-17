# R6.2: Bounded reference transfer effect

## Goal

Bounded reference transfer effect while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r6-location-arguments-and-bounded-transfer).
R6.1 reviewed and remotely merged.
Current code status: implemented; merged #115. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Implement LiquidHandler family, explicit flow/air-gap configuration, single-pair transfer DeviceCommand semantics and immutable TransferEvent. Add typed target-neutral trusted transfer-binding facts for physical identity, allowed wells and usable capacity outside Program. Validate all captured values and configuration before the event.

D024 fixes the concrete binding/event contract before implementation. Require
all family settings independently of subclass overrides, reject dynamic transfer
selection, capture arguments in declared order across JSON, and update only
last-applied configuration on success without an enable/disable fiction.

## Non-goals

No physical inventory simulation, native equipment access, lifecycle enable fiction, same-well transfer, multi-channel packing, splitting, implicit defaults or untrusted JSON limits.

## Acceptance

Test empty/multiple/unknown/same wells, ordering, missing services/bindings/configuration, incompatible trusted contracts, positive flow/volume and nonnegative gap, capacity including gap, immutable events, cross-call configuration and failure-before-action. Compare author/direct IR/JSON execution; unknown commands still reject.

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

## Local acceptance (2026-09-18)

50 added focused tests pass; full source/target/examples/tools suite: 1449 passed.
Website tooling: 98 passed; 57 CI example/syntax commands pass and existing
companions are unchanged. Ruff check/format (326 files), mypy (145 sources),
strict website build, AutoSuite smoke and recipe validation pass. 180 relative
plan links and 16 Python contract snippets validate. The API catalogue check
initially found the missing TransferEvent API entry; it was added and the full
website suite rerun successfully. The review follow-up rechecked the full suite (1449), website tools (98), strict
build, Ruff and mypy. No native receipt or Executor result exists.

## Version

Version: MINOR 0.10.0 → 0.11.0, lockstep. Adds LiquidHandler,
TransferDeviceBinding and bounded TransferEvent reference semantics. Existing
JSON v4 vocabulary and baseline output remain unchanged. No tag or publication.
Reassess the decision if review changes the shipped scope.
