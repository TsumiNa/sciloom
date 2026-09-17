# R7.1: Verify complete operator and equipment workflows

## Goal

Verify complete operator and equipment workflows while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r7-integrated-results).
R1–R6 implementation PRs merged; native unlocks only where evidence exists.
Current code status: implemented; review/merge is tracked by the stage PR. Native status follows the [group overview](00-overview.md)
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

D026 reuses the three existing manual IR builders and adds
`examples/mixed_equipment.py`, the source-derived `mixed_equipment_ir.py/.json`
companion and integration regressions. The public workflow page supplies exact
commands, effects and per-layer status; the [delivery audit](../07-delivery-audit.md)
maps all seven refactors to inspected evidence. Historical merged-status wording
is corrected using remote PR metadata, without changing native pending states.

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

## Local acceptance (2026-09-18)

14 new integration tests pass. Full source/target/examples/tools suite: 1463
passed; website tooling: 98 passed. All 59 current CI example/syntax commands
pass, including three required paired workflows, mixed source/JSON and deployment
review export. Existing generated companions are unchanged. New mixed companion
reproduces with repository-relative paths; reference JSON cannot be exported as
ASFP. Ruff check/format (329 files), mypy (146 sources), strict documentation
build, smoke and recipe checks pass. Read-only corpus audit: 271 files, 127
archive entries, 52 function matches, 67 templates. 187 relative plan links,
16 Python contract snippets and 18 plan structures pass. Remote metadata confirms
all predecessor PRs #103–#116 merged.

No native receipt/Executor result is added; the audit explicitly retains
unverified/incomplete native acceptance and conditional unlock work. R7's own
review, latest-head CI and remote merge are recorded by its PR, not inferred
from these local results.

## Version

Version: none, examples, integration tests, public learning documentation and
internal delivery records only. Shipped APIs are unchanged; both packages remain
0.11.0. No release tag or package publication.
