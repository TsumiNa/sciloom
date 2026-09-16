# Stage 12: Bounded CSV append

## Goal

Implement A06 one-row logging.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add append/try_append author operations, ordered typed values and status, reference file writes and the observed AutoSuite one-text-column mode. Preserve file ownership and explicit failure behavior.

## Non-goals

No overwrite/change-cell, header generation, retries, directory creation, multirow arrays or unverified target column combinations.

## Implementation decisions

The [concrete append contract](01-contract.md#stage-12-concrete-append-contract)
defines records, byte profile and failure classification before implementation.
The audit does not establish the exportbehaviour=0 enum label. Preserve the
observed task as isolated native measurement probes and gate public compilation
until append/new-file behavior and required error propagation are verified.

## Acceptance

Test repeated writes and new-file creation, capture once, IO_ERROR versus ordinary fatal failure and no fictional rollback. Probe exact quoting/encoding/line endings separately from logical row equality; preserve old fixtures and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implemented verification

AppendCsv has source lowering, stable JSON v4 encoding, typed validation, consumer
coverage and explicit reference file effects. Repeated writes, capture before
status assignment, child/loop use, read-back, immutable snapshots, failures before
I/O and partial-write preservation are covered. The author and direct-IR/JSON
examples agree. Six native Export CSV probes remain pending, with evidence and
host procedure in reference document 28. No target path assumes mode 0 is append.

Local acceptance: 761 code/example/tool tests, 89 website tests, mypy (104 source
files), Ruff, 30 example/syntax commands, strict site, AutoSuite smoke, recipe
validation, corpus audit and diff whitespace checks. Existing v4 fixtures and
old example artifacts remain unchanged. Executor results are not available.

## Version

Version: PATCH 0.3.10 → 0.3.11 in both workspace packages, adding CSV row append
within the user's explicitly requested 0.3.x series. JSON remains v4 and old
artifacts remain unchanged. No release tag or PyPI publication.
