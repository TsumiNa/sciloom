# Typing and tests

Run `uv sync --locked` followed by `uv run mypy`. CI checks Python 3.12, 3.13 and
3.14. Core and `sciloom_autosuite` functions have complete annotations, and
unannotated function bodies are checked. Both distributions carry py.typed; no
custom mypy plugin is needed.

What the type checker sees and what it cannot enforce is on
[typing without inheritance](advanced/typing-without-inheritance.md).

## Verification workflow

The full check list, the example commands and the pre-commit hook are on
[verification](reference/verification.md). Ruff enforces formatting, import
grouping and the ban on parent-relative imports: use single-dot relative imports
inside a package and absolute imports everywhere else.

Colocate tests as `<module>_test.py`. Production mypy traversal excludes these
intentional negative runtime fixtures; when adding test modules under src, also
maintain pyproject's explicit IDE override list. Positive and negative typing
fixtures verify the expected error behavior rather than merely running mypy.

API changes require exact imports, signatures, calls, results and extension examples
in the authoritative design document before implementation. Keep that contract
consistent across sequential PRs. Review, address feedback, pass latest checks and
squash merge before starting the next stage. See
[documentation development](documentation.md) for site-specific checks.
