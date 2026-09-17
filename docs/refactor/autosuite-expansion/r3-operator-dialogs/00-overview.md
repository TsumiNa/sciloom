# R3: Ordered operator results

## Goal

Express text and yes/no input with explicit reference responses and fatal cancellation/timeout.

## Authority and dependencies

Use the [single contract](../01-contract.md#r3-ordered-text-and-yesno-results).
R2.1 merged. Native implementation does not require CSV unlocking; any necessary failure mechanism requires its own native proof.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R3.1 | [Typed dialog results across source and JSON](01-plan-dialog-semantics.md) | Pending |
| R3.2 | [Map proven operator dialog outcomes](02-plan-native-dialogs.md) | Pending |

Native status: Result, cancel, Stop and timeout behavior pending.
No stage below is already implemented. Native-unlock prerequisites are distinct
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
