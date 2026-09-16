# Stage 5: Explicit reference environment

## Goal

Introduce environment injection and ordered external-event infrastructure.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Before production edits, extend that contract with concrete file, clock,
location-directory, property-store and acknowledgement service constructor/method
signatures, ownership, missing-service diagnostics and usage examples. Those
service interfaces are not specified in stage 0; this is a required first task
of stage 5, and its review must check the later consuming stages against them.
Add ReferenceEnvironment to Interpreter as the optional environment keyword. Retain old constructor behavior, result fields and DeviceEvents. Establish service ownership, missing-service errors, isolated defaults and immutable event snapshots. Add each concrete service with its owning subsequent feature instead of exposing empty future APIs.

## Non-goals

No implicit host I/O, real sleeping, real-clock default, automatic acknowledgement, runtime hardware client or generic event plugin.

## Acceptance

Run all old reference examples unchanged; test environment/session isolation and explicit sharing, missing-service diagnostics, event order and historical snapshot immutability. Check core layering and shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation

The authority now gives exact service signatures, module/import paths, ownership,
error boundaries and stage availability for files, clocks, acknowledgement,
locations and well properties. They are design contracts, not placeholder
implementations. Concrete services still arrive in their consuming stages.

`ReferenceEnvironment` owns an append-only event history; its public `events`
property returns a tuple snapshot. `Interpreter(..., environment=...)` retains
the supplied instance or creates a fresh one. A session records each completed
device event both in its per-run result and in the environment history. A failure
does not remove already completed events. Shared environments do not merge
Function variables or logical-device state.

`ExecutionEvent` is currently the existing DeviceEvent type, ready for closed
union additions with individual capabilities. The private `_require_service`
helper provides `missing_environment_service` diagnostics with the requesting
node/source; service consumers will call it as their features land. No service
registry, host I/O or automatic confirmation is introduced.

The complete `examples/developer/reference_environment.py` demonstrates two
sessions with shared history and independent device snapshots. Its short actual
output is in the module docstring. Environment tests cover fresh defaults,
explicit identity sharing, event ordering, failure retention, immutable prior
snapshots and missing-service diagnostic metadata.

Acceptance passed: 503 code/example tests, 80 website tests (including strict
rendering, source inclusion and API extraction), mypy over 75 source files,
Ruff checks/formatting, AutoSuite smoke, recipe validation, all 18 CI
example/syntax commands and `git diff --check`. Rebuilding after clearing the
ignored website cache removed an older snippet rendering; no source or generated
companion needed changing. Existing v4 fixtures and ASFP companions are unchanged.

## Version

Version: PATCH 0.3.3 → 0.3.4, adding explicit reference-environment ownership and
event history under the user's lockstep 0.3.x decision. JSON stays v4.
