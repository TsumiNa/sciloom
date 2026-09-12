# Verify an independent device contribution

## Goal

Verify an independent device contribution, following the [authoritative interface contract](00-overview.md).

## Scope

Add the contract's independent DemoAgitator with gain configuration, its registered calibrate() command and a recording Target. Demonstrate schema extension, required multi-parameter configuration, typed arguments and gain range validation using public contributor interfaces. The added device itself must require no shared DSL/core edits.

## Non-goals

No invented real AutoSuite hardware operation or measured semantics.

## Acceptance

Run shared acceptance; verify gain writes and calibrate() produce the expected recording-target output, unsupported-device diagnostics, contract mismatch and parameter errors, required configuration, and independent target/import typing. Keep developer output documentation next to its source.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.
