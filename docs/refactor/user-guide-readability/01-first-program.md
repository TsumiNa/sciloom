# First useful program

## Goal

Let a new reader install the checkout and generate a fixed-speed shaker package.

## Scope

Implement the first example in the [contract](00-overview.md), its companion,
reference-execution and artifact tests, public downloads, mypy and CI coverage.
Rewrite Getting started around that source. Record writing guidance in the
documentation contribution page and link this plan from the internal index.
The existing five-page tutorial remains coherent until PR2 replaces it.

## Non-goals

No shipped-code changes, tutorial reorder or new deployment claims.

## Acceptance

Run the example and compare its companion; check saved/applied speed and start
events. Run ruff, mypy, pytest for both packages and examples, AutoSuite smoke,
recipe validation, existing author/developer examples and proposed syntax checks.
Run strict site build, all website tests and git diff --check. Verify the rendered
Getting started page includes the actual source and matching downloads.

## Commands

Run from the repository root:

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest src/sciloom packages/sciloom-autosuite/src examples
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
uv run python examples/function_call.py
uv run python examples/agitation.py
uv run python examples/scale_values.py
uv run python examples/non_zero_array_min.py
uv run python examples/stir_rack.py
uv run python examples/tutorial/start_shaker.py
uv run python -m examples.developer.agitation_ir
uv run python -m examples.developer.list_ir
uv run python -m examples.developer.demo_device
uv run python -m examples.developer.portable_agitation
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
git diff --check
```

After example generation, inspect `git diff` for unexpected companion changes.

## Version

Version: none, documentation and a learning example only.
