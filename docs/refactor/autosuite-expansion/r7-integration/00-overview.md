# R7: Integrated workflows and delivery state

## Goal

Demonstrate end-to-end expression and truthful layer-by-layer support.

## Authority and dependencies

Use the [single contract](../01-contract.md#r7-integrated-results).
R1–R6 implementation PRs merged; native unlocks only where evidence exists.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R7.1 | [Verify complete operator and equipment workflows](01-plan-workflows.md) | Pending |

Native status: Reported per constituent capability, never inferred from integration tests.
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
