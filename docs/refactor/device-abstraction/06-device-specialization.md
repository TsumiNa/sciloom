# Rebind portable programs to devices

## Goal

Rebind portable programs to devices, following the [authoritative interface contract](00-overview.md).

## Scope

Implement comptime.can_write/supports/is_device, typed static-branch lowering and pure core.specialization. Preserve both branches in authored IR, validate all source/schema types, then select and validate supported retained operations. Add CompileResult.specialized_ir and cross-target/JSON examples, update all current architecture and interface docs.

## Non-goals

No arbitrary host evaluation, GUI/server, getters, time model, implicit missing-binding fallback or serialized plugin import.

## Binding and specialization detail

The final binding envelope adds required
`base_contracts: tuple[DeviceTypeContract, ...]` beside `contract`. This is the
complete trusted ancestor directory, not Python classes; `bind_device()` builds it
from the profile MRO. Direct Target implementations supply these records explicitly.
Validate the directory and compare matching authored type IDs with trusted records.
This supports a bound subtype whose intermediate bases do not occur in source/JSON.

`specialize(program, *, bindings) -> Program` validates authored IR and bindings,
selects DeviceIf branches, prunes unreachable functions, and changes resource
declared types to the trusted bound types. It merges their data contracts into the
directory, preserving node IDs and source positions. Inactive extension records
remain in authored IR; the specialized directory contains bound types and ancestors.
Missing bindings are checked before branch evaluation.
The specialized result remains a high-level semantic program and is validated
again; capability/configuration analysis runs before Target validation/emission.
Existing device examples therefore receive new semantic hashes/ASFP UUIDs when
bound resource types are made explicit; authored `.to_ir()` stays unchanged.

`can_write` resolves a literal member name from compatible device declarations
imported into the runtime method's defining namespace. Ambiguous/unknown names
fail; no global plugin registry is introduced. This query does not narrow the
Python type. Use `is_device` for access to subclass-only members.

## Acceptance

The implemented portable developer example verifies authored JSON → AutoSuite/Demo
compilation → reference snapshots. Source, direct-IR and native-free subprocess
tests cover selection, trusted ancestry/signatures, cross-function configuration,
pruned calls, idempotence and retained diagnostic identities. TypeGuard positive
and negative cases run through mypy. No new runtime/hardware semantics are claimed.

Run shared acceptance; test TypeGuard, guarded native properties/commands, all-branch typing, missing bindings, unsupported selected operations, unreachable-function pruning, native-free JSON loading, source/direct-IR equivalence, pure deterministic specialization and interpreter rejection of unresolved nodes.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.
