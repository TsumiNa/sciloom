# Stage 15: Stored well metadata

## Goal

Implement A07 user text-property reads and writes.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add host WellProperty descriptor, indexed write and get with explicit optional default. Preserve high-level ordered read/write nodes, per-well reference storage and observed Get/SetProperty task mapping.

## Non-goals

No measured/configuration getter, readonly native telemetry, per-well arrays or arbitrary property types.

## Acceptance

Test single-well strict read, missing/wrong-type default behavior, empty/multiwell writes, captured values and well/session isolation. Check error guarding and native property names/default fields against evidence. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

