# Stage parameters until explicit start

## Goal

Stage parameters until explicit start, following the [authoritative interface contract](00-overview.md).

## Scope

Implement property declarations, runtime ConfigureProperty and explicit StartAgitation/StopAgitation across DSL, IR, interpreter and AutoSuite. Define the complete v4 catalog/static/extension wire vocabulary; unsupported execution paths fail explicitly. Implement definite configuration across calls and backend private context threading. Remove set_speed/SetAgitation and migrate docs, tests and learning outputs together.

## Non-goals

No real getters/duration, public globals or recovery, arbitrary plugin execution, or condition-query execution before stage 6.

## Implemented interfaces

Author property/start/stop code in the overview is executable from this stage.
`PropertyContract`, `CommandParameter`, `CommandContract`, `DeviceTypeContract`,
`DeviceResource`, `ConfigureProperty`, `StartAgitation`, `StopAgitation`,
`DeviceCommand`, `CommandArgument`, `DeviceIf`, `CanWrite`, `SupportsOperation`
and `IsDevice` are the public v4 data vocabulary in `sciloom.core.ir`.

The binding envelope now owns `contract: DeviceTypeContract`, plus explicit
`writable_properties` and `supported_operations` semantic-ID tuples; type identity
and ancestry are read from the contract. The overview's binding example is updated
in this stage. Contributor declaration helpers are `device_contract(cls)` and
`bind_device(logical_id=..., device=..., physical_id=...)` in
`sciloom.devices.declarations`. They inspect declarations without invoking bodies.
Command defaults/variadics and non-None returns are rejected; setter values must
be positional and agree with getter annotations.

Reference results use `DeviceState(configuration, applied_configuration, enabled)`
and `DeviceEvent(node_id, resource_id, operation_id, state)`. Both are available
from `sciloom.core.interpreter`; the developer example verifies their snapshots.
Property lists obey the same immutable value-copy rules as runtime variables.

Native command and device-condition data round-trip in v4, but the compiler
explicitly rejects them until stages 5/6. The interpreter rejects unresolved
conditions at construction and unknown native commands on execution. There is
no parallel v3 reader or legacy operation alias. Rebuilt ASFP UUIDs reflect v4.

## Acceptance

Run shared acceptance; test capture timing, configured/applied separation, persistent/shared state, independent sessions, empty-loop and branch initialization, parent/child state flow, JSON v4 strictness and native typing. Inspect ASFP hidden state and unchanged public entry inputs. Regenerate v4 companions.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.
