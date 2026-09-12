# Rebind portable programs to devices

## Goal

Rebind portable programs to devices, following the [authoritative interface contract](00-overview.md).

## Scope

Implement comptime.can_write/supports/is_device, typed static-branch lowering and pure core.specialization. Preserve both branches in authored IR, validate all source/schema types, then select and validate supported retained operations. Add CompileResult.specialized_ir and cross-target/JSON examples, update all current architecture and interface docs.

## Non-goals

No arbitrary host evaluation, GUI/server, getters, time model, implicit missing-binding fallback or serialized plugin import.

## Acceptance

Run shared acceptance; test TypeGuard, guarded native properties/commands, all-branch typing, missing bindings, unsupported selected operations, unreachable-function pruning, native-free JSON loading, source/direct-IR equivalence, pure deterministic specialization and interpreter rejection of unresolved nodes.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.

