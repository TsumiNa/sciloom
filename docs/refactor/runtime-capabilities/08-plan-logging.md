# Stage 6: Typed runtime logging

## Goal

Implement A09 as an ordered operation.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Author log call, typed IR statement, runtime scalar/quantity capture, ordered reference event and observed AutoSuite LogData task. Include category and stream expressions. Add author/developer documentation for values already supported.

## Non-goals

No telemetry, list/Zone/object formatting or application logging setup.

## Acceptance

Assert captured value/type/category/stream, source and event ordering against adjacent assignments. Compare native task shape with source evidence; distinguish logs from physical readings. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

