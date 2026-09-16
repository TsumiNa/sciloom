# Capability gaps and runtime Zone parameters

Audit date: 2026-09-16. Implementation baseline:
`9d818d89367b524585ed8f63f0ebaaefa15397a1` (SciLoom and sciloom-autosuite 0.2.0).
This is an evidence inventory and development recommendation, not an accepted
API design or a claim of Executor acceptance. The original corpus was read only.

The subsequent accepted [runtime-capability implementation plan](../../docs/refactor/runtime-capabilities/00-overview.md)
defines the new interfaces and sequence. This audit retains its baseline findings;
follow the plan's stage status for implementation progress.

## Findings

The corpus supports considerably more than the current compiler. This audit
identifies **12 bounded additions with enough evidence to begin implementation**,
**8 broader areas with partial evidence**, and **4 areas requiring additional
source material**. These are planning groups, not counts of vendor commands or
an exhaustive inventory of every manual option. Dependencies between groups
matter: CSV loading, for example, needs text and volume types first.

The colleague's observation about agitation is correct. AutoSuite accepts a
runtime `zone` function parameter and uses it in a Stir task. SciLoom currently
binds a logical agitator to a fixed zone and individual shaker at compilation.
Reusing Python with another target binding works; passing another zone to the
same compiled function is a missing capability. Hardware compatibility validation
also needs more than the checks in the current deployment record.

“Enough evidence” below means a bounded semantic contract and observed XML can
be implemented and checked against references. Every new serializer still needs
Editor re-export and Executor simulation. No instrument execution was performed
for this audit.

## Scope and counting method

The received local corpus contains:

| Input directory under `autosuite/corpus/` | Files | Distinct XML byte streams within that directory |
|---|---:|---:|
| `asfp/` | 58 | 58 |
| `app/` | 68 | 68 |
| `extracted/latest_app/functions/` | 52 | 52 |

APP files were decompressed with gzip before XML parsing. Every element carrying
a `typeid` was inspected, including elements named `task`, `task0`, and
`component`; searching only `component` misses evidence. ZIP members were not
counted again. The extracted functions overlap their parent application, and
different application snapshots contain repeated tasks. These numbers must not
be added to obtain a count of independent experiments or accepted fixtures.
Disabled tasks and historical generated candidates establish presence, not
successful execution. The latest application and its functions take precedence
when choosing implementation evidence.

The primary application is `corpus/app/config20260909_polymerization.app`, with
raw SHA-256 `757854f4fc7c33ce8c14b02003a97d78263c34e8c5154638bd1a0d8e3b1bbcf5`.
Counts describe this checkout, not a required canonical corpus for all developers.

There are **27 distinct task/flow component types** across those inputs. The
production backend emits **6** of them, leaving **21 without an emitter**. Even
the six implemented types cover selected behavior only. Text variables, Zone
parameters and sequential zones reuse existing component families, so a task
count alone understates the remaining language work. Conversely, a task manager
container is not an independent experiment operation. No coverage percentage is
inferred from these counts.

At the audited 0.2.0 baseline, the code boundary was:

- [Semantic types](../../src/sciloom/core/ir/types.py): integer, real, Boolean,
  rotational speed, and homogeneous lists of those types; no text, Zone, volume
  or time value types.
- [Semantic nodes](../../src/sciloom/core/ir/model.py): expressions, lists,
  assignments, calls, branches, loops, device configuration/commands and device
  specialization; no CSV, clock, wait, well-property or application-event nodes.
- [AutoSuite task generation](../../packages/sciloom-autosuite/src/sciloom_autosuite/tasks.py),
  [primitives](../../packages/sciloom-autosuite/src/sciloom_autosuite/primitives.py),
  [function generation](../../packages/sciloom-autosuite/src/sciloom_autosuite/functions.py),
  and [agitation](../../packages/sciloom-autosuite/src/sciloom_autosuite/agitation.py).

Implementation update for 0.3.2: A01 text/text lists and A02 volume/duration
quantities are now implemented, including their reference execution and bounded
AutoSuite mappings. The inventory above records the earlier baseline, not the
current type set. See [text mapping](19_TEXT_MAPPING.md),
[quantity mapping](20_QUANTITY_MAPPING.md) and the
[stage status](../../docs/refactor/runtime-capabilities/00-overview.md#stage-status-and-sequence)
for the implemented subset, remaining guards and pending Executor checks.

The contributor `DeviceCommand` mechanism does not itself implement AutoSuite's
Execute Operation task, arbitrary measurement results, or all vendor devices.
The [CSV recipe validator](../recipe/validate_recipe.py) runs on the host; it is
not runtime CSV support in compiled functions.

## A. Twelve bounded additions supported by the evidence

`Fxx` below identifies the exact latest-app function listed in the source key.
Manual references use **printed page numbers** in
`corpus/manual/1001.9796.T AutoSuite Software Manual.pdf` (AutoSuite 2.47.1.1).
Each row deliberately limits its scope; its tests are software/reference tests,
followed by platform acceptance, not substitutes for platform acceptance.

| ID | Addition and useful first scope | Original evidence | Verification to add |
|---|---|---|---|
| A01 | Runtime text and text lists: literals, assignment, parameters, concatenation, trim, length and the observed split operation. Needed for paths, reagent names and sample IDs. | F25, F28, F33, F45; manual 3.8.5, 3.10.4, 3.11.3. | Typed I/O and copying, empty strings, escaping, split boundaries. Define explicit SciLoom conversions rather than inheriting every implicit vendor coercion. |
| A02 | Volume and time quantities with canonical units, parameters and volume lists. These unlock recipe amounts, aspiration calculations and waits. | F28/F31 volume interfaces and `ml` import unit; F11/F13 Wait/Timer; manual 3.8.5 pp. 111–112. | Unit conversion, dimensional compatibility and round trips, including mL versus SI volume and minutes versus seconds. Temperature offsets and arbitrary derived dimensions are separate work. |
| A03 | Runtime Zone inputs/outputs and expressions: pass a zone to a function, resolve a named zone, inspect size/well identity, combine selected wells, and address an observed Stir task through the parameter. | F24, F30, F34, F48; manual 3.6.19 pp. 73–74, 3.8.5 p. 113, 3.9.2–3 pp. 134–136, 3.11.5 pp. 160–161. | Zone round trips and calls, empty/invalid selections, ordered unique wells, and a known compatible deployment. General dynamic hardware validation remains a design and platform gate; see below. |
| A04 | Sequential-zone traversal and selecting a well by index, initially with one zone and an explicit fragment size. | F43 and the per-well loop in F46; manual 3.8.10–12 pp. 121–126. | Empty/single/multiple wells, order, fragment boundaries and invalid index. Fragment position is not the ordinary loop counter. Coordinated multi-zone/batch scheduling needs a separate contract. |
| A05 | CSV import: selected-row scalar reads and all-row column reads into typed arrays, using the observed delimiter/header profiles and explicit result codes. | F25, F28; manual 3.7.8 pp. 88–92. | Headers, 1-based row/column selection, missing column/default, bad type, EOF, missing file and unit conversion. See the CSV section for the evidence limits. |
| A06 | CSV export: the observed one-row text-log profile, with path expression, column expression and I/O result. | F46; manual 3.7.9 pp. 93–96. | Repeated writes, result code, exact bytes and selected line endings in Executor. Other export modes are not established by this one XML profile. |
| A07 | Well metadata: write/read a named user property, use an explicit fallback, and label samples. | F45, F46, F50; manual 3.7.6–7 pp. 85–87. | Per-well isolation, missing/wrong-type properties, fallback and ordered assignments. This is stored well metadata, not an agitator measurement getter. |
| A08 | Wait for a duration; set a named timer and wait relative to it within a defined scope. | F11/F13 and latest APP: `waitmode=0` and `2`, `SATaskSetTimer`; manual 3.6.24 pp. 76–77 and 3.7.12 pp. 101–102. | A reference clock, elapsed-time behavior, use-before-set and timer scope. Waiting leaves device states unchanged; it does not imply automatic stop. Contact waits need a device signal contract. |
| A09 | Log typed values with category and stream expressions. Start with ordinary variables and computed values. | F24 and latest APP `SATaskLogData`; manual 3.7.11 pp. 100–101. | Value/type/category/stream capture and emitted task. A log expression that reads a device requires B08 as well. |
| A10 | Display a text message with the observed OK acknowledgement mode. | Primary APP `dialogtype=showmessage`, `buttonoption=ok`; F21/F47 instead use Stop/OK-Stop, as clarified in [the notification mapping](23_NOTIFICATION_MAPPING.md); manual 3.6.17 pp. 66–71. | Message evaluation and suspension/acknowledgement in a controlled execution model. Interactive input, timeout answers and stopping policies require their own probes. |
| A11 | Selected numeric builtins such as `abs`, `floor` and `round`, preserving explicit result and unit rules. | F30/F31/F35; latest APP logging uses `round`; manual 3.11.7 p. 162. | Negative values, boundaries, finite-value rules and result types. Do not silently map every Python math function or promise identical floating-point rounding. |
| A12 | Current wall-clock time formatted as text for log filenames. | F15 uses `DateTime('%Y-%m-%d_%H%M%S')`; manual 3.11.1 pp. 146–149. | An injected reference clock and controlled formatting/time-zone cases. This does not add the separate vendor timestamp type or make a clock read a compile-time constant. |

A01–A12 are implementation candidates, not twelve approved APIs or necessarily
twelve PRs. For example, A03 must first settle how a logical device receives a
runtime location without weakening its capability contract.

## B. Eight areas with useful but incomplete evidence

These areas are not impossible. Their observed subcases can guide adapters or
tests, but the available material does not justify a broad implementation claim.

| ID | Area | What is known | Missing evidence or design boundary |
|---|---|---|---|
| B01 | Broader array operations and container construction | F25 writes successive header cells; F30 builds selected zones; manual 3.7.2, 3.8.5 and 3.11.4 describes array assignment, sorting and removal. Existing array mapping records whole-array assignment. | SciLoom deliberately rejects out-of-bounds writes. Define explicit construction/growth instead of copying vendor implicit expansion. Obtain probes for holes, clearing, insertion/removal, type defaults, alias behavior and unused XML modes. The manual also contains conflicting array-initialization statements; prefer re-export evidence. |
| B02 | Application/global state, lifecycle events, fatal handlers and interruption | APP task manager/global variables, F07/F08 event records, F32/F47 error conventions; manual 3.8.6 p. 117, 3.9.4–6 pp. 136–138, 3.7.14 pp. 103–104. | Define an Application compilation unit and explicit shared state. Confirm event-number mappings, startup/stop/error order, interruption and recovery. The observed error latch is application logic, not proof of recoverable exceptions. ASFP compilation alone cannot supply the application's lifecycle. |
| B03 | Liquid transfer and native needle/diluter operations | F16–19, F23, F30–42; `SATaskLiquidTransfer`, named Aspirate/Dispense/Move and Extend operations; [dynamic-transfer analysis](13_DYNAMIC_TRANSFER_CURRENT_SPEC.md). | Known operations and chunk arithmetic are usable references. A reusable driver needs channel/capacity/port mapping, tool configuration, liquid class, motion/interlock constraints, units and completion/failure semantics. Manual 3.6.20 p. 75 delegates details to the system manual. Do not treat XML generation as a validated liquid-handling method. |
| B04 | Heating/cooling, external temperature control, reflux and vacuum | Latest APP contains SetTemperature, SetReflux and SetVacuum; `Suzuki-Miyaura-automation.app` also contains PeripheralTemperature. Manual 3.6.3–4, 3.6.11, 3.6.16. | Need concrete profiles, temperature/pressure/gradient types, range limits, controller roles and precise wait/hold/completion behavior. One device's task payload does not establish a common thermal-control protocol. |
| B05 | Reactor drawers, valves, gas and digital contacts | F04–06, F19–20, F41/F44; SetReactionBlockState; older APP Switch Contact and digital-output native operations. Manual 3.6.14 and 3.7.13. | Separate drawer position, gas routing and electrical contact capabilities. Confirm state enums, row/group mapping, parent-device relationships, signal polarity and interlocks against the installed hardware. Recipe-specific group sizes are not universal hardware rules. |
| B06 | Gravimetric transfer, tool/container handling and robot motion | Older APP `SATaskSolidTransfer`, GDU-Pfd mount/unmount and axis operations; manual 3.6.21 p. 75 and 3.7.3 pp. 80–82. | System/tool manuals, dosing parameters, balances, units, calibration, motion constraints and failure behavior. The historical solid-transfer payload has many device-specific fields. Do not generate arbitrary variants from names or copy inactive defaults as operating instructions. |
| B07 | External executables and integrated GPC/HPLC/MALS workflows | F01/F11/F13/F14 use Run Executable; APP records executable path, arguments, exit code, output capture, timeout and simulation behavior. Manual 3.7.4 pp. 83–84. | The task wrapper can be implemented in a bounded form, but it does not reconstruct the external scripts/programs, command-line protocol, output grammar or instrument-ready signal. Full analytical runs need those deployed dependencies and behavior on timeout/nonzero exit. |
| B08 | Actual device readings and result-bearing operations | APP expressions read values such as `"Vacuum Pump:actual value"`; F49 queries syringe capacities; manual 3.10.3 and device operation sections distinguish values/operations. | Establish typed telemetry names, units, availability, freshness and failure semantics per profile. Current property reads are forbidden and extension commands return no value. Stored well metadata (A07), configured values and actual measurements must remain distinct. |

## C. Four areas that need new source material

| ID | Mentioned capability | Material currently missing |
|---|---|---|
| C01 | Database task: queries, result mapping and database writes (manual 3.7.10 pp. 97–100) | No corresponding task component was found in the scanned APP/ASFP set. Need a vendor-produced export, connection/configuration schema, typed result examples and error/transaction behavior. |
| C02 | Other device families: pH, viscosity, microwave, sonication, capping/decapping and dedicated transport tasks (manual 3.6) | Descriptions alone are not serialization or driver contracts. No corresponding task/operation examples for these functions were found in this scan. Need exports plus the relevant device manuals, profiles and constraints. Observed robot/tool operations in B06 do not establish these families. |
| C03 | The newer Run Executable Custom Device (manual 3.7.5 p. 84) | The legacy Run Executable task is present; its XML is not proof of the newer custom-device configuration and operation/result signatures. Need that extension's exported configuration and minimal call/result samples. |
| C04 | Broader shuttle/ArkSuite workflows and cross-system scheduling | The manual mentions workflow/shuttle integration; the retained corpus does not establish the required deployment, protocol and task contracts. ArkSuite assumptions remain deferred under AGENTS. |

Other unobserved options inside an A/B feature also require evidence. In
particular, a manual list of choices is not a mapping of those choices to numeric
XML enum values. This inventory does not authorize guessing those values.

## CSV: what can actually be supported first

Across all scanned files, the unique import mode combinations are:

| `delimitermode` | `importrowmode` | `iswithheader` | Latest reference |
|---:|---:|---:|---|
| 0 | 0 | 0 | F25; F28 reads a reagent name from a selected cell |
| 0 | 1 | 1 | F28 reads experiment IDs and reagent volumes from columns |

F25 reads text columns using `columnindex=loop + 1` and stores results in
`header_txt_array`. F28 reads a text header, then column 1 into `expid_array_txt`
and a selected volume column into `reagent_array_vol` with the `ml` unit. These
are runtime file reads, not embedding the CSV during Python compilation.

The manual defines import result codes: 0 success, 1 type mismatch/default,
2 missing column/default, 3 end of file, and 4 file I/O error. Rows and columns
are selected with 1-based indexes, unlike array indexes. Zone is excluded as a
CSV destination type. A text zone name can subsequently be resolved separately.
Tests must establish how result codes aggregate across several bad cells/rows.

Only one export combination occurs: `delimitermode=0`, `endlinecharacter=0`,
`exportbehaviour=0`, `multiplelines=0`. F46 traverses a zone, reads each well's
`log_for_debug`, prefixes `WellFullName`, and writes column 1 of a text log file.
The workflow indicates repeated row logging; its exact append/new-file and byte
behavior still needs a small execution probe. Do not infer every numeric enum
mapping from UI ordering. The manual separately defines export result 0 as
success and 1 as I/O failure.

Before claiming general CSV compatibility, collect minimal exports and expected
files for alternate delimiters, line endings, overwrite/change-cell modes and
multi-row arrays. Also test quoting, delimiters inside cells, empty fields,
embedded newlines, Unicode/encoding, numeric locale and unequal column lengths.
Use known quantities to check imported units and exported conversion. Python's
standard CSV behavior is not evidence of AutoSuite's byte-level behavior.

F25's array construction must not silently weaken SciLoom's checked-index rules.
The new design can expose an explicit list-producing import or explicit list
construction; copying the original out-of-bounds writes into ordinary DSL
index assignment would change existing semantics.

## Assessment of the colleague's Zone feedback

### Direct evidence

F24 (`24_Sample and Run GPC.asfp`, in the locally shared corpus)
declares `reactor_zone` and `sampling_vial_zone` as scalar `zone` inputs, alongside
`shaker_speed` of type `angularspeed`. Its Stir tasks contain the following
selected fields (not a complete task):

```xml
<zone>reactor_zone</zone>
<taskdatas>
  <count>1</count>
  <taskdata0>
    <progid />
    <deviceid />
    <wellid>-1</wellid>
    <speed>shaker_speed</speed>
  </taskdata0>
</taskdatas>
<switchon>1</switchon>
```

The function definition ID is `{DE6D061F-54C0-46C9-920E-17C2CBB56BA4}`; the start
task ID is `{EA0D86C8-FC2A-49DA-9AA8-C1A44A6B7F3B}`. Its stop task also addresses
`reactor_zone`. Caller records in the original latest APP pass the expression
`reactor_zone` and select sampling zones with expressions such as
`FindZone('Sampling3-1')`. This is actual function parameterization in the supplied
program, not merely a feature listed in the manual.

Manual 3.8.5 p. 113 says Zone variables can reference another zone or be writable
and assigned through a task/function. Sections 3.9.2–3 describe typed function
inputs and expression bindings. Section 3.6.19 requires a Stir zone to contain
wells belonging to equipment capable of agitation. The existing
[agitation mapping note](16_AGITATION_MAPPING.md) already records dynamic Zone
parameters as outside the implemented fixed-binding slice.

### What the present code does

`AutoSuiteIndividualShaker` takes a Python `zone: str` and `device_id: str`.
The serializer writes those fixed values, including the individual-shaker
ProgID. This supports the following distinctions:

| Reuse scenario | Present support |
|---|---|
| Compile the same Python workflow with another fixed target binding | Supported |
| Share a logical device reference between child Functions | Supported |
| Call one generated ASFP function with different runtime Zone inputs | Not supported |
| Validate the selected profile's declared operations and configuration | Supported |
| Resolve the supplied Zone through an APP configuration and prove its wells belong to the stated physical shaker | Not implemented |

The profile checks a nonempty, single-line zone string and a positive decimal
shaker ID. Target resolution checks bindings and declared compatibility, but does
not read an application configuration to establish the physical relationship.
The caller currently supplies a matching configuration. A zone's rack/block
device ID can differ from its parent shaker ID; treating them as interchangeable
would be incorrect.

Even F21 (`21_Validate Polymerization Zone.asfp`)
only tests `ZoneSize(...) < 1` for the four supplied zones. It is an emptiness
check, not a hardware-type validator.

### Architectural consequence

Keep two concepts separate: a device contract describes supported operations,
while a Zone selects an ordered set of wells/locations. A Zone is not a Python
device instance, a hardware type, or just a string field substituted into XML.
Runtime Zone support is therefore an addition through DSL types, IR values,
function bindings and target addressing, not a one-line change to the serializer.

Retain fixed deployment binding for procedures tied to known equipment. Add a
designed path for runtime location selection with a compatible device contract.
The concrete author API needs a separate proposal; no new signature is specified
or implemented by this audit.

For a closed set of zones and a known APP configuration, a target can check the
allowed equipment in advance. For an arbitrary runtime Zone, compilation cannot
know its actual contents. It needs a validated caller contract, a constrained
selection, or a supported runtime check/failure path. The compiler must not claim
static hardware validation for an unconstrained input.

Dynamic selection also affects saved configuration and start/stop: what happens
if the zone changes between configuration, start and stop; if it spans several
controllers; or if two logical slots select the same physical device? Device
specialization queries must describe the supported contract rather than pretend
to know an unknown runtime location. These questions are recorded as
[QA-006 and QA-007](../../docs/refactor/device-abstraction/qa.md), for later joint
confirmation rather than immediate interruption of the user.

## Recommended development order and evidence collection

1. Design runtime locations and validation (A03), alongside text and the required
   quantities (A01/A02). Keep the existing high-level device configuration/start/
   stop intent; do not replace it with raw AutoSuite task names.
2. Implement a bounded recipe path: CSV import, list construction and explicit
   I/O outcomes (A05 and the necessary B01 subset). Verify F28 against the retained
   recipe. Then add row logging/export and well metadata (A06/A07).
3. Add sequential zones, waits/timers and diagnostic output (A04/A08–A12), each
   with its own semantic contract. A Wait is not an agitation duration property.
4. Port the pure capacity/chunk calculation from F31 with volume types. Use it to
   test the model before adding the concrete needle/diluter adapters and full
   dynamic-transfer procedure (B03).
5. Add Application/global/error handling and additional hardware profiles when
   the corresponding lifecycle and device contracts are confirmed (B02/B04–B08).

Useful next material to obtain, grouped for one discussion with experimenters:

- A minimal Zone-input Stir function plus two callers using different compatible
  zones, and a caller using an incompatible/empty zone; retain the APP device
  tree and observed Editor/Executor outcomes. Include a zone spanning multiple
  wells/controllers to establish the intended first supported scope.
- Small CSV probes with input files, expected output files, task result codes
  and one changed option per export. Include string escaping, units and defaults.
- A device/profile table linking zones, wells, racks/blocks and controlling
  devices, plus parameter ranges and hardware manuals for the desired operations.
- Minimal application event/global-state probes and a deliberate task fault;
  establish event IDs/order and state after normal return versus abort.
- The actual external helpers and their documented interfaces for analytical
  instrument integration, if those workflows are next in scope.

Use three separate acceptance records: semantic/reference execution, static
XML/re-export comparison, and Executor simulation on the configured system.
Physical process validation remains an additional instrument-specific activity.
Never infer it from generated XML or the SciLoom interpreter.

## Appendix: observed task families

Counts are occurrences in all 58 standalone ASFPs, 68 APPs and 52 extracted
function files, respectively. Repeated snapshots, calls and disabled tasks are
included. Every type below has prefix `Chemspeed.` and suffix `.1` in this scan.
“Partial” means the production compiler emits this type for its current subset.

| Type | ASFP | APP | Extracted | SciLoom emitter |
|---|---:|---:|---:|---|
| SAMacroTask | 622 | 10656 | 198 | Partial |
| SATaskCondition | 168 | 398 | 18 | Partial |
| SATaskEventFunction | 10 | 86 | 2 | — |
| SATaskExecuteFunction | 343 | 2707 | 105 | Partial |
| SATaskExecuteOperation | 229 | 5361 | 59 | — |
| SATaskExportCSV | 3 | 109 | 1 | — |
| SATaskFunctionDefinition | 242 | 1337 | 50 | Partial |
| SATaskGetProperty | 3 | 47 | 2 | — |
| SATaskImportCSV | 7 | 57 | 3 | — |
| SATaskInterrupt | 0 | 90 | 0 | — |
| SATaskLiquidTransfer | 80 | 3205 | 14 | — |
| SATaskLogData | 15 | 955 | 1 | — |
| SATaskManager | 0 | 68 | 0 | — |
| SATaskPeripheralTemperature | 0 | 142 | 0 | — |
| SATaskRunExecutable | 27 | 208 | 5 | — |
| SATaskSetAgitation | 22 | 1499 | 2 | Partial |
| SATaskSetElectricalContact | 0 | 536 | 0 | — |
| SATaskSetProperty | 2 | 42 | 2 | — |
| SATaskSetReactionBlockState | 78 | 2417 | 10 | — |
| SATaskSetReflux | 4 | 161 | 0 | — |
| SATaskSetTemperature | 16 | 596 | 0 | — |
| SATaskSetTimer | 28 | 455 | 2 | — |
| SATaskSetVacuum | 11 | 691 | 2 | — |
| SATaskSetVariable | 425 | 3050 | 118 | Partial |
| SATaskSolidTransfer | 0 | 260 | 0 | — |
| SATaskUserDialog | 48 | 1320 | 7 | — |
| SATaskWait | 83 | 4233 | 16 | — |

The 52 extracted files comprise 50 ordinary function definitions and two event
functions. Execute Operation also carries distinct operation IDs/signatures
inside a single component type; counting it once does not imply one missing
hardware operation. Blank placeholder operations are not usable evidence.

### Source key

All Fxx references are under `autosuite/corpus/extracted/latest_app/functions/`.
The original spelling of names is preserved.

| Key | Filename |
|---|---|
| F01 | `01_util Make Csv.asfp` |
| F04–06 | `04_N2 Open.asfp`; `05_N2 Closed.asfp`; `06_N2 Control.asfp` |
| F07–08 | `07_EVENT_type_2_7.asfp`; `08_EVENT_type_5_8.asfp` |
| F11/F13/F14 | `11_Run MALS.asfp`; `13_Run GPC Analysis.asfp`; `14_Run HPLC.asfp` |
| F15 | `15_util Get Time Stamp.asfp` |
| F16–20 | `16_Mix With Needle2.asfp`; `17_Dilute and Mix.asfp`; `18_Priming 1st 2nd Syringe.asfp`; `19_Purge Reactor.asfp`; `20_Test Reactor Valve.asfp` |
| F21 | `21_Validate Polymerization Zone.asfp` |
| F23/F24 | `23_Prepare GPC Sample.asfp`; `24_Sample and Run GPC.asfp` |
| F25 | `25_Import Csv Header.asfp` |
| F28/F29 | `28_Load Reagent Table.asfp`; `29_Load Reagent.asfp` |
| F30/F31 | `30_Dynamic Transfer Volumectrically.asfp`; `31_Get Aspirate Chunk.asfp` |
| F32 | `32_Throw Error.asfp` |
| F33–36 | `33_Get Parent Element Name.asfp`; `34_Get Single Well ID.asfp`; `35_Get ISynth Drawer Index.asfp`; `36_Check Well Interlock.asfp` |
| F37–40 | `37_Aspirate From Source.asfp`; `38__Aspirate.asfp`; `39__Dispense.asfp`; `40_Dispense To Destination.asfp` |
| F41/F42 | `41_Set ISynth Drawer Valve.asfp`; `42_Dispense Chunk.asfp` |
| F43/F44 | `43_Get Well Zone With Index.asfp`; `44_Set ISynth Drawer State.asfp` |
| F45/F46 | `45_Write Well Log.asfp`; `46_Export Wells Log.asfp` |
| F47/F48 | `47_Report Error.asfp`; `48_Zone Resolv.asfp` |
| F49/F50 | `49_Syringe Capasity.asfp`; `50_Label sample ID.asfp` |
