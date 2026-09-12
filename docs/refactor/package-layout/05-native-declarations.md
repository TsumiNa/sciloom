# Use native types with explicit runtime roles

## Goal

Use native types with explicit runtime roles, following the [authoritative interface examples and semantics](00-overview.md).

## Scope

The scalar interfaces now execute in the existing function-call and agitation
examples. Their class/constructor docstrings demonstrate the documentation
convention. Generated ASFP remains byte-identical; developer JSON source locations
are regenerated after adding those descriptions. Lists remain a later stage.

Implement Annotated Input/Output/Var with one role, native scalar mapping, frozen defaults and host protection. Migrate all current declarations and author exports; add Function docstrings and update AGENTS.

## Non-goals

No lists or JSON version change yet.

## Acceptance

Run shared acceptance plus missing/nested roles, defaults, inheritance, host access and native type tests. Preserve ASFP bytes; regenerate source-location metadata if needed.

Check this stage against the exact imports, signatures and examples in the contract.
Update that contract in the same PR if an interface decision changes. Complete
review, resolve feedback, verify latest-head checks and confirm remote squash merge
before beginning the next stage.
