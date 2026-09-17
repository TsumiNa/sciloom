# R4: Command effects and typed configuration

## Goal

Allow a second device family without copying shaker-only state logic or weakening typed contracts.

## Authority and dependencies

Use the [single contract](../01-contract.md#r4-explicit-command-effects-and-typed-configuration).
R3 implementation PRs merged or completed as implemented/gated. Recheck that R5's planned concrete thermal needs justify each abstraction.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R4.1 | [Explicit lifecycle command contracts](01-plan-command-effects.md) | Implemented in this PR; review/merge pending |
| R4.2 | [Preserve typed multi-property backend state](02-plan-multi-property-state.md) | Pending |

Native status: Native profile support remains bounded; no new physical claims.
R4.1 provides typed declarations, definite configuration and reference effects;
AutoSuite explicitly rejects new lifecycle commands pending profile adapters.
R4.2 remains pending. Native-unlock prerequisites are distinct
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
