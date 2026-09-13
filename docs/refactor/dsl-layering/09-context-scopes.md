# Separate program-scoped and function-scoped lowering state

## Goal

Make the lifetime of lowering state explicit, so a reader can tell what is shared
across functions from what belongs to one function.

## Scope

Group the program-wide accumulators, built once by the driver, into their own
record, and keep the per-function fields on `LoweringContext`. Construct the
context after source discovery so every field is set at construction and no
module fills another module's attributes.

## Non-goals

No change to lowering behavior, node identifiers, diagnostics or the analysis
module boundaries. This stage is optional; the frontend is already acyclic and
readable without it.

## Acceptance

Shared acceptance. Generated artifacts are byte-identical, and the context no
longer carries an attribute set by a different module.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
