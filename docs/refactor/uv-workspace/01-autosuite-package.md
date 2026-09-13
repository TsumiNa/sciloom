# Move AutoSuite into the `sciloom-autosuite` workspace member

## Goal

Implement the [workspace contract](00-overview.md): `sciloom.contrib.autosuite`
becomes the distribution `sciloom-autosuite`, imported as `sciloom_autosuite`.

## Scope

Declare the workspace and the member: `packages/sciloom-autosuite/pyproject.toml`,
`py.typed`, the workspace source, the `dev` group entry, ruff `src`, mypy
`files`, `mypy_path` and overrides. `git mv` the package and delete
`src/sciloom/contrib/__init__.py`. Rename every `sciloom.contrib.autosuite`
reference and the `"sciloom.contrib"` import-guard prefixes in examples, core
tests and the member's tests; add a comment above each corpus path constant in
the member tests. Regenerate `uv.lock`. Extend the CI pytest path, `.gitignore`,
the mkdocs search paths, the API page directives, `website/tools/api_test.py`
(second search path, per-package resolution) and the publication fixture copy
list. Update the public pages listed in the overview, README, AGENTS.md §8-§10
and `docs/01_TARGET_ARCHITECTURE.md`. Mark every current-contract statement of
the `sciloom.contrib` namespace in earlier plans superseded with a pointer to
this plan: the ownership row and the author-API import in
`docs/refactor/package-layout/00-overview.md`, the ownership row in
`docs/refactor/dsl-layering/00-overview.md`, and the ownership row, the
"installation into the sciloom.contrib namespace" sentence and the import
example in `docs/refactor/device-abstraction/00-overview.md`. Stage files and
stage tables stay as history.

## Non-goals

No runtime, IR, XML or public class-name changes; no compatibility alias for
`sciloom.contrib`; no lockstep enforcement (PR2); no test decoupling (PR3); no
corpus move; no extra.

## Acceptance

- `uv lock && uv lock --check`; after `uv sync --locked`,
  `import sciloom_autosuite` resolves under `packages/sciloom-autosuite/src`, and
  the import fails after `uv sync --locked --no-dev` (re-sync afterwards).
- `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`,
  `uv run pytest src/sciloom packages/sciloom-autosuite/src examples`, the
  AutoSuite smoke and recipe checks, `compileall examples/proposed_frontend`, all
  eight examples and `uv run python autosuite/tools/audit_corpus.py`.
- `uv sync --locked --group docs`, the strict site build and
  `uv run --group docs pytest website/tools`; the docs preview artifact shows
  `id="sciloom_autosuite.AutoSuiteTarget"` anchors and the new import in
  getting-started.
- `uv build --package sciloom-autosuite` produces a wheel containing `py.typed`;
  delete the artifacts afterwards.
- A search for `sciloom.contrib` over `src`, `packages`, `examples`, `website`,
  `AGENTS.md`, `README.md`, `.github` and `pyproject.toml` finds nothing, and over
  `docs/refactor/*/00-overview.md` finds it only on lines that carry a superseded
  note pointing to this plan (stage files keep their historical text); example
  companion files are byte-identical; `git diff --check` and `git diff --exit-code`
  pass after all builds and example runs.
- After merge, `https://tsumina.github.io/sciloom/dev/` shows the new import path.

## Version

No bump: `0.1.0` has never been tagged, so the import-path change breaks no
released contract. Both members stay at `0.1.0`; the merged state is
`0.1.0+<merge commit>`.
