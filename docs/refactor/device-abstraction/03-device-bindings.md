# Declare logical device dependencies

## Goal

Declare logical device dependencies, following the [authoritative interface contract](00-overview.md).

## Scope

Introduce BaseDevice/type identity, independent device-slot schema and immutable AutoSuiteIndividualShaker profiles. Bind via AutoSuiteTarget(devices=...). Add core binding facts/Target resolution and migrate every caller. The sole implemented runtime language remains set_speed/stop until stage 4.

## Non-goals

No property/start behavior, v4 or compile-time queries; no old-binding aliases.

## Acceptance

Run shared acceptance; test annotation-only slots, inheritance, deterministic paths, logical sharing, type/duplicate/missing bindings and host access protection. Verify Target typing and empty bindings for device-free targets.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.

