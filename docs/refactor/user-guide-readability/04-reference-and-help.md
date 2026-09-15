# Reference and help readers can use

## Goal

Make questions, restrictions and errors easy to find and fix.

## Scope

Rewrite FAQ by task, troubleshooting by symptom, and reference tables with
accurate rules and updated lesson links. Retain every existing diagnostic code.
Move structured exception inspection into developer diagnostics documentation.
Review the complete User Guide and Getting started against the
[contract](00-overview.md), including slot sharing, state lifetime, compilation
versus execution, installation and input/binding explanations.

## Non-goals

No unverified AutoSuite instructions, raw evidence edits or API changes.

## Acceptance

Run PR1's full checks; verify retained diagnostic coverage and executable failure
examples. Inspect rendered navigation, links, search, downloads and code folds.
Confirm builds introduce no extra tracked changes and API/version publication
checks still pass. Complete the plan status before review, never after merge.

## Implemented coverage

FAQ starts with changing speed, sharing equipment and retained state.
Troubleshooting preserves all 66 diagnostic catalogue entries (30 distinct codes)
under symptom-based sections. Six wrong/fixed snippets cover units, loop syntax,
Boolean conditions, AutoSuite short-circuit rejection, output-list initialization
and configuration before start. Tests compile the failures and reference-execute
the corrections, including empty lists and repeated calls. Structured diagnostic
inspection and the collected failure script now live in developer troubleshooting,
with their executable tests retained.

Reference tables distinguish source-language restrictions from AutoSuite rules.
Class initializers, inherited declarations, logical slot sharing and runtime
state descriptions were checked against the implementation. Current capabilities
and glossary wording distinguish ordinary Python execution from compiled steps.
The documentation contributor guide records how correction snippets are tested.

Local validation passed: 345 package/example tests, 79 website tests, ruff,
mypy, smoke and recipe checks, all current examples and the strict build.
Rendered FAQ navigation, correction anchors, code blocks and reference tables
were reviewed in the browser. The complete lesson source/download tests and
unchanged developer cumulative tutorial tests passed. Regenerating examples and
building the site produced no additional tracked changes.

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

Version: none, documentation and verification only.
