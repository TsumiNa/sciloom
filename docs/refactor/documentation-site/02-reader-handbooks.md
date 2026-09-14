# Reader handbooks

Historical stage record. The User Guide and Developer Guide it produced are
superseded by the [example-led handbooks plan](../handbook-restructure/00-overview.md).

## Goal

Explain current SciLoom behavior to experiment authors and contributors.

## Scope

Follow the [authoritative contract](00-overview.md). Complete introduction,
installation/quick start, user and developer guides, and eight example walkthroughs.
Include actual source and committed outputs. Explain restricted Python, state/list
copy semantics, device configuration/lifecycle, bindings, specialization, IR v4,
reference execution and independent contributions. Update Mermaid architecture
diagrams. Replace superseded current-guide text with pointers, preserving history.
Keep publicly unavailable installation and future capabilities labelled accurately.

## Non-goals

No raw corpus publication, new experiment semantics, full API docstring work or
Pages deployment. Do not turn proposed frontend examples into supported tutorials.

## Acceptance

Strict-build all pages and verify links/downloads/diagrams. Run each referenced
example and check its described result. Ensure author pages do not require IR
knowledge. Run existing checks and git diff --check; inspect desktop/mobile pages.
Review and squash merge before stage 3 begins.

## Implementation evidence

English introduction, six author chapters, contributor architecture/IR/compiler/
interpreter/extension/typing chapters and eight source-backed walkthroughs are
implemented. Six complete handbook snippets execute in tests; eight render checks
compare included example source with the real files. Existing numbered current
guides point to the handbook; broader historical proposals retain explicit status.
Local acceptance: 342 tests, mypy (63 files), smoke, recipe, eight examples,
proposed syntax, strict documentation build and diff checks pass.
