# Verification

The checks a change must pass, in the order CI runs them, from the repository
root after `uv sync --locked`:

```bash
uv run ruff check
uv run ruff format --check
uv run pytest src/sciloom packages/sciloom-autosuite/src examples
uv run mypy
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
git diff --check
```

Then run every example; CI ends with `git diff --exit-code`, so each must leave
its committed companion files unchanged:

```bash
uv run python examples/function_call.py
uv run python examples/agitation.py
uv run python examples/scale_values.py
uv run python examples/non_zero_array_min.py
uv run python examples/stir_rack.py
uv run python -m examples.developer.agitation_ir
uv run python -m examples.developer.list_ir
uv run python -m examples.developer.demo_device
uv run python -m examples.developer.portable_agitation
```

Enable the repository pre-commit hook once per clone with
`git config core.hooksPath .githooks`; it fixes and formats staged Python files
before each commit and refuses partially staged files.

The AutoSuite commands use internal reference material that is shared inside the
team rather than through this repository, so a checkout may not have it. The
smoke and corpus checks skip their evidence sections when it is absent, and the
tests that compare generated XML against it skip themselves. Everything the
repository carries still runs. The proposed frontend examples are syntax-checked
design material, not runnable supported APIs.

Raw AutoSuite evidence is never rewritten to make generated code pass. Static
structure tests, reference execution, Executor simulation and physical validation
are separate forms of evidence; see
[what compilation establishes](../../introduction/status.md#what-compilation-establishes).
