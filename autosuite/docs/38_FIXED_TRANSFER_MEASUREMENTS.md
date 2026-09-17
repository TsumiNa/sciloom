# Fixed single-pair transfer: native measurement and profile gate

R6.2 implements typed single-pair **reference intent**. Native generation remains
rejected by `unsupported_device_command`; flow/length encoding is separately
gated. This document specifies the native evidence needed to implement a fixed
AutoSuite profile without guessing tool, channel, calibration or rinse behavior.
No Executor result or validated profile is supplied by this document.

## Sources and reproducible observations

Primary source: `autosuite/corpus/app/config20260909_polymerization.app`, SHA-256
`757854f4fc7c33ce8c14b02003a97d78263c34e8c5154638bd1a0d8e3b1bbcf5`.
The gzip-decoded XML matches `corpus/extracted/latest_app/application.xml`, SHA-256
`0b356ec816d30b995b17d7f4273a9cbac5d8d771913b6a87407d7220de03efb1`.
Product 2.47.1.1 / Swing XL Isynth. The default corpus audit checks this association
without rewriting either file. There are 17 `Chemspeed.SATaskLiquidTransfer.1`
elements: three in application tasks, fourteen in extracted functions.

All 17 name `4Needle Head` / `NeedleTypeStandard`. Their enabled and selected
syringe masks agree in this APP, but equality is not a general rule. Counts below
exclude the `<count>` child of `transferdatas`; each counted entry is a
`transferdataN` row. `A/E` means the observed `rinsealways` / `rinseatend` values.
An address pair is the raw `sourcewell:destwell` value, not a SciLoom well identity.

| Task ID | Container | Rows | Mask | A/E | Address pairs |
| --- | --- | ---: | ---: | --- | --- |
| 0959C60D-1561-4802-A10C-2BEAF291EC88 | Application tasks | 1 | 3 | 0/1 | 4294967295:4294967295 |
| 4513ABEB-09AC-4893-B93A-054D09C99863 | Application tasks | 1 | 12 | 0/1 | 4294967295:4294967295 |
| 138C7FED-FA1A-4561-96DC-498C05142752 | Application tasks | 1 | 3 | 0/1 | 4294967295:4294967295 |
| 239EE5C1-6C4B-43EE-8E8E-8AC5DDB24A8E | Prime All Port E | 4 | 15 | 0/0 | 0:0, 1:1, 2:2, 3:3 |
| 63F9C03B-8C72-4E0D-B339-B1FE37D7C4A7 | __GPC_InjectPort | 1 | 2 | 0/0 | 0:0 |
| 8FCECC17-8122-4557-B25D-7BB8C1A4C0F2 | __GPC_WashPortNeedle | 1 | 2 | 0/1 | 0:0 |
| 2F8A6B04-1250-432E-BB7E-CA51B8349A5E | Prime 2nd Sringe Port F | 1 | 2 | 0/0 | 0:0 |
| 91189457-1690-433B-BC79-2CAC21427F54 | Run GPC Analysis | 1 | 2 | 0/0 | 0:0 |
| 2AB755D7-D616-4CE2-9780-8CAD5AF15BC1 | Mix With Needle2 | 1 | 2 | 0/1 | 0:0 |
| 9E97265A-AD46-45C1-B8E1-A8F0C23ACB1E | Dilute and Mix | 1 | 2 | 0/0 | 4294967295:4294967295 |
| 1CF1E3C0-2D4F-4B32-B7CE-DE85174B0362 | Dilute and Mix | 1 | 2 | 0/0 | 4294967295:4294967295 |
| 883C5C59-F87E-4BB4-A214-34950D5564A2 | Priming 1st 2nd Syringe | 2 | 3 | 0/0 | 0:0, 0:1 |
| 25980D7C-8CEF-4D9C-9B57-B0FC6133E43C | Prepare GPC Sample | 1 | 3 | 1/0 | 4294967295:4294967295 |
| FE6B230B-DBE3-4065-B130-C783692CD345 | Prepare GPC Sample | 1 | 2 | 0/0 | 4294967295:4294967295 |
| D88C1B6B-8A6E-45A6-8E8C-26E41EB8DBA2 | __GPC_SolventInject | 1 | 2 | 0/0 | 0:0 |
| 6BC653F6-C3F8-4F14-92D7-EE413A8F9BED | Run GPC Analysis XXX | 1 | 2 | 0/0 | 0:0 |
| 3ABC35F6-5675-438F-A948-422A79471708 | Load Reagent | 1 | 3 | 0/1 | 4294967295:4294967295 |

`4294967295` is an observed serialization value; this guide does not reinterpret
it as a concrete well, `-1`, a zero-based index or a supported semantic wildcard.
Function names and masks alone do not establish physical channel identity.
The APP has explicit needle-head calibration fields; their presence or zero
values do not establish an accepted calibration for a new profile.

Secondary source: the user's `AutoSuite_截图转录.zip`, SHA-256
`5b578f51b313f169361fddbfc1e196df062d8e606bed2996fb7f58fe39c2e841`.
Its `test.asfp`, SHA-256
`9bce834bdc9981488b7a1612dcc12a390af684825f4c17712d8698bf5122b06a`, contains
task `{B139F33D-50FD-4C8C-88AB-F27BFE37CE9F}` with 48 rows, source `isynth2 all`,
destination `isynth1 all`, both masks 15 and rinse A/E 0/1. The first row has
quantity `1e-06`, air gap `1e-08`, source/destination speeds
`1.66666666667e-07`, and well addresses 0/0. The task's declared units are
`ml`, `ul` and `ml/min`. These are observations, not a new encoding implementation.
Screenshot 08 shows one-based UI well numbers; only this paired sample supports
that UI/XML correspondence. The package is not a complete successful execution
fixture, and its displayed September 17 APP was not supplied. See
[the screenshot evidence](34_EDITOR_SCREENSHOT_EVIDENCE.md).

## Capture one valid fixed-tool baseline first

Use AutoSuite Editor to create and validate a minimal function in a copy of the
intended deployment APP. Preserve the original received evidence unchanged.
Select exactly one source well, one distinct destination well, one explicitly
identified channel and a fixed tool. Record the actual equipment identities,
not only their display names. Supply volume, both flows and air gap explicitly.

Record and validate all deployment settings needed by that task: tool type and
usable capacity; channel-to-syringe mapping; calibration identifiers/version;
source/destination needle-position modes and lengths; required ports, valve,
rinse-solvent and waste connections; and an explicit supported rinse policy.
Any intentional no-rinse setting requires positive operator/profile evidence;
absence, an empty field or a grey control is not permission to disable rinsing.
Also record extra volume, post-air-gap, compensation, underrun/overrun,
equilibration, autofill and tool-unmount settings and whether they are active.
An adapter must account for every active field, not silently inherit a screenshot.

Export the Editor-produced function, reopen it, re-export it unchanged and retain
both hashes and the containing APP hash. Record product/build/profile versions,
task/function IDs and exact UI selections. A generated or hand-edited candidate
does not become a vendor original. Store generated probes outside corpus, and
receive vendor originals through the team's existing evidence process.

## Paired measurements and acceptance matrix

Change one control at a time in the validated Editor baseline. Each row needs
an original export and unchanged re-export, before/after UI values and native
results. Do not prefill pass/fail from what the reference interpreter predicts.

| Case | Required observation and acceptance |
| --- | --- |
| Volume, flow and length units | Two distinct nonzero values per field; exact SI/display conversion, precision and saved/re-exported payload. Include flow asymmetry so source/destination cannot be swapped unnoticed. |
| Channel identity | Select each candidate channel separately to measure masks/addresses; the first supported profile accepts only its one proven channel. A multi-bit mask is not accepted as a single channel. |
| Single-well identity | Non-first source and destination UI wells, swapped pair, and overlapping named Zones; preserve real well identities and prove the one-to-one address mapping in the same APP. |
| Capacity | Explicit usable capacity, liquid plus air-gap at and above its boundary; no implicit splitting or volume reduction. Distinguish gross syringe capacity from usable capacity and other active margins. |
| Ranges | Min/max and invalid volume, both flow rates, gap and profile-specific needle lengths/modes. Reject before action; do not infer one instrument's ranges for the generic family. |
| Topology | Valid route, missing source/rinse/waste connection, incompatible tool/channel and stale calibration. Confirm failure before aspiration and no caller continuation. |
| Rinse policy | Explicit supported policy and its exact ordered actions, including repeated calls. Confirm the configured rinse solvent/waste path; no silent disabling or automatic default. |
| Configuration lifetime | Configure in caller, transfer in shared child, reconfigure then transfer again, independent child, loop re-entry, consecutive entry calls and restart. Apply [deployment lifetime checks](33_DEPLOYMENT_STATE_LIFETIME.md); known incompatible reset settings remain rejected. |
| Failure boundaries | Entry, called function, loop and caller-after-call markers. Reuse [failure probes](24_RUNTIME_FAILURE_GATE.md) for propagation rather than creating a competing framework. |
| Mixed devices | Distinct physical heater/shaker/liquid actuators with shared well geography; real actuator conflicts reject. Check order without using zone names as physical identities. |
| Repeatability | Run the identical saved artifact twice and retain separate ordered logs/results. Configuration application, rinse order and subsequent log occurrence must agree with the explicit contract. |

For the host's exact saved generated APP, the existing simulation gate is:

```bat
AutoSuiteExecutor.exe generated.app /r /sim 100 /s /c
```

Record the actual resolved executable/version, full argv, working directory,
APP/ASFP hashes, exit/result and ordered markers before transfer, after transfer
and after caller return. A simulation run is not a measurement of physical
volume accuracy; physical equipment acceptance is a separately recorded result.
No command in this document has been executed on the AutoSuite host.

## Receipt and native-unlock requirements

Use the fields and evidence handling in [native receipts](35_NATIVE_MEASUREMENT_RECEIPTS.md):
source commit/dirty flag and package versions; original APP/export/re-export
hashes; generated candidate hashes; product and concrete profile versions;
execution command; exact inputs; ordered logs; observed result and controls.
That tool currently checks failure/CSV suites, **not transfer receipts**. Do not
mislabel a transfer result as a supported receipt suite or interpret completeness
as acceptance. Add any narrowly scoped transfer receipt validation only with the
actual captures; retain pending native status until reviewed.

Once evidence exists, complete the exact typed native constructor/binding example
in [the authoritative contract](../../docs/refactor/autosuite-expansion/01-contract.md#native-profile-entry-gate--r63)
before implementation. A future adapter must prove static singleton locations,
same-APP layout/deployment provenance, configuration capture/lifetime, explicit
route and calibration facts, and all active parameter mappings. It must keep
reference `TransferDeviceBinding` facts distinct from native XML payload records.
No arbitrary XML/dictionary passthrough, dynamic imports from IDs, hidden source
parameters, channel packing, route selection or capacity splitting is permitted.

Unlock only the proven profile and operations; unknown versions/profiles and
unproven runtime checks continue to reject. Source/IR/JSON/reference passing,
XML parsing and the historical [dynamic transfer algorithm](13_DYNAMIC_TRANSFER_CURRENT_SPEC.md)
do not satisfy this native gate. R6.3's present documentation-only implementation
is complete as **implemented/gated**; native adapter and verification remain pending.
