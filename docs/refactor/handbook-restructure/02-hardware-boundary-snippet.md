# Hardware boundary snippet

## Goal

State once that compilation and reference execution are not hardware
acceptance. Today the sentence "Compilation and reference execution do not
operate hardware or replace AutoSuite Executor checks" is pasted on all eight
example pages and reworded on seven others.

## Scope

Add `website/snippets/hardware-boundary.md`: one `!!! note` admonition, no links
(a shared snippet cannot carry relative links, because it is included at
different depths). Move the "What validation establishes" paragraph of
`website/docs/user-guide/compilation.md` to `website/docs/introduction/status.md`
under `## What compilation establishes`, and replace it on the compilation page
with the include plus a link to that section. Replace the pasted sentence on the
eight `website/docs/examples/*.md` pages with `--8<-- "website/snippets/hardware-boundary.md"`.

## Non-goals

No change to `index.md`, `getting-started.md`, README or example module
docstrings, where the boundary is one sentence in flowing prose. No new pages.

## Acceptance

- `grep -rn "do not operate hardware" website/docs` returns nothing.
- `uv run --group docs python website/tools/site.py build --strict`; the
  rendered example pages show the admonition.
- `uv run --group docs pytest website/tools` (the walkthrough byte-checks still
  pass).
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
