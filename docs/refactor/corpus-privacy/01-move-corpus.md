# Move the corpus out of git

## Goal

Implement the [split by origin](00-overview.md) so the working tree no longer
tracks vendor or instrument material.

## Scope

Untrack the vendor paths with `git rm --cached` and consolidate them on disk
under `autosuite/corpus/`. Replace the `autosuite/manual/` ignore rule with a
deny-by-default allowlist. Add `autosuite/README.md`, `.claude/settings.json`
deny rules and a pre-commit evidence check. Point the member tests, the smoke
check and the corpus audit at the new location; add `@requires_corpus` to the
tests that read evidence, through a new conftest in the member. Rewrite
`audit_corpus.py` for a corpus that grows: no fixed counts, per-section presence
guards, changed files fail and added or missing files are reported. Update the
paths and rules in AGENTS.md, `autosuite/docs/`, the device-abstraction overview,
the list example header and the public typing-and-tests page.

## Non-goals

No history rewrite; that is [its own operation](02-history-rewrite.md). No change
to compilation, IR or generated XML. No submodule, no corpus version pinning, no
change to which examples or pages exist.

## Acceptance

- `git check-ignore` reports `autosuite/corpus/**` and a stray `autosuite/*.app`
  as ignored, and the four tracked directories as not ignored.
- `uv run ruff check`, `ruff format --check`, `uv run mypy`,
  `uv run pytest src/sciloom packages/sciloom-autosuite/src examples`.
- With the corpus present: the full suite passes, and `smoke_test.py` and
  `audit_corpus.py` both report OK.
- With the corpus moved aside: the member suite passes with its evidence tests
  skipped, core and examples pass, and both tools report that they skipped.
- A staged file under `autosuite/corpus/` is refused by the pre-commit hook.
- `uv run --group docs python website/tools/site.py build --strict` and
  `uv run --group docs pytest website/tools`.
- No tracked file references the old `autosuite/app`, `asfp`, `archives`,
  `extracted`, `catalogs`, `manual`, `MANIFEST.csv`, `schema/type_templates` or
  `schema/golden_diffs` paths.

## Version

No bump: layout, ignore rules and tooling only; the merged state is
`0.1.0+<merge commit>`.
