# Expose author and contribution packages

## Goal

Expose author and contribution packages, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Implemented paths: `sciloom.dsl` and `sciloom.contrib.autosuite`. Root compiler
exports and RuntimeField are removed; contributors use `sciloom.core.compiler`.
The remaining scalar author API is unchanged until stage 5.

Move frontends/python to dsl and backends/autosuite to contrib/autosuite. Remove old paths and root RuntimeField export. Update imports, lazy loading, tests, examples and current documentation.

## Non-goals

No native declaration or list semantics yet.

## Acceptance

Run shared acceptance; core execution blocks dsl/contrib imports; author imports and external target contract work. ASFP bytes remain identical.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
