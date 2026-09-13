# Recognize device members through the lowering context

## Goal

Remove the expression-to-operation cycle by moving `device_member` onto
`LoweringContext`, per the [contract](00-overview.md).

## Scope

Add `LoweringContext.device_member` beside `host_attribute`. Delete the free
function in `device_operations.py` and rewrite its five call sites in
`expressions.py`, `statements.py` and `device_operations.py`. Delete the
function-local import in `expressions.py` and shrink the layering allow list to
three.

## Non-goals

No diagnostic code or message change, no node identifier change, no other context
method moves.

## Acceptance

Shared acceptance, plus `uv run pytest src/sciloom/dsl`. Generated example
artifacts are byte-identical to the parent commit.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
