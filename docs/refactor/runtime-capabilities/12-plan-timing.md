# Stage 10: Wait and timer

## Goal

Implement A08's monotonic duration semantics.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Declare Function-owned Timer resources, start/reset and wait_until; add ordinary wait. Extend the resource union without changing existing device fields. Perform definite-start analysis across branches/calls with no historical-entry assumption. Reference waiting advances a virtual clock; target maps observed waitmode 0/2 and SetTimer.

## Non-goals

No Timer sharing across Functions, contacts, physical setpoints, automatic stop or real sleeping.

## Acceptance

Test five-second composed example, already elapsed target, reset, negative durations, zero-iteration branches and use-before-start. Confirm waits leave device state intact and child time counts. Compare timer scope/native payload evidence; run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

