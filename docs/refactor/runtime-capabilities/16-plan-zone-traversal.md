# Stage 14: Sequential Zone traversal

## Goal

Implement A04 indexing and well/fragment iteration.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add typed index and structured foreach nodes; lower ordinary for to a declared Var[Zone] target. Capture the iterable once, check size/divisibility, preserve zero-iteration semantics and map verified sequential macros. Use already available body operations in this stage's examples.

## Non-goals

No undeclared loop state, partial final fragment, coordinated multizone/batch, break/continue/for-else or ahead-of-stage well-property API.

## Acceptance

Test empty/single/multiple wells, bounds/bool/negative indices, positive static size and divisibility before effects. Check traversal order and fragment position distinct from loop counter, plus all consumers/specialization. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

