# R1: Deployment conditions and persistent state

## Goal

Make deployment-dependent state assumptions explicit while retaining offline compilation.

## Authority and dependencies

Use the [single contract](../01-contract.md#r1-deployment-conditions-and-review-artifacts).
R0 merged.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R1.1 | [Read-only deployment facts and reports](01-plan-deployment-facts.md) | Merged #104 |
| R1.2 | [Enforce known deployment incompatibilities](02-plan-state-guards.md) | Implemented in this PR; review/merge pending |

Native status: Reset=0/1 lifetime experiments pending.
Four measurement bundles and their host procedure are available; no native
results have been received. Native-unlock prerequisites are distinct
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
