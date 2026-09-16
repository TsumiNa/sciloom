# Stage 13: Runtime Zone values

## Goal

Implement the A03 value layer and a read-only layout without dynamic device actions.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add a distinct Zone type/literal, opaque well identities, ordered uniqueness, scalar fields/calls, find/combine/well_name/len, fixed reference directory and AutoSuiteLayout.from_app. Parse only verified zone/well/device relationships and enumeration order from gzip APP. Existing fixed profiles continue to compile unchanged.

## Non-goals

No list[Zone], device object as value, implicit truthiness, task/app compiler, source-corpus changes or dynamic Stir emission yet.

## Acceptance

Test empty/unknown names, duplicate-combine order, well identity versus index, function passing, JSON, invalid single-well queries and layout ancestry. Corpus comparisons skip without corpus; synthetic structural tests always run. Reject unsupported target cases explicitly and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

