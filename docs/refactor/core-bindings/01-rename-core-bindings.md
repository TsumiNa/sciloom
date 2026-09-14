# Rename the module and its references

## Goal

Land the [rename](00-overview.md) as one mechanical change that leaves every
check green.

## Scope

`git mv` `src/sciloom/core/devices.py` and its colocated test to `bindings.py`
and `bindings_test.py`. Rewrite every import: the relative imports inside
`sciloom.core`, the absolute imports in `sciloom.devices.declarations`, the test
fixtures, the AutoSuite member, the developer examples and the executed snippets
in the public tutorials. Point the three API directives in `api/compiler.md` at
the new path. Rename the row in the public architecture table and, while in that
table, add the `sciloom.core.configuration` row it had omitted. Update the one
sentence in AGENTS.md §10 and mark the old row in the device-abstraction plan as
superseded.

## Non-goals

No change to any class, function, signature, IR node or generated artifact. No
alias at the old path. Historical plans under `docs/refactor/` keep their code
examples as written.

## Acceptance

- No file under `src/`, `packages/`, `examples/`, `website/`, `.github/` or the
  root Markdown files mentions `sciloom.core.devices` or `core/devices`.
- `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`,
  `uv run pytest src/sciloom packages/sciloom-autosuite/src examples`.
- The developer examples run and leave the tree clean; the generated example
  companions are byte-identical.
- `uv run --group docs python website/tools/site.py build --strict` and
  `uv run --group docs pytest website/tools`; the rendered `api/compiler/` page
  carries the anchor `sciloom.core.bindings.DeviceBindings`.

## Version

No bump: a rename of an unreleased contributor import path; the merged state is
`0.1.0+d937864`.
