# Define list IR and reference behavior

## Goal

Define list IR and reference behavior, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

Implemented nodes: ListLiteral, ListLength, ListGet and ListSet (optional arithmetic
op preserves augmented assignment evaluation order). Run the direct-IR example
with `uv run python -m examples.developer.list_ir`; it is also exercised by CI.
JSON v3 and existing scalar ASFP artifacts are regenerated. After normalizing
UUIDs, scalar ASFP structure/payloads remain unchanged.

Add ListType and list operation nodes, strict JSON v3 and interpreter tuple value semantics. Add semantic/codec/copy/snapshot/index tests. Explicitly reject list programs in AutoSuite until stage 8.

## Non-goals

No Python list lowering or AutoSuite list generation.

## Acceptance

Run shared acceptance; direct IR list programs execute; JSON v3 round trips/rejects malformed input; list target rejection is explicit. Regenerate scalar artifacts for version-dependent UUID changes.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
