# Give statement recursion one owner

## Goal

Remove the statement-to-condition cycle by making `device_conditions` a
recogniser, per the [contract](00-overview.md).

## Scope

Add the `DeviceCondition` record and `device_condition`; delete branch lowering
and the function-local import from `device_conditions.py`. Add
`LoweringContext.narrowing` and stop mutating `narrowed_devices` from outside the
context. Build `DeviceIf` in `statements.py`, keeping the contract's allocation
order so the predicate keeps the lower sequence number. Shrink the allow list to
two.

## Non-goals

No change to query semantics, narrowing rules, diagnostic codes or messages, and
no module rename.

## Acceptance

Shared acceptance, plus a new assertion that the predicate identifier precedes its
`DeviceIf` identifier. `examples/developer/portable_agitation.json` is unchanged,
proving no renumbering.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
