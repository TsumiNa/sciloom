# Stage 12: Bounded CSV append

## Goal

Implement A06 one-row logging.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add append/try_append author operations, ordered typed values and status, reference file writes and the observed AutoSuite one-text-column mode. Preserve file ownership and explicit failure behavior.

## Non-goals

No overwrite/change-cell, header generation, retries, directory creation, multirow arrays or unverified target column combinations.

## Acceptance

Test repeated writes and new-file creation, capture once, IO_ERROR versus ordinary fatal failure and no fictional rollback. Probe exact quoting/encoding/line endings separately from logical row equality; preserve old fixtures and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

