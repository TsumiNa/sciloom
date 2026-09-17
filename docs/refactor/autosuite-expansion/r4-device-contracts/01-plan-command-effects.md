# R4.1: Explicit lifecycle command contracts

## Goal

Explicit lifecycle command contracts while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r4-explicit-command-effects-and-typed-configuration).
R3 implementation PRs merged or completed as implemented/gated. Recheck that R5's planned concrete thermal needs justify each abstraction.
Current code status: implemented; merged #109. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Add the lifecycle command-contract variant and decorator options; preserve ordinary command contracts and dedicated agitation nodes. Resolve property requirements, validate inherited/conflicting contracts, analyze definite configuration through branches/calls/loops and execute trusted logical lifecycle effects. Add the independent contributor example from the contract.

Per D014, the two initial lifecycle effects accept no command arguments; reject
nonempty parameters at declaration and IR validation. Ordinary typed commands
are unchanged. The concrete contributor profile explicitly declares its required
configuration, as the existing binding API requires.

## Non-goals

No method-name inference, dynamic code import, schema migration, arbitrary result values, general plugin registry or unknown command simulation.

## Acceptance

Prove unchanged old JSON bytes; new variant round trips; incomplete/conditional config rejection; apply snapshots; disable retains state; JSON trusted-contract mismatch rejection; ancestor consistency; child/shared resource behavior. Unknown ordinary commands remain rejected. Explicitly handle/reject the variant in every consumer.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Implementation and local acceptance

Added LifecycleEffect/LifecycleCommandContract to the existing typed schema and
operation decorator; the old ordinary command and agitation records are unchanged.
Requirements resolve to declared property IDs and are checked for writability,
definite initialization across calls/branches/loops, and again at reference action
time. Reference effects preserve immutable logical/physical snapshots; unknown
ordinary commands still reject. Supplied trusted contracts reject forged effects
and inconsistent ancestry. AutoSuite validation and emission explicitly reject
new lifecycle commands; no native profile is claimed.

The complete lifecycle_commands contributor example and JSON companion exercise
capture, reapply and disable using an independent recording target. Tests cover
missing/conditional configuration, shared and distinct child resources, loops,
repeated entry state, explicit disable preconditions, malformed declarations/IR,
specialization, unknown commands and no later actions after failure. Existing
v4 fixture bytes and old ASFP companions remain unchanged.

Local acceptance: full code/example/tool suite, 98 website tooling checks,
48 CI example/syntax commands, Ruff check/format, mypy (138 source files), strict
documentation build, smoke and recipe validation passed. Read-only corpus audit:
271 files, 127 archive entries, 52 function XML matches, 67 templates. Native
execution remains unverified. Review and latest-head CI are still required.

## Review and completion

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: MINOR 0.6.0 → 0.7.0, adds explicit typed lifecycle contracts and contributor
declarations with defined reference effects. Both packages remain lockstep; no
release tag or publication. Reassess after review changes.
