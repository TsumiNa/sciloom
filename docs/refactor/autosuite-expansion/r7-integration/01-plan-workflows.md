# R7.1: Verify complete operator and equipment workflows

## Goal

Verify complete operator and equipment workflows while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r7-integrated-results).
R1–R6 implementation PRs merged; native unlocks only where evidence exists.
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

Publish runnable author/developer counterparts for barcode/property/log, heater/fixed-wait/stop and single-pair transfer/log; reuse current property/log/location services. Include mixed old/new devices and shared cross-function configuration. Produce actual same-base companions and a Python/IR/JSON/reference/static-native/Executor status matrix.

## Non-goals

No reference JSON labeled as ASFP, fake generated success for gated devices, treating a fixed wait as reaching temperature, new unplanned compiler features or hardware execution claims.

## Acceptance

Run common acceptance and all current/new examples; compare effect order, types and source/IR/JSON outcomes. Gated examples must show expected diagnostic or produce their correctly labeled reference artifact. Verify deployment reports accompany review exports, companions reproduce and raw evidence/internal plans stay out of public downloads.

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

Version: none, this revision records a plan and changes no shipped code.

Implementation expectation: none, examples, tests and documentation only; production defects require a separately scoped fix.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
