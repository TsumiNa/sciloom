# Separate vocabulary from analysis

## Goal

Make the package tree match the architecture diagram: `flow` and `devices` are
what an author writes, `dsl` is the analysis, per the [contract](00-overview.md).

## Scope

Move the declaration modules into `sciloom/flow/` under the contract's names and
rename the analysis driver. Move their colocated tests. Update the lazy author
API, the mypy override list, the depth-sensitive path in a moved test, and the two
cross-package test imports. Replace the `dsl/__init__.py` docstring with the
phase description, the reading order and the reason it re-exports nothing. Record
the organisation rule in `AGENTS.md` and on the architecture page, and label the
diagram's first node with the two vocabularies.

## Non-goals

No logic change, no published API path change, no move of `sciloom.devices`, no
re-exports from `sciloom.dsl`.

## Acceptance

Shared acceptance. The import-isolation subprocess tests still pass, the API
reference still resolves every published path, and generated artifacts are
byte-identical to the parent commit.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
