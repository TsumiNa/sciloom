# Practical advanced guides and walkthroughs

## Goal

Explain common author tasks using the [writing contract](00-overview.md).

## Scope

Rewrite the four Advanced pages and five author example walkthroughs. Keep
complete runnable code, but move deliberate failures into troubleshooting and
retain execution checks. Explain copying and configuration through their effects.
Shorten agitation's module docstring by removing the long XML excerpt; preserve
the ASFP companion and existing example behaviour. Regenerate the developer JSON
companion's source spans when shortening the docstring moves the method's lines;
only diagnostic positions change, not the semantic nodes or ASFP.

## Non-goals

No broad Developer Guide rewrite, API or compiler changes.

## Acceptance

Run PR1's full checks. Execute revised snippets and relocated error cases, check
source/download agreement and compare existing ASFP companions unchanged; inspect
any regenerated developer JSON for source-position-only changes.
Read the rendered pages for an identifiable task, editable values and result.

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
uv run python examples/tutorial/control_shaker.py
uv run python examples/tutorial/choose_stirring_speed.py
uv run python examples/tutorial/stir_sample_rack.py
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

Version: none, documentation and example descriptions only.
