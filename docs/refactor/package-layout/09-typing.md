# Enforce shared implementation type contracts

## Goal

Enforce shared implementation type contracts, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Add locked mypy development dependency/config/CI, complete core/contrib function annotations, preserve decorator signatures and py.typed, and add positive/negative interface/native-field typing checks.

## Non-goals

No whole-project strict mode, plugin, or claim of complete DSL call/role/device static checking.

## Acceptance

Run shared acceptance plus uv run mypy and typing positive/negative tests. CI uses the same reproducible command and supported Python versions.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.

