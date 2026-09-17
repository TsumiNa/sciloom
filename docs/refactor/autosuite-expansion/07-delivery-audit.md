# Expansion delivery audit

This records the accepted scope against concrete artifacts. It separates shipped
semantic/static work from **unfinished native acceptance**. An implemented/gated
stage is the explicitly accepted evidence-limited path, not a claim that an
AutoSuite profile or Executor result exists. Conditional native-unlock PRs are
still pending and must not be silently marked complete.

Audit baseline: main `d23a3a37d3782ad2f4179828d03f4d03fe9b883b` plus the R7
integration change; lockstep 0.11.0. Remote merge metadata was checked for every
PR #103–#116. R7's own PR is the final review/merge gate; local checks alone do
not close it. Full-suite results are recorded in the
[R7 plan](r7-integration/01-plan-workflows.md).

## Requirement-to-evidence map

Paths below are repository-relative. They point to behavior and tests, not only
to plan prose; the listed tests are included in the required full suites.

| Accepted requirement | Implementation and verification evidence | Remaining limitation |
| --- | --- | --- |
| Plans, priority, dependency order, one authority, preflight and discrepancy handling | This plan set; `01-contract.md`, `02-execution-rules.md`, `05-decisions.md` D001–D026; stage plans retain Goal/Scope/Non-goals/Acceptance/Version; remote PR sequence #103–#116 | R7 review/merge recorded by its PR; no material semantic exception was silently taken |
| R1 read-only APP version/hash/reset facts, separate layout provenance and target report | `sciloom_autosuite/deployment.py`, `layout.py`, `deployment_test.py`; exact compressed-byte identity, malformed settings and same/unknown/mismatched provenance tests | Product/profile facts are not execution evidence |
| R1 persistent Var/config requirements, reject known incompatible APP, retain offline ASFP and review conditions | `target.py`, `deployment.py`, `review.py`, their tests and `examples/developer/deployment_review.py`; integration compares old shaker bytes and paired report hashes | Reset=0/1 native state behavior is pending |
| R1 accumulator, shared/independent instances, loops, restart | `autosuite/tools/probe_state_lifetime.py` and colocated tests; reference session/ownership results and separate host-run records for both settings | Generated probes are not native results; doc 33 carries host cases |
| R2 evidence provenance and actual bytes/order/repeated runs | `autosuite/docs/34_EDITOR_SCREENSHOT_EVIDENCE.md`, doc 35, `validate_native_receipt.py` and 33 tests; identities/dirty state/controls/commands and CSV continuity checked read-only | Receipt completeness returns pending_review, never verified; no accepted native receipt exists |
| R2 failure/CSV unlocks without bypass flags | Existing `probe_runtime_failure.py`, `probe_csv_read.py`, `probe_csv_append.py`; target rejection and tools regressions | R2.2–R2.4 remain conditional pending work; no read/append/propagation equivalence claim |
| R3 ordered text/bool results, whole assignment RHS, declared destination, single capture, child/loop order | `dsl/driver_dialogs_test.py`, `core/ir/codec_dialogs_test.py`, typed RequestText/AskYesNo and interpreter handlers | AutoSuite result/cancel/Stop/timeout behavior remains gated |
| R3 empty text/False accepted, absent/exhausted/wrong service rejected, cancellation/Stop/deadline fatal before later effects | `interpreter/dialogs_test.py`, `driver_dialogs_test.py`, `examples/capture_barcode_test.py`, R7 mixed failure tests | Doc 36 and 30 generated probes define native measurements; no response is inferred |
| R4 stable ConfigureProperty/DeviceCommand and old agitation vocabulary; typed lifecycle requirements/effects | `core/ir/device_contracts.py`, `configuration.py`, codec/lifecycle tests; old CommandContract retains its shape | Unknown ordinary command still rejects without defined semantics |
| R4 per-resource/property-ID typed backend storage, capture/snapshots/shared calls | `sciloom_autosuite/device_state.py`, `device_state_properties_test.py`; scalar/list nested-call transport; generic reference snapshots | Private backend transport stays outside Program; no synthetic profile grants native support |
| R4 subclass extension and actual actuator identity conflicts | `devices/declarations.py`, binding tests, independent contribution example; R7 mixed physical-ID collision regression | Same geography does not imply same physical actuator; native identities need profile evidence |
| R5 absolute temperature/difference/rate throughout author/IR/JSON/reference/type checking | `units_temperature_test.py`, `driver_temperature_test.py`, `codec_temperature_test.py`; affine arithmetic and invalid absolute sums | Native encoding/ranges/conversion remain explicitly rejected; core SI is unchanged |
| R5 fixed Heater settings, explicit apply/start/stop, missing/conditional/cross-call configuration | `devices/heating.py`, `device_state_heating_test.py`, `warm_sample.py` and direct IR; mixed flow uses real generic lifecycle effects | No telemetry, wait-to-temperature or dynamic thermal selection API |
| R5 concrete native profile evidence and offset investigation | Doc 37 inventories eight APP tasks and specifies exact input/re-export/gradient/profile measurements | R5.3 merged as capture documentation, not a native adapter; profile constructor awaits evidence |
| R6 Zone command arguments, flow/length dimensions, property boundary unchanged | `devices/declarations_locations_test.py`, `units_transfer_test.py`, `driver_transfer_values_test.py`, `codec_transfer_values_test.py` | No Zone property/list-of-Zone escape hatch; native quantity encoding gated |
| R6 one-pair transfer, declared-order capture, explicit fixed facts, positive flow/volume, gap/capacity and known distinct allowed single wells | `TransferDeviceBinding`, `DeviceSession.transfer`, `device_state_transfer_test.py`; compile/reference requirements, reordered JSON capture and failure-before-transfer checks | Reference event is intent, not liquid inventory or physical precision; dynamic liquid-handler bindings reject |
| R6 explicit tool/channel/calibration/position/rinse in a proven native adapter | Doc 38 records all 17 primary tasks, secondary 48-row evidence and paired single-channel capture matrix | R6.3 merged as capture documentation; actual profile/typed payload/static native transfer still pending |
| R7 three author/manual-IR/JSON flows with truthful per-layer status | Existing barcode, heater and transfer paired examples; `mixed_equipment_ir_test.py` compares all forms, outputs, event order, locations, native gates and no ASFP output | All three new complete flows are native gated; Executor status pending |
| R7 mixed new/old devices and cross-function state | `mixed_equipment.py`, `mixed_equipment_ir.py/.json`; two child calls, 1→3 mL/min snapshot, explicit stops, repeated entries, restart, cancellation and capacity failure | Earlier effects survive a later failure; no hidden rollback or shutdown |
| JSON remains v4, old bytes/readers and deterministic outputs | `core/ir/schema.py` typed-record codec, `codec_compatibility_test.py` immutable fixtures/hashes, baseline native codegen and regenerated existing companions | New vocabulary may be rejected by old readers; no implicit migration |
| Every added type/node is handled or rejected across consumers | Full source/codec/specialization/reference/target suites, concrete profile gates and layer-boundary tests | Static success cannot substitute for native evidence |
| Corpus read-only; public artifacts exclude raw evidence/internal plans | Read-only corpus audit; `website/tools/site_test.py` explicit allowlist, symlink and stale-output protections; R7 only adds listed generated learning artifacts | Host receipt collection remains external; no corpus file is generated/rewritten here |
| Sequential reviews, latest-head CI, squash merge, lockstep version and no publication | D001–D026 and remote PR metadata; lockstep checks/build guard; R7 changes no shipped production API | No release tag/package publication is requested or performed |

## Current flow status

| Flow | Python | Direct IR | JSON v4 | Reference | Static AutoSuite | Executor |
| --- | --- | --- | --- | --- | --- | --- |
| Barcode → property → log | Available | `barcode_ir` | Available | Explicit responses/locations/property store | Gated result-dialog/singleton semantics | Pending |
| Heater → fixed wait → stop | Available | `warm_sample_ir` | Available | Fixed binding/virtual time | Gated thermal profile/encoding | Pending |
| Single-pair transfer → log | Available | `transfer_sample_ir` | Available | Fixed binding/locations/capacity | Gated transfer profile/encoding | Pending |
| Mixed shared-child flow | Available | Source-derived IR; constituent manual builders above | Available | Three fixed actuators, ordered effects | Gated new profiles/effects | Pending |
| Existing fixed shaker control | Available | Existing agitation IR example | Available | Existing configuration/lifecycle behavior | ASFP plus review report available | Not proved by this audit |

## Native work remains open

No valid receipt for the following is available: reset-dependent lifetime;
entry/child/loop/caller failure propagation; CSV read and repeated append byte
semantics; operator result/terminal behavior; thermal profile and temperature
offset; fixed-tool transfer calibration/ranges/topology/rinse behavior. Their
questions and exact next evidence steps remain in [Q&A](06-qa.md) and docs 24,
27, 28, 33, 35–38. Existing compiler rejections must remain until a separate
evidence-backed unlock PR passes the same review/CI/merge sequence.

The accepted first implementation wave can close its independently valid
implemented/gated PRs under the user's explicit rule. It cannot be described as
"all native capabilities verified" or "ready for instrument deployment." A
requirement audit that includes native operation completion must classify the
items above as **unverified/incomplete**, not silently redefine them as passing.

Deferred beyond this wave: measured temperature/wait-to-temperature, weighing,
pH, parallel/mutex, external processes, dynamic routing, multichannel packing,
capacity splitting, closed-loop transfer and Application/global compilation.
No placeholder public APIs were added for them.

## Version

Version: none, requirement/evidence audit only; package versions remain 0.11.0.
