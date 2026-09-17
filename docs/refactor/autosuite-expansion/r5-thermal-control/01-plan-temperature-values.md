# R5.1: Typed absolute temperature and rates

## Goal

Typed absolute temperature and rates while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R4.2 merged; R5.3 additionally needs exact profile and conversion evidence or must remain gated.
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

Implement Temperature, TemperatureDifference and TemperatureRate, canonical units and the bounded arithmetic matrix in the contract. Extend scalar/list value handling, author conversion, expression checks, JSON, snapshots and diagnostics. Every target consumer supports the exact type or rejects it explicitly.

## Non-goals

No vendor-specific SI offset, mass/pressure, generic dimensional algebra or native thermal profile.

## Acceptance

Test 0°C/20°C/negative Celsius, zero kelvin boundary, nonfinite/bool rejection, affine difference arithmetic, invalid absolute addition/scaling, rate/difference comparison, runtime Input/Output/Var and homogeneous lists, JSON parity and old byte baselines. Use expected numerical conventions rather than exact physical equivalence.

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

Implementation expectation: MINOR, adds temperature value types and operations.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
