# Verify an independent device contribution

## Goal

Verify an independent device contribution, following the [authoritative interface contract](00-overview.md).

## Scope

Add the contract's independent DemoAgitator with gain configuration, its registered calibrate() command and a recording Target. Demonstrate schema extension, required multi-parameter configuration, typed arguments and gain range validation using public contributor interfaces. The added device itself must require no shared DSL/core edits.

## Non-goals

No invented real AutoSuite hardware operation or measured semantics.

## Implemented interfaces

The external `examples.developer.demo_contribution` package provides DemoAgitator
and DemoTarget using public device/core contracts. The runnable `demo_device`
module compiles gain, speed, lifecycle and calibrate into a JSON recording.
Generic DSL command binding and trusted capability checks are enabled; neither
shared implementation contains demo-specific IDs or range rules. The reference
interpreter still rejects calibration because its execution meaning is undefined.
Positive/negative typing tests cover quantity/property assignments and native
command calls. Additional command tests exercise scalar/list arguments and Python
parameter kinds. Device-condition execution remains stage 6.

## Acceptance

Run shared acceptance; verify gain writes and calibrate() produce the expected recording-target output, unsupported-device diagnostics, contract mismatch and parameter errors, required configuration, and independent target/import typing. Keep developer output documentation next to its source.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.
