# Typing and tests

Run `uv sync --locked` followed by `uv run mypy`. CI checks Python 3.12, 3.13 and
3.14. Core/contrib functions have complete annotations, and unannotated function
bodies are checked. The package carries py.typed; no custom mypy plugin is needed.

Input/Output/Var are Annotated aliases. Mypy sees the Python value type, while
SciLoom reads role metadata. Wrong scalar/list assignments and invalid device
property types are caught statically. Runtime and operation decorators preserve
signatures; is_device uses TypeGuard to narrow compatible device interfaces.

Mypy does not enforce host-time field protection, role nesting, mandatory Var
initializers, every Function call binding, the source subset or vendor constraints.
Python's bool/int subtype relationship also differs from SciLoom's index rules.
Schema, IR and target validation remain necessary.

## Verification workflow

```bash
uv run ruff check
uv run ruff format --check
uv run pytest src/sciloom examples
uv run mypy
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
```

Ruff enforces formatting, import grouping and the ban on parent-relative imports.
Use single-dot relative imports inside a package and absolute imports everywhere
else. Enable the repository pre-commit hook once per clone with
`git config core.hooksPath .githooks`; it fixes and formats staged Python files
before each commit.

The AutoSuite commands use retained internal reference material in a source
checkout; that corpus is not distributed by the public documentation site.
Run all eight current examples using commands on their walkthrough pages. Proposed
frontend examples are syntax-checked design material, not runnable supported APIs.

Colocate tests as `<module>_test.py`. Production mypy traversal excludes these
intentional negative runtime fixtures; when adding test modules under src, also
maintain pyproject's explicit IDE override list. Positive and negative typing
fixtures verify the expected error behavior rather than merely running mypy.

API changes require exact imports, signatures, calls, results and extension examples
in the authoritative design document before implementation. Keep that contract
consistent across sequential PRs. Review, address feedback, pass latest checks and
squash merge before starting the next stage. See
[documentation development](documentation.md) for site-specific checks.

Raw AutoSuite evidence is never rewritten to make generated code pass. Static
structure tests, reference execution, Executor simulation and physical validation
are separate forms of evidence.
