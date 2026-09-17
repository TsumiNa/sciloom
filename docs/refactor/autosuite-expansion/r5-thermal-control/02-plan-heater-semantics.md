# R5.2: Fixed heater configuration and lifecycle

## Goal

Fixed heater configuration and lifecycle while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R5.1 reviewed and remotely merged.
Current code status: implemented in this PR; review/merge pending. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Add Heater family properties and lifecycle contracts, author-to-IR lowering and reference state/events using R4. Require both temperature and ramp_rate explicitly. Provide source/IR/JSON warm-sample examples and mixed heater/shaker logical programs.

Protect the new built-in signatures in the core directory. Reuse generic R4
lowering/effects; add no heating-specific node or operation-name inference.
Reject thermal candidate selection in shared binding-use validation to retain
the fixed-only boundary, including subclasses; preserve existing agitation
selection semantics. Contributor examples remain explicitly reference-only.

## Non-goals

No getters, wait-to-temperature, implicit start/stop, physical simulation or unsupported AutoSuite profile acceptance.

## Acceptance

Test incomplete/branch-dependent configuration, configuration changes while running, explicit reapply, stop retention, shared/cross-call state and separation from shaker properties. Confirm fixed wait only advances explicit virtual time and never claims measured temperature. Native-unavailable commands remain rejected.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

Implemented Heater with two write-only typed properties and explicit lifecycle
contracts. Existing generic lowering/configuration/reference effects handle it;
there is no new heating-specific node or state engine. Built-in IDs and
requirements reject forged redefinitions. Shared binding-use validation rejects
thermal candidate selection, including subclasses, while existing agitation
selection remains available.

Executable `examples/warm_sample.py` reports the native gate;
`examples/developer/warm_sample_ir.py/.json` provides a minimal trusted fixed
contributor/recording target and direct IR matching the author's reference effects.
Tests cover typed capture, both missing properties, branch/zero-loop proof,
shared and independent children, repeated calls/reapply, immutable snapshots,
stop retention, explicit clock/failure order, profile extension, mixed shaker
state and physical-identity collisions. No native behavior is claimed.

Acceptance: 1297 code/tool/example tests, 98 website tests, 52 example/syntax
commands; Ruff check/format (312 files), mypy (141 files), strict documentation,
smoke and recipe validation passed. Existing ASFP/JSON companions are unchanged.
Corpus audit remained 271 files / 127 archive entries / 52 function matches /
67 templates. Public docs also correct the remaining stale R4 statement that
distinct actuators must have distinct zone names. No raw corpus was modified.

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: MINOR 0.8.0 → 0.9.0, adds the public fixed Heater family and typed
reference lifecycle semantics; both packages remain lockstep. No native profile
unlock, tag or publication.
