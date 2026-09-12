# Lower Python list operations to semantic IR

## Goal

Lower Python list operations to semantic IR, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Implemented source conversion retains ListLiteral/ListLength/ListGet/ListSet
nodes. Tests execute the accepted ScaleValues class, compare Python and direct IR,
and cover frozen defaults, composed-instance isolation, len shadowing and explicit
unsupported forms. AutoSuite compilation remains rejected until stage 8.

Support typed list declarations/defaults, contextual literals, len, index read/write/augmented write, whole copies and function binding. Handle built-in expression calls separately from Function calls.

## Non-goals

No comprehensions, iteration, slicing, grow/remove methods or target list emission.

## Acceptance

Run shared acceptance and compare Python-lowered versus direct IR execution. Validate literal inference, bool indices, evaluation order, invalid containers, list defaults and parameter copying.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
