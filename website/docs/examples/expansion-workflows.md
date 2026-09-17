# Operator and equipment workflows

The following procedures use the same typed semantic program for Python, direct
IR, JSON v4 and reference execution. The status table separates language behavior
from native compilation and Executor acceptance.

| Workflow | Python / direct IR / JSON | Reference execution | AutoSuite static generation | Executor acceptance |
| --- | --- | --- | --- | --- |
| [Barcode → single-well property → log](capture-barcode.md) | Implemented | Explicit location, metadata and response services; cancel/Stop/timeout prevent later effects | Gated: result-dialog termination and runtime singleton check | Pending |
| [Heater configuration → start → fixed wait → stop](warm-sample.md) | Implemented | Fixed binding and explicit clock; saved/applied states are separate | Gated: exact thermal profile, conversion and payload | Pending |
| [Single-pair transfer → log](transfer-sample.md) | Implemented | Explicit fixed tool capacity, allowed wells and flow/gap settings | Gated: fixed-tool profile, native encoding and route/calibration/rinse facts | Pending |
| Mixed procedure below | Python and source-derived JSON; each constituent has an independent direct-IR example | Three distinct actuators, shared child configuration and ordered effects | Gated: verified new profiles and constituent operations are unavailable | Pending |
| [Existing fixed agitation](agitation.md) | Implemented | Explicit saved/applied state | Generates ASFP; review export can include deployment conditions | Not established by compilation |

No recording target produces an ASFP for a gated flow. Fixed waits express time,
not reaching temperature. Reference transfer records intent, not liquid inventory
or instrument accuracy. Native acceptance requires actual deployment evidence.

## A shared equipment cycle

The parent captures a barcode and stores it before configuring equipment. A
shared child starts heating and agitation, waits ten seconds, transfers 0.25 mL,
then explicitly stops both devices and logs completion. Changing the parent's
aspirate-flow setting affects the second transfer; it cannot change the first
transfer's immutable event snapshot.

```python
--8<-- "examples/mixed_equipment.py"
```

Run `uv run python examples/mixed_equipment.py`. It reports the current native
gate and writes no ASFP. The numerical settings demonstrate composition, not a
validated process recipe.

For contributors, this companion supplies all reference services and bindings:

```python
--8<-- "examples/developer/mixed_equipment_ir.py"
```

Run `uv run python -m examples.developer.mixed_equipment_ir`. It writes the complete
`mixed_equipment_ir.json` companion and reports barcode `S-001`, two transfers,
20 seconds elapsed, aspiration flows 1 and 3 mL/min, and all actuators stopped.
The source paths in this generated JSON are relative to the repository root.

Cancel, Stop, timeout and invalid responses prevent metadata writes and every
device action. A later transfer error preserves earlier metadata/logs and already
started device state; it prevents subsequent transfer, stop and success-log
statements. The reference interpreter does not invent rollback, recovery or
automatic shutdown. Physical fault behavior still requires native verification.

The constituent direct-IR companions are `barcode_ir.json`, `warm_sample_ir.json`
and `transfer_sample_ir.json`. Integration tests compare their outputs and ordered
events with their source programs and JSON restorations, including transfer source
and destination identities. They also check repeated calls, independent restarts,
resource conflicts and actual native-gate diagnostics.

## Deployment review remains separate

The existing deployment review example uses the
[review exporter](../user-guide/reference/devices-and-targets.md) to write an ASFP
plus a same-base `.deployment.json` report with exact artifact and IR hashes.
Offline reports have unknown deployment compatibility and pending native status.
Review export rejects a reference JSON artifact rather than relabelling it as
AutoSuite output. Supplying an APP enables provenance/reset checks; it does not
turn a report into an Executor result.

```python
--8<-- "examples/developer/deployment_review.py"
```

Run `uv run python -m examples.developer.deployment_review`. It reports reference
totals 1 and 2, deployment status unknown and native status pending, and writes
the two associated companions.

[Review example](../_generated/examples/developer/deployment_review.py) ·
[Generated ASFP](../_generated/examples/developer/deployment_review.asfp) ·
[Deployment report](../_generated/examples/developer/deployment_review.deployment.json)

[Author Python](../_generated/examples/mixed_equipment.py) ·
[Contributor Python](../_generated/examples/developer/mixed_equipment_ir.py) ·
[Complete mixed JSON](../_generated/examples/developer/mixed_equipment_ir.json)
