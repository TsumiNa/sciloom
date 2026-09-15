# Stage 11: Typed CSV reads

## Goal

Implement A05 row and column reads with explicit results and failure policy.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Implement Column metadata, runtime selectors/default capture, read/try-read forms, fixed tuple bindings and named statuses. Add typed read IR, in-memory files and opt-in local adapter, parsing/type/unit checks, atomic result-field commit and bounded AutoSuite generation. Record parser profiles and gate needed failure checks.

## Non-goals

No header-to-variable lookup, implicit field creation, DataFrame, arbitrary slicing, implicit array growth, filesystem transaction or Python evaluation of cells.

## Acceptance

Test headers/zero-based selectors, single/multiple columns, empty data, missing rows/cells/files, invalid types/defaults, volume units, output isolation and snapshot copies. Check mixed column policies rather than trusting aggregate vendor codes. Reproduce F28's bounded recipe path; validate evidence matrix and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit
series-level version decision. Choose the next patch after final review;
documentation/example/tooling-only changes use none. JSON remains v4. No release
tag or PyPI publication.

