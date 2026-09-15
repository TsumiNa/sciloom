# Stage 5: Explicit reference environment

## Goal

Introduce environment injection and ordered external-event infrastructure.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add ReferenceEnvironment to Interpreter as the optional environment keyword. Retain old constructor behavior, result fields and DeviceEvents. Establish service ownership, missing-service errors, isolated defaults and immutable event snapshots. Add each concrete service with its owning subsequent feature instead of exposing empty future APIs.

## Non-goals

No implicit host I/O, real sleeping, real-clock default, automatic acknowledgement, runtime hardware client or generic event plugin.

## Acceptance

Run all old reference examples unchanged; test environment/session isolation and explicit sharing, missing-service diagnostics, event order and historical snapshot immutability. Check core layering and shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

