# R2: Native evidence and existing capability acceptance

## Goal

Turn isolated observations into narrowly scoped acceptance evidence for capabilities already modeled in core.

## Authority and dependencies

Use the [single contract](../01-contract.md#r2-evidence-and-native-unlocking).
R1.2 merged. Unlock PRs additionally require the receipts below and no other implementation PR open.
Read [preflight and difference handling](../02-execution-rules.md) before every
PR. Record decisions before revising interfaces; material differences require
an explicit developer decision.

## Ordered PRs

| Stage | Outcome | Code status |
| --- | --- | --- |
| R2.1 | [Organize native measurement receipts](01-plan-evidence-receipts.md) | Merged #106 |
| R2.2 | [Accept verified native failure propagation](02-plan-failure-unlock.md) | Pending |
| R2.3 | [Accept verified literal CSV reads](03-plan-csv-read-unlock.md) | Pending |
| R2.4 | [Accept verified CSV append](04-plan-csv-append-unlock.md) | Pending |

Native status: Failure, read and append native gates pending.
The read-only checker records pending_review for complete receipts. No host
receipt exists yet; R2.2–R2.4 remain pending, with compiler gates unchanged.
After R2.1 merge, independent R3.1 proceeds under the accepted sequence.
Native-unlock prerequisites are distinct
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
