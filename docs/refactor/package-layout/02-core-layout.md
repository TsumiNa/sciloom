# Consolidate shared core modules

## Goal

Consolidate shared core modules, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Implemented paths: `sciloom.core.ir`, `sciloom.core.compiler`,
`sciloom.core.diagnostics` and `sciloom.core.interpreter`. The scalar frontend and
AutoSuite backend retain their existing paths until stage 3. JSON remains v2.

Move IR/compiler/diagnostics/interpreter and their tests into core. Update all consumers, root compiler exports, subprocess import strings and live documentation.

## Non-goals

No DSL spelling, JSON version or backend behavior changes.

## Acceptance

Run shared acceptance; direct core imports and non-XML compilation work without vendor modules. Example ASFP bytes remain identical.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
