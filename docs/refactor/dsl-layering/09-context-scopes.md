# Separate program-scoped and function-scoped lowering state

## Goal

Make the lifetime of lowering state explicit, so a reader can tell what is shared
across functions from what belongs to one function.

## Scope

Group the program-wide accumulators, built once by the driver, into a
`ProgramScope` record, and collect what source discovery learns into a frozen
`RuntimeSource` handed to the context in one assignment instead of five separate
attributes filled from another module.

## Non-goals

No change to lowering behavior, node identifiers, diagnostics or the analysis
module boundaries.

Constructing the context after source discovery, so that every field is set at
construction, is deliberately not done. The driver registers a Function's
declared device slots before lowering its body, so a malformed slot reports
before a missing runtime method. Moving source discovery ahead of that loop would
reverse which diagnostic an author sees first, and the ordering is worth more
than the single remaining post-construction assignment, which is now commented at
its declaration.

## Acceptance

Shared acceptance. Generated artifacts are byte-identical, and the context no
longer carries an attribute set by a different module.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
