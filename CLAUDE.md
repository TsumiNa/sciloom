# CLAUDE.md

Claude Code entry point for this repository.

## Read this first

[`AGENTS.md`](AGENTS.md) is the authoritative instruction file for this package.
Read it in full before starting work. This file only routes to it; it does not
restate or override it. If the two ever disagree, `AGENTS.md` wins.

`AGENTS.md` covers:

| Topic | Section |
| --- | --- |
| Architecture invariants (Semantic IR, class-level schema, compile unit) | §1 |
| Evidence hierarchy when facts conflict | §2 |
| Evidence files must not be mutated silently | §3 |
| Python frontend rules | §4 |
| Error model (fatal by default) | §5 |
| Validation layers | §6 |
| Required reading before touching serialization | §7 |
| Tests to run | §8 |
| Documentation location rules | §9 |

## Repository instruction files

Per `AGENTS.md` §"Additional repository instructions", the files under
[`.github/instructions/`](.github/instructions/) are **required repository
rules**, not reference material. Claude Code does not load them automatically —
read the applicable ones yourself, using each file's `applyTo` and `description`
to decide scope, and recheck when the task expands to new files or activities.

- [`shell-environment.instructions.md`](.github/instructions/shell-environment.instructions.md) — read **before any terminal command**. The default shell here is `fish`: no POSIX heredocs; prefer the Write/Edit tools over shell redirection for file content.
- [`branch-and-pr-workflow.instructions.md`](.github/instructions/branch-and-pr-workflow.instructions.md) — read **before editing files**; decides branch vs. PR vs. current branch.
- [`implementation-and-tests.instructions.md`](.github/instructions/implementation-and-tests.instructions.md) — minimal abstraction, no scope expansion, `@dataclass` config objects, type hints, colocated `<source>_test.py` tests.
- [`repository-doc-boundaries.instructions.md`](.github/instructions/repository-doc-boundaries.instructions.md) — what belongs in `README.md` vs. `AGENTS.md` vs. `ARCHITECTURE.md`.
- [`python-imports.instructions.md`](.github/instructions/python-imports.instructions.md) — read **before writing or changing imports**; single-dot relative imports inside the current package, absolute imports for everything else, never `..`, grouped stdlib / third-party / local.

Explicit user instructions and system/developer instructions take precedence
over all of the above.

## Environment

- Package: `SciLoom`, source under [`src/sciloom/`](src/sciloom/), built with `uv_build`.
- Python `>=3.12,<3.15`; use `uv run ...` for project commands.
- Lint/format: `uv run ruff check` / `uv run ruff format` (line length 120). Enable the pre-commit hook once per clone: `git config core.hooksPath .githooks`.
- Types: `uv run mypy` (`check_untyped_defs = true`).
- Tests: `uv run pytest`, plus the AutoSuite checks listed in `AGENTS.md` §8.
