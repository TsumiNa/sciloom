# Stage 9: Formatted wall time

## Goal

Implement A12 as an explicit, ordered clock read.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add the contract's now_text format subset, one read per call and a controllable wall-clock environment service. Map to observed native DateTime and document platform-local versus configured reference time.

## Non-goals

No datetime values, locale/timezone formatting, unique filename guarantee or implicit host clock.

## Acceptance

Test exact fixed-clock text, format validation, separate reads across clock changes, missing service and monotonic-clock independence. Compare native format evidence and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

