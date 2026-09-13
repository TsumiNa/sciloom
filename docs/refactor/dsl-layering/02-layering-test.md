# Make the layering executable

## Goal

Turn the layering claims of the [contract](00-overview.md) into a test, before
any of them is true, so every later stage moves a checked number.

## Scope

Add `src/sciloom/dsl/layering_test.py`. It parses every frontend module with
`ast` and asserts: the set of function-local intra-package imports equals an
explicit allow list, currently four entries; no declaration module imports an
analysis module at module level; and touching `sciloom.Function`,
`sciloom.Input` and `sciloom.comptime` in a subprocess leaves the analysis
modules out of `sys.modules`. Record the module-level dependency graph and the
current cycle count as an asserted value. Add the module to the mypy override
list in `pyproject.toml`.

## Non-goals

No production code change. The graph assertion records today's cycles rather than
forbidding them; stage 5 flips it to acyclic.

## Acceptance

Shared acceptance. The new test passes against unmodified sources, and removing
any allow-list entry without the matching source change fails it.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
