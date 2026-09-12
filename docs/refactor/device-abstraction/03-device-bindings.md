# Declare logical device dependencies

## Goal

Declare logical device dependencies, following the [authoritative interface contract](00-overview.md).

## Scope

Introduce BaseDevice/type identity, independent device-slot schema and immutable AutoSuiteIndividualShaker profiles. Bind via AutoSuiteTarget(devices=...). Add core binding facts/Target resolution and migrate every caller. The sole implemented runtime language remains set_speed/stop until stage 4.

## Non-goals

No property/start behavior, v4 or compile-time queries; no old-binding aliases.

## Implemented intermediate interface

Generic Agitator annotations are supported with v3; other slot types explicitly
require v4. Device profiles and bindings are immutable. A composed Function's
canonical path is the first path in a sorted breadth-first walk of host Function
attributes; shared logical references retain their owner's slot path. Unowned
references outside that composition fail. All declared slots on compiled Functions
require bindings, including slots without an operation in the current body.

```python
from sciloom import Agitator, Function, rpm, runtime
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget

class Mix(Function):
    agitator: Agitator

    @runtime
    def run(self) -> None:
        self.agitator.set_speed(600 * rpm)

result = Mix().compile(target=AutoSuiteTarget(devices={
    "agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
}))
assert result.artifact.suffix == ".asfp"
# v3: one logical resource and one Stir task; speed=10 rps, switchon=1.
```

Runnable after stage 3; equivalent executable coverage lives in
`dsl/device_schema_test.py` and `contrib/autosuite/codegen_agitation_test.py`.
Binding-path changes regenerate agitation UUIDs and the JSON example's resource
IDs/source locations. The v3 wire schema and observed Stir payload stay unchanged.

## Acceptance

Run shared acceptance; test annotation-only slots, inheritance, deterministic paths, logical sharing, type/duplicate/missing bindings and host access protection. Verify Target typing and empty bindings for device-free targets.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.
