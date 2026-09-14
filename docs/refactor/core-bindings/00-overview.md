# Rename `sciloom.core.devices` to `sciloom.core.bindings`

## Why

Two modules were both called `devices`, one per layer. `sciloom.devices` is the
author-facing vocabulary: `BaseDevice`, device families such as `Agitator`, member
declarations and `bind_device`. `sciloom.core.devices` held the data-only records
a target produces when it answers each logical device slot: `DeviceBinding`,
`DeviceBindings` and `validate_bindings`. The architecture keeps these two device
abstractions apart on purpose (an author programs against a family, never a
brand; a target binds a concrete instrument to each slot), and the layering
tests enforce the import direction. The names did not: the architecture table
could only tell them apart by their descriptions.

## Decision

Rename the core module to `sciloom.core.bindings`. The name says what the module
holds. Nothing else changes: the three public names, their fields, the
validation they perform, the IR and the JSON contract are untouched.

Alternatives considered:

- Keep both names and rely on the descriptions. Rejected: the collision sits
  exactly on the distinction the architecture is built around.
- Rename `sciloom.devices` instead. Rejected: it is the name every author and
  tutorial uses, and "devices" is the right word for a vocabulary of devices.

## Consequences

Contributors who write a target import `DeviceBindings` from
`sciloom.core.bindings`. No release exists, so no published contract breaks. The
shipped AutoSuite member, the developer examples and the public tutorials move
in the same PR. Historical plans keep the old path with a note.

## Non-goals

No change to `sciloom.devices`, to the binding classes, to specialization or to
generated output. No compatibility alias for the old module path.

## Plan

One PR: [rename the module and its references](01-rename-core-bindings.md).

## Version

No bump: a rename of an unreleased contributor import path; the merged state is
`0.1.0+<merge commit>`.
