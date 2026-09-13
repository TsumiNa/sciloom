# Move composition discovery into the analysis driver

## Goal

Remove the declaration-to-entry cycle by relocating `component_paths`, per the
[contract](00-overview.md), leaving one documented seam.

## Scope

Move `component_paths` from the device-slot module to the analysis driver and
narrow its parameter to `Function`. Keep the `vars(...)` traversal that avoids
firing descriptors. Move its black-box test to a driver test module and add the
missing coverage for the private-name rejection. Comment the two runtime imports
of `Function` so they are not later demoted to type-checking imports. Shrink the
allow list to one, leaving the facade seam as the frontend's only deferred
import.

## Non-goals

No new module for a single-caller helper, no change to composition naming rules
or to the weak reference cache.

## Acceptance

Shared acceptance, plus the device-slot and driver test modules. The instance
dictionaries of a lowered model stay unchanged and instances stay collectable.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
