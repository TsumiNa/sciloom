# R5: Temperature and fixed thermal control

## Goal

Validate extensibility using a real second equipment family with explicit staged settings and lifecycle.

## Authority and dependencies

Use the [single contract](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R4.2 merged; R5.3 additionally needs exact profile and conversion evidence or must remain gated.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R5.1 | [Typed absolute temperature and rates](01-plan-temperature-values.md) | Merged #111 |
| R5.2 | [Fixed heater configuration and lifecycle](02-plan-heater-semantics.md) | Implemented in this PR; review/merge pending |
| R5.3 | [Bind an evidenced fixed thermal profile](03-plan-native-thermal-profile.md) | Pending |

Native status: Thermal profile and apparent temperature offset unresolved.
R5.1 provides core/reference thermal values, typed fields/lists and JSON v4;
AutoSuite explicitly rejects thermal types pending native encoding evidence.
R5.2 adds the fixed Heater family, protected built-in signatures, generic
configuration/lifecycle behavior and executable source/direct-IR/JSON examples.
R5.3 remains pending. Native-unlock prerequisites are distinct
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
