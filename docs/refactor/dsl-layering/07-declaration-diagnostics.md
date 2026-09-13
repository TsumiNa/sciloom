# One error model for declarations

## Goal

Report every class-definition-time rejection as a structured diagnostic, per the
[contract](00-overview.md).

## Scope

Replace the bare exceptions raised while a class body executes, in the device-slot
schema builder and in `device_contract`, with `IRValidationError` carrying a
`Diagnostic`. Update the affected tests. Document the resulting codes beside the
existing schema codes.

## Non-goals

Host-access guards keep raising `TypeError`; reading a device property or calling
a runtime method from host Python is not a declaration error. `bind_device` keeps
raising `TypeError` because it reports a target author's binding mistake. No
message rewording beyond what the new structure requires.

## Acceptance

Shared acceptance. Author-facing messages keep naming the offending declaration,
and no diagnostic mentions implementation vocabulary.

Use the exact names and signatures in the contract. Update the contract and the
affected stage examples in the same pull request if an implementation detail
changes an interface.

Complete review, address feedback, verify latest-head checks and confirm the
remote squash merge before starting the next stage.
