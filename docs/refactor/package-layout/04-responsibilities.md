# Separate conversion and execution responsibilities

## Goal

Separate conversion and execution responsibilities, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Split DSL fields/source/context/expressions/statements, IR types/type checking, interpreter values/evaluation and AutoSuite type/variable/expression generation. Keep cohesive orchestration entrypoints and colocated tests.

## Non-goals

No semantic changes, operation registries or generic pass framework.

## Acceptance

Run shared acceptance, compare example artifacts and diagnostic behavior; no new import cycles or compatibility wrappers.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.

