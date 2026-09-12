# Compile list programs to AutoSuite arrays

## Goal

Compile list programs to AutoSuite arrays, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Implemented: typed array declarations/parameters, private function and call copies,
runtime literal construction, checked reads/writes, and repeated While-condition
prerequisites. Author examples `scale_values.py` and `non_zero_array_min.py` have
generated ASFP companions. A conservative definite-assignment rule prevents stale
list outputs; the authoritative contract records this target restriction.
See [mapping evidence](../../../autosuite/docs/17_ARRAY_MAPPING.md). The wire test
model validates scheduling assumptions, not vendor execution acceptance.

Implement evidence-derived array encoding/bindings, temporary value isolation, list construction, checked reads/writes and condition prerequisite scheduling. Add numeric Non Zero Array Min learning reference and mapping documentation.

## Non-goals

No raw evidence rewrites, full volume model, CSV import or claim of Executor acceptance.

## Acceptance

Run shared acceptance, new examples and array/guard/call/loop fixture tests. Document evidence grades, update MANIFEST for reference docs, run corpus audit; keep the actual-host Executor gate explicit.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
