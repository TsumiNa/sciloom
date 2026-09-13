# Decouple core tests from the AutoSuite member

## Goal

After `uv pip uninstall sciloom-autosuite`, `uv run --no-sync pytest src/sciloom examples`
passes, and the member's tests import no `sciloom.*_test` module.

## Scope

Move the AutoSuite-specific assertions out of the core tests into the member:
the XML prologue check in `flow/device_slots_test.py`, the `.asfp` suffix check
in `dsl/driver_list_test.py`, and the AutoSuite half of
`dsl/device_conditions_test.py` (new `sciloom_autosuite/portability_test.py`).
Switch the generic uses in `core/configuration_test.py`,
`devices/declarations_test.py`, `flow/device_slots_test.py` and
`dsl/device_conditions_test.py` to `examples/developer/demo_contribution`
(`DemoTarget`, `DemoAgitator`; two deployments with different device ids where
two targets are compared). `dsl/device_conditions_test.py` currently imports
`PortableAgitation` from `examples/developer/portable_agitation.py`, whose module
top level imports the AutoSuite target; give the core test its own portable
program fixture instead, and keep the example unchanged. Replace the member's
imports of `sciloom.flow.function_test`, `sciloom.core.configuration_test` and
`sciloom.dsl.driver_list_test` with local copies of those small `Function`
fixtures or with `examples/scale_values.py`.

## Non-goals

No production code or example changes; the root `dev` group keeps depending on
the member, because the CI examples import it; no change to the import guards.

## Acceptance

- `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy`, `uv run pytest src/sciloom packages/sciloom-autosuite/src examples`.
- `uv pip uninstall sciloom-autosuite`, then `uv run --no-sync pytest src/sciloom examples`
  passes, then `uv sync --locked` restores the environment.
- `uv run pytest packages/sciloom-autosuite/src` still exercises the XML prologue,
  `.asfp` suffix and portability assertions that moved there.
- A search for `sciloom.dsl.*_test`, `sciloom.core.*_test` or `sciloom.flow.*_test`
  under `packages/` finds nothing; a search for `sciloom_autosuite` and
  `portable_agitation` under `src/sciloom` finds only the import-guard strings.
- `uv run --group docs pytest website/tools`, `git diff --check` and
  `git diff --exit-code` pass.

## Version

No bump: tests only; the merged state is `0.1.0+<merge commit>`.
