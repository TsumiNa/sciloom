# Developer Guide relayout

## Goal

Move the Developer Guide pages into their groups without changing their content,
so the later content PRs are reviewable as content changes.

## Scope

`git mv`: `developer/architecture.md` → `developer/reference/architecture.md`,
`ir.md` → `reference/ir.md`, `interpreter.md` → `reference/interpreter.md`,
`compiler.md` → `reference/pipeline.md`, `contributions.md` → `reference/target-contract.md`.
Add a short `developer/index.md`. Regroup the nav in `website/mkdocs.yml`:
Overview; Tutorial (the three existing tutorials, unchanged); Reference; Project
(`typing-and-tests`, `documentation`, `publication`, `brand`).

Update every reference in the same PR: relative links inside the moved pages,
README (the developer handbook link), `docs/01_TARGET_ARCHITECTURE.md`,
`docs/02_COMPILER_ARCHITECTURE.md`, `docs/05_INSTANCE_SPECIALIZATION_AND_COMPILE_API.md`,
`docs/11_SEMANTIC_IR.md`, `docs/14_REFERENCE_EXECUTION.md`, `docs/INDEX.md`,
`docs/refactor/package-layout/04-responsibilities.md`, `website/docs/index.md`,
`website/docs/api/{index,compiler,devices,interpreter,ir-flow}.md`, and the four
slugs in the first-fence list of `website/tools/handbook_test.py`.

## Non-goals

No wording change; titles keep their current text (the pipeline page is retitled
in PR 8). `brand.md`, `publication.md`, `documentation.md` and
`typing-and-tests.md` keep their paths.

## Acceptance

- `grep -rn --exclude-dir=refactor --exclude-dir=.build "developer/\(architecture\|ir\|interpreter\|compiler\|contributions\)\.md" README.md docs website .github`
  returns nothing; `docs/refactor/` keeps the old paths as history.
- `uv run --group docs pytest website/tools`; `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`; `git diff -M --stat` shows the five files as renames.

## Version

`Version: none, documentation and test tooling`.
