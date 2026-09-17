# AutoSuite expansion: deployment semantics, interaction and equipment

## Authority and baseline

Accepted by the user on 2026-09-18. This sequence implements the seven-refactor
plan agreed after the independent review of 33 Editor screenshots and their
native ASFP. The baseline is main commit
`28a00c8c57a182f19bab3661a12fc06ee30f74c9`, lockstep version 0.3.15.

**R0 and R1.1 are merged; R1.2 deployment guards are implemented in this PR.**
R2–R7 remain planned; native verification remains pending.
The [contract](01-contract.md) is the single authority for new interfaces.
The [execution rules](02-execution-rules.md) require reassessment before every
refactor and PR, and whenever implementation or native evidence contradicts a plan.
Do not treat an example in this directory as an available API.

Existing [runtime capabilities](../runtime-capabilities/00-overview.md) are the
baseline, including reference CSV, locations, timers and property services.
Their integration landed in PR #102; the historical closing-PR wording is not a
reason to implement it again. Existing native gates remain pending.

## Goal

Repair deployment-dependent semantic gaps, extend typed IR/JSON where actual
new semantics require it, and add operator interaction, fixed thermal control
and bounded volumetric transfer to the AutoSuite contribution. Preserve the
typed semantic source of truth and the thin, versioned serialization backend.

The new sequence uses normal repository version rules rather than the previous
runtime-capabilities sequence's 0.3.x exception. Workspace packages remain
lockstep. No tag, release or package publication is authorized.

## Priority and sequence

| Refactor | Outcome | Plans | Code status | Native status |
| --- | --- | --- | --- | --- |
| R0 | Authoritative plans and reassessment rules | [Planning PR](03-plan-record-contract.md) | Merged, PR #103 | Not applicable |
| R1 | Deployment facts and persistent-state checks | [Overview](r1-deployment/00-overview.md) | R1.1 merged #104; R1.2 implemented, review/merge pending | Reset experiment pending |
| R2 | Evidence receipts and existing capability acceptance | [Overview](r2-native-verification/00-overview.md) | Pending | Existing failure/CSV gates pending |
| R3 | Text and yes/no operator results | [Overview](r3-operator-dialogs/00-overview.md) | Pending | Result/cancel/timeout pending |
| R4 | Typed command effects and multi-property device state | [Overview](r4-device-contracts/00-overview.md) | Pending | No new platform claim |
| R5 | Temperature values and a fixed thermal device | [Overview](r5-thermal-control/00-overview.md) | Pending | Exact thermal profile pending |
| R6 | Location arguments and simple volumetric transfer | [Overview](r6-volumetric-transfer/00-overview.md) | Pending | Exact transfer profile pending |
| R7 | Integrated source/IR/JSON workflows and status | [Overview](r7-integration/00-overview.md) | Pending | Per capability |

Default implementation order:
R0 → R1.1 → R1.2 → R2.1 → R3.1 → R3.2 → R4.1 → R4.2 →
R5.1 → R5.2 → R5.3 → R6.1 → R6.2 → R6.3 → R7.1.
R2.2–R2.4 are conditional native-unlock PRs: run at the next sequential boundary
where their prerequisite evidence is available, not in parallel with an open PR.
An unverified native task may finish its implementation stage as
`implemented/gated`; keep its public compiler rejection and record the unfulfilled
native acceptance. A native-unlock PR cannot merge without its evidence.

Every actual PR is independently green, reviewed and remotely confirmed squash
merged before another implementation PR begins. This includes R0. Do not create
later worktrees/branches while the preceding PR is open. Receipt collection on
the platform does not authorize parallel implementation.

## Architecture and decisions

- Retain Python → typed Program → specialization → target validation → target
  Serialization IR → XML. Reference execution is a semantic specification.
- JSON remains v4. Preserve existing kinds, field meanings and canonical bytes;
  add vocabulary through typed records, not a second JSON model.
- Deployment settings, vendor identifiers, profile payloads and private state
  transport stay outside Program. Layout is spatial data, not all deployment data.
- Saved configuration, applied configuration and measured physical state differ.
  Configuration writes capture values; explicit commands apply or stop.
- New device classes can reuse existing IR. New value/effect/location semantics
  require explicit typed extensions and all-consumer coverage.
- Missing evidence blocks the affected native capability, not unrelated reference
  work. No runtime option or manifest can bypass a native rejection.
- Keep old compilation entry points and deterministic outputs. Offline ASFP
  generation is retained with an explicit deployment review report.

Rejected approaches: rebuilding the compiler, a catch-all XML/dict operation,
dynamic imports from semantic IDs, hidden global-state workarounds, interpreting
every GUI field as active, or replacing real failure propagation with a log flag.

## Boundaries

This wave does not implement telemetry or wait-until-temperature, gravimetric
dispensing, pH loops, application/global compilation, external process execution,
parallel/mutex control, a GUI, an ASFP importer or a hardware I/O runtime.
Do not publish placeholder nodes/APIs for these. See [deferred work](04-evidence.md#deferred-work).

Original corpus and user archive remain read-only and excluded from publication.
Distilled AutoSuite facts belong in autosuite/docs; this directory holds design
and acceptance policy. [Evidence](04-evidence.md), [decisions](05-decisions.md)
and [questions](06-qa.md) are shared across the stages.

## Version

Version: none, this overview records a plan without changing shipped interfaces.
For code PRs decide PATCH/MINOR from actual final scope; MAJOR requires explicit
developer approval. Record exact lockstep versions at implementation time.
