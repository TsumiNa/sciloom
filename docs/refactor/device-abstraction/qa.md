# Collected device questions

These questions are collected for the user to ask experimenters together later.
They are not requests for immediate answers and do not block the accepted
provisional implementation. Keep question, decision, impact, evidence and status
together. The [interface contract](00-overview.md) is authoritative.

| ID | Question | Provisional decision | Impact | Evidence | Status |
|---|---|---|---|---|---|
| QA-001 | When running, should writes apply immediately? What should repeated start mean? | Writes stage configuration; start applies the complete snapshot and starts or continues operation. | Property semantics, snapshots, device adapters, author expectations. | User selected staged writes; original Stir submits complete speed/on state. | Pending experimenter confirmation |
| QA-002 | Does duration mean workflow waiting, a device timer, or automatic stop? Does timing begin at command issuance or setpoint attainment? | No generic duration property or automatic stop in this slice. | Future time types, blocking/completion and lifecycle semantics. | Stir has no observed duration field; Wait/Timer orchestrate timing; IController distinguishes WAIT and HOLD. | Pending experimenter confirmation |
| QA-003 | Should a getter return configured values, last-applied values or actual measurements? | Do not expose property reads yet; keep snapshots explicit and future telemetry separate. | Getter types, initialization, physical evidence and device read mappings. | Reference command state is not telemetry; actual/setpoint are distinct in manual IController. | Pending experimenter confirmation |
| QA-004 | What configuration should survive application restart or recovery after failure? | Reference sessions retain state across calls/runs; compile starts without assuming prior calls. AutoSuite hidden state returns on normal calls; post-failure recovery equivalence is not promised. | Storage lifetime, hidden context, initialization analysis, future handlers/shared storage. | Existing reference failure semantics retain preceding writes; current hardware faults are fatal. | Pending experimenter/platform confirmation |
| QA-005 | What parameter ranges and deployment combinations are valid on the actual devices? | Apply confirmed constraints only; reject invalid/unprovable constrained values; do not infer universal ranges or physical equivalence. | Profile validation, runtime inputs and deployment checks. | Manual 3.6.19 delegates ranges to device specifications; corpus supports selected zone/shaker bindings only. | Pending device specifications and experimenter confirmation |
| QA-006 | Which runtime Zone selections should one compiled agitation function accept: one controller, several wells on one controller, or several controllers? | Retain current fixed bindings until a runtime-location API is designed. A future Zone parameter must carry or satisfy a compatible device contract; an unconstrained runtime value cannot be fully validated at compile time. | Zone types and parameters, APP configuration lookup, capability validation and device specialization. | Colleague feedback; latest-app `24_Sample and Run GPC.asfp` passes `reactor_zone` to Stir; manual 3.6.19 and 3.8.5. See the [capability audit](../../../autosuite/docs/18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md). | Runtime parameter support confirmed in source; desired scope and validation policy pending |
| QA-007 | If a runtime Zone changes between configuration/start/stop, or two logical slots select overlapping hardware, which controller owns the saved and running state? | Do not infer an answer from fixed-binding state semantics or silently retarget a running device. Settle location capture, overlap and stop behavior before implementing dynamic addressing. | Shared configuration, alias checks, cross-function state, interpreter and backend addressing. | Current fixed-binding implementation has one state per logical resource; original parameterized Stir establishes addressing but not SciLoom's staged-configuration policy. | Pending design and experimenter confirmation |

## Updating this record

Stage-4 implementation evidence: configured/applied snapshots and normal-return
transport are covered by `core/interpreter/device_state_test.py` and
`contrib/autosuite/device_state_test.py`. These are semantic/static checks; QA-001,
QA-004 and QA-005 remain pending experimental/platform confirmation. The evidence
levels and Executor requirements are recorded in the
[AutoSuite mapping note](../../../autosuite/docs/16_AGITATION_MAPPING.md).

Stages 5/6 add an artificial gain bound and recording calibration command solely
to test contribution and specialization. They provide no new experimental evidence
for QA-001–005. Cross-target/JSON tests verify software contracts; all five
experimenter/platform confirmation statuses remain pending.

Add new domain questions here rather than asking them individually. When an answer
arrives, record who/what supplied it, date, evidence and affected contract sections.
If a decision changes behavior, update the contract, relevant stage plans, examples
and tests together. Do not describe a provisional choice as experimentally verified.
