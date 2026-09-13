# Record the layering contract

## Goal

Record the [authoritative interface contract](00-overview.md) for the frontend
layering refactor before any code changes.

## Scope

Add the overview and the stage plans under `docs/refactor/dsl-layering/`. No
source, configuration or published documentation changes.

## Non-goals

No code movement, no cycle removal, no naming change, no public documentation
edits; those belong to the stages they describe.

## Acceptance

Run `uv run --group docs pytest website/tools` and
`uv run --group docs python website/tools/site.py build --strict`, and confirm the
refactor tree stays unpublished.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
