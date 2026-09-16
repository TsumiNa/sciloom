# Runtime device-location evidence

Stage 16 introduces high-level DeviceAt and data-only candidate bindings. It does
not claim native dynamic selection has passed Executor, and does not activate
unchecked Stir emission or native private selection-parameter transport.

## Source evidence

The primary APP's extracted F24 (`24_Sample and Run GPC.asfp`) uses
`reactor_zone` as the Stir Zone and leaves task `progid`/`deviceid` empty. This
establishes a serialized runtime Zone operand, rather than requiring a literal
zone string in every function. See [agitation mapping](16_AGITATION_MAPPING.md)
and [capability audit](18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md). Manual 3.6.19
(printed pp. 73–74) explains agitation; it does not prove SciLoom's additional
candidate-membership or fail-before-action semantics.

The primary APP and read-only layout importer preserve well ownership and element
ancestry. For example, the local `Heater Shaker 23` Zone selects well 27 on
ISynth-2 (device 1.1), whose ancestor is IndividualShaker 23. Zone index, well
identity, local device address and controller identity are different facts.

Stage 17's real-APP check also found that the Zone named `Heater Shaker 24`
belongs to controller 21, while `Heater Shaker 21` belongs to controller 24 in
this supplied APP. No rename or correction is inferred: the names are not
binding evidence. The new author example uses the verified 23 and 22 profiles
and still validates their ancestry from the caller's APP.

## Implemented deployment checks

`AutoSuiteAgitatorSelection` contains nonempty, same-profile individual shaker
candidates. A target with candidates requires `AutoSuiteLayout`. Every candidate
Zone must exist and contain wells, and all its wells must descend from exactly
the declared `Chemspeed.SADeviceIndividualShaker.1` address. Different logical
devices cannot alias candidate controllers. Binding uses actual identities, not
matching Zone labels alone. A supplied layout also validates fixed bindings;
fixed compilation without a layout retains its previous contract and bytes.

The reference scope captures one Zone, rejects empty/unknown/outside/multiple
controller selections before body effects, and inherits through shared-resource
calls. Configuration belongs to the logical device; applied values/running
state belong to each physical controller. Selecting B does not stop A. A stop
on B preserves B's applied values, independently of A. Exiting a scope on success
or failure releases context but causes no equipment action or rollback.

## Evidence matrix

| Concern | Existing XML | Manual semantics | Reference/static validation | Executor |
| --- | --- | --- | --- | --- |
| Runtime Zone operand | F24 Stir | 3.6.19 | High-level DeviceAt and JSON v4 round trip | Pending |
| Candidate/controller ownership | Primary APP element/well ancestry | Layout/device concepts | Synthetic invalid layouts and primary APP read-only tests | Deployment acceptance pending |
| Cross-call capture/context | No direct proof of SciLoom scope contract | No equivalent scope guarantee established | DSL/IR/JSON, shared children, nesting and recursive-scope rejection tested | Native context transport inactive |
| Fail before a physical action | No proven fatal primitive | Error behavior is insufficient alone | Reference rejects invalid selection before body; no rollback invented | [Failure gate](24_RUNTIME_FAILURE_GATE.md) remains open |
| Independent running state | Separate physical controllers in APP | Stir configures switch/speed together | Immutable physical snapshots, repeated calls and session isolation | Physical/Executor equivalence pending |

AutoSuite rejects DeviceAt/candidate compilation with
`unsupported_device_location`, after semantic/deployment checks. An explicit
runtime dialog, skipped branch or unverified bounds read is not a replacement
for fatal propagation. The target has no unsafe override. Add actual Executor
results and native transport only after the failure gate is satisfied.

Original evidence and its corpus manifest remain unchanged.
