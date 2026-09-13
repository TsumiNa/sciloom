# Name the conventions for adding an analysis module

## Goal

Write down the conventions a contributor needs in order to extend the analysis,
per the [contract](00-overview.md).

## Scope

Rename the lowering function `operation` to `device_command` so `operation`
means only the declaration decorator. Give module-private helpers a leading
underscore. Add the comment required on the remaining function-local import.
Record the five conventions in the `dsl` package docstring and in the developer
guide, including the mypy override list step. Correct the `compile_ir` docstring
claim about what its runtime check verifies.

## Non-goals

No behavior change, no diagnostic code renaming, no published API change.

## Acceptance

Shared acceptance, plus the documentation build. Every convention in the package
docstring is either enforced by the layering test or checkable by reading one
file.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
