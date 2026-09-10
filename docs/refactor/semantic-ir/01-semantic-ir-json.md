# PR1: Typed IR with validated JSON

## Goal

Provide one typed, independently usable semantic representation for all frontends.

## Scope

Immutable dataclasses for packages, functions, owned variables, scalar expressions,
assignment, calls, If/Else and While. Integer, real and boolean scalar types.
Stable caller-supplied semantic IDs and optional source spans. Versioned JSON
import/export with structural and semantic diagnostics. Validate ownership, types,
call bindings and non-recursive call graphs. Synchronize the accepted field syntax
in project design documents and examples. Add pytest as a uv development dependency.

## Non-goals

Python source lowering, `.compile()`, XML generation, Application and global binding.
Function ownership is represented now; global declarations are not accepted yet.

## Acceptance

- JSON round-trips preserve IDs, types and order with deterministic encoding.
- Invalid JSON shapes, dangling IDs, cross-function references, invalid operators,
  type mismatches, incomplete call bindings and recursion produce diagnostics.
- `uv run pytest src/sciloom/ir` passes.
- `uv run python autosuite/tools/smoke_test.py` passes.
- `uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv` passes.
- `uv run python -m compileall -q examples/proposed_frontend` passes.
