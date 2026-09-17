# R1.2: Enforce known deployment incompatibilities

## Goal

Enforce known deployment incompatibilities while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r1-deployment-conditions-and-review-artifacts).
R1.1 reviewed and remotely merged.
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

Connect the shared assessment to AutoSuiteTarget.validate after specialization; reject known incompatibility, retain unknown offline generation, and implement the checked ASFP-plus-report review exporter. Conservatively inventory internal Var and persistent configuration requirements. Add state-lifetime probes using existing manifest conventions, not a separate harness.

## Non-goals

No automatic APP change, variable promotion to global, new compiler entry point, liveness optimizer or unverified native persistence claim.

## Acceptance

Test compatible/incompatible/unknown outcomes, no requirements for genuinely stateless programs, unchanged core compile/write API and diagnostics with affected nodes. Test mismatched target/bindings/artifact rejected by review export, deterministic report/artifact digests and IO errors. Probe repeated entry, shared/distinct children, loop re-entry and restart under both reset settings; require actual host receipts before marking native verified.

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

Implementation expectation: MINOR, adds deployment-aware target validation and review export.
Before the implementation PR is reviewed, replace this planning-only decision
with the exact lockstep from/to transition based on its actual shipped scope and
then-current baseline. The user explicitly requested no preallocated future
version numbers. Reassess after review changes; no publication.
