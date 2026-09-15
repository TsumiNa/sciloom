# Five independent tutorial snapshots

## Goal

Teach the experiment in the order defined by the [contract](00-overview.md).

## Scope

Replace all five lessons together; retain URLs and update navigation, labels and
links. Add the remaining three tutorial examples and companions, explicit public
downloads and CI/mypy coverage. Validate user pages against complete source files;
remove only the user's append-only series registration. Preserve the developer
series. Correct claims about measurement and runtime execution in touched material.

## Non-goals

No generic tutorial framework, public API changes or hardware execution.

## Acceptance

Run PR1's full checks. Verify both enabled branches, threshold values, empty
lists, loop reset, saved state and distinct instances/sessions. Compare generated
companions, actual rendered code and downloads. Each lesson must run independently;
developer cumulative tests must still pass. Check folded code and navigation.

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

Version: none, documentation, examples and tests only.
