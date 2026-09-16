# Stage 17: Complete runtime workflows

## Goal

Verify the twelve additions together and teach the supported scope.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add recipe-table, selected-shaker and per-well-label/time/CSV workflows plus the pure aspiration-chunk calculation. Pair author examples with direct IR/JSON/reference examples. Publish selected sources and same-basename outputs, update API/manual/status/Q&A and demonstrate independent Target support/rejection.

## Non-goals

No actual liquid-transfer driver, unverifiable hardware recipe, new release tag or public raw corpus.

## Acceptance

Run every new source independently, compare committed companions, Python/direct IR/JSON outputs, old v4 baselines and meaningful failure cases. Build the site, check API/search/downloads and absence of internal evidence. Separate reference/static/platform acceptance and run all shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: none, this stage adds examples, documentation and verification rather
than shipped implementation. Both packages retain the same current 0.3.x
version; JSON remains v4. No release tag or PyPI publication.
