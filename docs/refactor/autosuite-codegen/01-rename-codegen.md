# Rename the AutoSuite code generation module

## Goal

Make Python source lowering and AutoSuite code generation distinguishable by name.

## Scope

Rename the backend module and its colocated tests to `codegen.py` and
`codegen_test.py`. Update imports and documentation together. Explain that
`compiler.py` owns both the Target protocol and the concrete shared pipeline,
while AutoSuiteTarget implements the protocol using vendor-specific generation.

## Non-goals

No semantic, artifact, public target API or Python frontend changes. No aliases.

## Acceptance

- `uv run pytest src/sciloom`
- `uv run python autosuite/tools/smoke_test.py`
- `uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv`
- `uv run python examples/function_call.py`
- `uv run python examples/agitation.py`
- `uv run python -m examples.developer.agitation_ir`
- `uv run python -m compileall -q examples/proposed_frontend`
- `git diff --check`
- Generated example companions remain unchanged; no stale backend module imports
  or current documentation paths remain. Existing backend and non-XML target
  tests continue to pass after the rename.
