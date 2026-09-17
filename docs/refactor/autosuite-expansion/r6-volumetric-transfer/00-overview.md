# R6: Location parameters and single-pair transfer

## Goal

Express actual ordered transfer intent without smuggling positions through strings or a single-controller context.

## Authority and dependencies

Use the [single contract](../01-contract.md#r6-location-arguments-and-bounded-transfer).
R5 implementation PRs merged or implemented/gated. Native transfer requires its own valid profile and proof for any runtime guards used.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R6.1 | [Typed command locations and transfer quantities](01-plan-location-arguments.md) | Merged (#114) |
| R6.2 | [Bounded reference transfer effect](02-plan-transfer-semantics.md) | Merged (#115) |
| R6.3 | [Map one evidenced fixed-tool transfer](03-plan-native-transfer.md) | Merged #116 (capture procedure; native gated) |

Native status: Tool/channel/calibration/rinse profile pending.
R6.1 provides typed Zone command arguments and flow/length quantities through
source/IR/JSON/reference services. Native encoding is rejected; the transfer
family/effect is implemented in R6.2 with explicit reference facts. Native-unlock prerequisites are distinct
from review/merge prerequisites. Finish each PR green and remotely squash merged
before beginning another; an implemented/gated stage preserves its rejection.

## Non-goals

The scope and exclusions in each PR and the contract are binding. Do not expand
this group to compensate for missing evidence or introduce placeholder APIs for
deferred capabilities.

## Acceptance

Use [common acceptance](../02-execution-rules.md#common-acceptance) and the
stage-specific tests. Record code checks and native receipts separately.
Update status, examples, affected public handbook pages and the contract together.

## Version

Version: none, this overview defines a refactor without changing shipped code.
Each implementation PR makes the version decision in its own plan.
