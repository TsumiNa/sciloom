# First useful program

## Goal

Let a new reader install the checkout and generate a fixed-speed shaker package.

## Scope

Implement the first example in the [contract](00-overview.md), its companion,
reference-execution and artifact tests, public downloads, mypy and CI coverage.
Rewrite Getting started around that source. Record writing guidance in the
documentation contribution page and link this plan from the internal index.
The existing five-page tutorial remains coherent until PR2 replaces it.

## Non-goals

No shipped-code changes, tutorial reorder or new deployment claims.

## Acceptance

Run the example and compare its companion; check saved/applied speed and start
events. Run ruff, mypy, pytest for both packages and examples, AutoSuite smoke,
recipe validation, existing author/developer examples and proposed syntax checks.
Run strict site build, all website tests and git diff --check. Verify the rendered
Getting started page includes the actual source and matching downloads.

## Version

Version: none, documentation and a learning example only.
