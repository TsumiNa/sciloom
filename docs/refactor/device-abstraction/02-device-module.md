# Move the existing device implementation

## Goal

Move the existing device implementation, following the [authoritative interface contract](00-overview.md).

## Scope

Move Agitator into sciloom.devices and update owning-module imports, tests and live documentation. Preserve root imports, current methods, IR and generated artifact bytes.

## Non-goals

No device slots, property lifecycle, bindings or JSON changes.

## Acceptance

Run shared acceptance; compare example JSON/ASFP bytes with the parent commit and check core import isolation.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.

