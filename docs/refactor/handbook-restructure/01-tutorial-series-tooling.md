# Tutorial series tooling

## Goal

Make a multi-page tutorial series verifiable: the documentation tests execute
the steps cumulatively and prove that the last page's complete program is what
the steps build. Implements the [series contract](00-overview.md#series-contract).

## Scope

Add `website/tools/tutorials.py` with `Block`, `Series`, `blocks`, `program`,
`checkpoints`, `complete_program` and `same_program`, and its colocated
`website/tools/tutorials_test.py` covering: marker parsing (step; checkpoint with
and without code; unmarked fences ignored; a checkpoint without a `text` fence is
an error), `program` ordering, `same_program` accepting reordered imports and a
module docstring while rejecting a changed statement, and the `complete=None`
fallback.

In `website/tools/handbook_test.py`: add `SERIES = {}` (filled by PRs 4 and 9),
`test_tutorial_checkpoint` and `test_tutorial_series_is_the_complete_program`,
and generalise `test_walkthrough_includes_actual_source` from `examples/<slug>`
to a full page path so a tutorial page can be byte-checked against an example.
Existing tests are unchanged.

In `website/docs/developer/documentation.md`: a "Tutorial series" subsection that
shows the two markers and names the two tests.

## Non-goals

No page uses the markers yet. No change to what the first-fence and last-fence
tests execute. No new dependency.

## Acceptance

- `uv run ruff check`, `uv run ruff format --check`.
- `uv run --group docs pytest website/tools`: the new tests pass; with `SERIES`
  empty the two series tests are collected with no parameters.
- `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
