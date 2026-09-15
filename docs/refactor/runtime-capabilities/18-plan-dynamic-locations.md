# Stage 16: Runtime device locations

## Goal

Complete A03 through explicit selection scopes and trusted candidates.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Implement at, immutable common-contract candidate profiles, data-only selection bindings and APP-based allowed-well/controller checks. Extend scope/configuration analysis, specialized traversal, inherited shared-device context and backend private parameters. Track saved logical config separately from applied/enabled physical state; add physical result snapshots.

## Non-goals

No arbitrary unbounded hardware selection, overlapping logical candidate sets, implicit stop/restore, same-device nested selection or model-bound hardware objects.

## Acceptance

Test fixed bindings unchanged; missing/wrong/duplicate candidates; empty, outside and multicontroller zones; value capture; scope inheritance and same-device nesting. Test A-to-B selection leaving A running, stops per controller, cross-function configuration and immutable physical snapshots. Prove runtime rejection before body effects; run shared checks and record Executor status.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

