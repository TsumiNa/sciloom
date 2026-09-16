# Stage 14: Sequential Zone traversal

## Goal

Implement A04 indexing and well/fragment iteration.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add typed index and structured foreach nodes; lower ordinary for to a declared Var[Zone] target. Capture the iterable once, check size/divisibility, preserve zero-iteration semantics and map verified sequential macros. Use already available body operations in this stage's examples.

## Non-goals

No undeclared loop state, partial final fragment, coordinated multizone/batch, break/continue/for-else or ahead-of-stage well-property API.

## Acceptance

The [concrete traversal contract](01-contract.md#stage-14-concrete-traversal-contract)
records exact ZoneGet/ForEachZone structure, loop target persistence, captured
selection, nested loops and the initial AutoSuite support boundary. Dynamic
index and grouped-divisibility checks remain gated by verified fatal propagation.

Test empty/single/multiple wells, bounds/bool/negative indices, positive static size and divisibility before effects. Check traversal order and fragment position distinct from loop counter, plus all consumers/specialization. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and verification

Implemented: ZoneGet/ForEachZone additive v4 records, typed host Zone indexing
and iteration, source-only fragment markers, declared Var targets, captured
reference iteration, explicit consumer handling and size-one AutoSuite sequential
macros. The macro uses private captured/iterator Zones plus an outer empty guard;
larger groups and index emission remain explicit platform gates.

Python, direct IR and JSON checks cover empty selections, ordering, grouping,
target persistence, source/target mutations, child output writes, nested loops,
type/bounds failures and step limits. Configuration, timer and output analyses
retain zero-iteration behavior. Exhaustiveness mutation tests now also remove
Zone handlers. The author and developer examples include generated companions.

The [evidence note](../../../autosuite/docs/30_ZONE_TRAVERSAL_MAPPING.md) separates
static mapping from pending Executor results. RC-QA-014 collects remaining
capture/scope/empty-selection questions. No corpus file is modified.

Local acceptance: 861 code/example/tool tests, 92 documentation tests, mypy
(112 source files), Ruff (244 files), strict website build, 34 example commands,
AutoSuite smoke, recipe validation, proposed-source syntax and diff checks pass.
Corpus audit passes without writes. Previous example companions and v4 fixtures
are unchanged. Review and exact-head CI remain the merge gate.

## Version

Version: PATCH 0.3.12 → 0.3.13, adding Zone traversal within the user's explicitly
approved lockstep 0.3.x series. JSON remains v4 and old canonical artifacts stay
unchanged. No release tag or PyPI publication.
