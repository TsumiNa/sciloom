# Fixed heating: native capture procedure and compiler gate

**Code: core/reference implemented; native profile gated. Native status: pending.**
R5.3 supplies this measurement procedure, not a hardware profile or an Executor
result. `Heater`, temperature values and lifecycle events are available in core.
AutoSuite still rejects thermal encoding and heater commands. There is no public
thermal profile constructor, native bypass or inferred conversion constant.

## Evidence actually available

The primary read-only `autosuite/corpus/app/config20260909_polymerization.app`
has SHA-256 `757854f4fc7c33ce8c14b02003a97d78263c34e8c5154638bd1a0d8e3b1bbcf5`.
Its application root declares product `2.47.1.1`, configuration `Swing XL Isynth`
and timestamp `2026-09-09T14:37:26+09:00`. Those facts identify this file, not every
installation with a similarly named zone.

It contains eight `Chemspeed.SATaskSetTemperature.1` tasks. All have
`internalcontrol=0`, `temperatureunit=°C`, `gradientunit=°C/min` and `Gradient=0`.
Do not infer the meaning of zero gradient or the control-mode enum from labels.

| Task ID | Observed payload | What it does not prove |
| --- | --- | --- |
| `{A6161A56-A9F6-42B2-852D-EEC91CD67D52}` | Zone Sampling1-1; switchon=1; maxwaittime=0; progid Chemspeed.SADeviceThermostat.1; deviceid 0.1; wellid=-1; Temperature=393.16 | Exact entered temperature, live range, gradient behavior or Executor acceptance |
| `{000F161C-24AA-4FF2-97A6-F23A77D9A67C}` | Same zone/controller; switchon=0; maxwaittime=0; Temperature=293.16 | That the inactive temperature field is a new applied setpoint or that stop preserves device settings |
| `{64CDB9F8-1730-44CD-AB38-3B16CA417AD2}` | Zone reactor_zone; Temperature=initial_temp; maxwaittime=0 | Controller resolution or execution |
| `{E46264E3-C349-48B9-8C78-4155DDE4A114}` | Zone reactor_zone; Temperature=initial_temp; maxwaittime=1800 | Controller resolution or waiting semantics |
| `{D7495915-669B-43BA-A90E-1E62728E4211}` | Zone reactor_zone; Temperature=reaction_temp; maxwaittime=1800 | Controller resolution or waiting semantics |
| `{D44AB057-461D-4BDA-A9DC-E394409764EF}` | Zone reactor_zone; Temperature=initial_temp; maxwaittime=0 | Controller resolution or execution |
| `{16AA99A3-618A-41C7-850A-93E6874ECE30}` | Zone reactor_zone; Temperature=initial_temp; maxwaittime=1800 | Controller resolution or waiting semantics |
| `{D1BBE4A1-90B3-49FC-A9DE-2D4FEB02F69F}` | Zone reactor_zone; Temperature=reaction_temp; maxwaittime=1800 | Controller resolution or waiting semantics |

The six reactor_zone tasks all have switchon=1, blank progid/deviceid and
wellid=-1. Their shared zero-gradient, mode and unit fields are recorded above.
Repeated payloads still have distinct task IDs; no function ownership is inferred.

The [Editor archive](34_EDITOR_SCREENSHOT_EVIDENCE.md) separately shows 20°C/50°C
associated with 293.16/323.16. Its APP/product profile is not supplied. Neither
source establishes a portable 273.16 offset. Core absolute temperature remains
standard SI: 0°C = 273.15 K; a temperature difference has no absolute offset.
The representative SetTemperature template is historical evidence, subordinate
to the primary APP; it cannot supply missing precision or nonzero-rate behavior.

## Prepare a valid native baseline

Use a disposable copy of a valid APP on the AutoSuite host. Preserve the original
received APP and every native export unchanged; work outside corpus. This stage
does not require or authorize physical instrument execution. Start with Editor
serialization and Executor simulation. Instrument accuracy is a separate claim.

Record the installed component's native tree path, controller type/ID, associated
wells, driver/version, selected internal/external control mode, displayed limits
and settings. Keep the original APP and screenshots that establish those facts.
Trace colocated stirring and heating to their actual distinct components; a
shared zone is neither an identity collision nor proof of independence. Reject
unsupported or ambiguous selections rather than inventing a family-prefixed ID.

Create a minimal Function with explicit native log markers around one Heat / Cool
task, and a host caller with `host.before` and `host.after`. Include no unrelated
device operation, missing subfunction or incomplete CSV task. Confirm that the
control imports and executes in simulation before measuring variants. Record APP
reset settings using the [deployment procedure](33_DEPLOYMENT_STATE_LIFETIME.md).
Shared-state experiments need a compatible reset setting; a failed deployment
precondition must not be mistaken for a thermal failure.

## Precision and profile matrix

Create each variant through Editor, using exact typed input rather than dragging
a slider. Save the original native ASFP, close/reopen, export it again, and retain
the corresponding APP. Record entered text, displayed text after reopening,
active/disabled fields, units, native task IDs and exact serialized expressions.
Never round the payload or manually change XML to make it fit an expectation.

| Case | Explicit Editor input / action | Required comparison |
| --- | --- | --- |
| T0 / T20 / T50 | 0, 20, 50°C with the same supported nonzero gradient | Absolute offset, scale and precision across three points |
| Tnegative | -10°C if the selected profile accepts it; otherwise record refusal | Negative input behavior; do not extrapolate beyond the accepted profile |
| Tprecision | 20.125°C or the closest representable input, recording any rounding | UI quantization versus stored precision and repeat-export stability |
| G1 / G2 | 1 and 2°C/min at the same accepted setpoint | Rate scale, units and nonzero behavior, separately from absolute temperature |
| Gzero / Gnegative | 0 and -1°C/min entered in Editor | Acceptance/refusal and documented meaning; never assume zero means immediate or unlimited |
| SwitchOff | Explicit stop with the same selected controller | Which fields are inactive and whether disabling changes the retained settings |
| Mode / range | Each proposed supported mode and exact lower/upper limits, then values just outside them | Native mode mapping and rejection/clamping; retain each result rather than broaden support |

If a profile refuses a required point, retain the refusal and collect that point
only on another explicitly identified compatible profile. Do not execute rejected
values or combine measurements from different controllers into a single profile.
Temperature and gradient use separate mappings. Variable defaults, literal task
values and variable-reference task values each need a measured round trip before
supporting that form; one correct literal does not prove all expression encoding.

## Lifecycle and order matrix

After a successful baseline, run distinct native Functions for these cases. Use
accepted settings from the measured profile. Keep each case's complete ordered
trace, not only a final success code. Re-export before execution.

| Case | Native procedure | Required observation |
| --- | --- | --- |
| Start / wait / stop | start.before → explicit start → start.after → fixed wait → wait.after → explicit stop → stop.after | Correct controller, setpoint and gradient applied; ordered continuation; stop disables. Fixed wait is not arrival at temperature. |
| Reapply | Start with A; retain configuration B in runtime values; log before a second explicit start; then start B | No native command applies B merely because its backing variables changed; second start uses the complete B configuration |
| Stop / restart | Start A → stop → start A again with the saved values | Stop preserves the semantic saved configuration; no implicit reset or hidden default |
| Shared child / loop | Configure in caller, start in a shared child, change one property, call again; repeat through a loop | Both captured properties survive private call transport and the intended APP reset policy |
| Independent child | Two independent logical heaters bound to distinct physical components | No cross-instance configuration or actuator interference |
| Colocated stir / heat | Explicitly identified distinct stir and thermal components share wells | Both tasks retain the correct component identity and independent settings |
| Invalid setting / controller | Native rejection cases captured separately from successful controls | No subsequent device action or caller continuation may be claimed fatal without the failure-propagation evidence |

The current compiler cannot generate a native heater candidate. Build these
minimal measurements in Editor. When an evidenced adapter is proposed later,
repeat the matrix with generated output and compare its native re-export with
these originals. Do not describe this preparatory matrix as a generated probe
suite or modify a gated target to emit candidates.

Run each valid simulation APP with the established host command, substituting its
actual filename and retaining the exact argv and working directory:

```bat
AutoSuiteExecutor.exe thermal-probe.app /r /sim 100 /s /c
```

Simulation demonstrates native task acceptance and observable control flow; it
does not prove physical temperature, heating rate, sensor accuracy or settling.
If simulation cannot observe a setting or effect, mark it inconclusive. Reuse the
existing [failure probes](24_RUNTIME_FAILURE_GATE.md) for fault propagation;
do not infer child/loop/caller termination from a single thermal error message.

## Receipt and narrow unlock decision

For each case preserve the following in the team's normal received-evidence
tree, with relative paths and SHA-256 hashes recorded in the measurement notes:

1. Original APP/ASFP and Editor re-export, product/profile/driver versions,
   component tree/identity, mode, units, ranges and reset setting.
2. Exact input texts and operator actions, screenshots of active controls and
   reopened values, complete task payloads and IDs, and any refusals or rounding.
3. Executor command, working directory, exit code, raw logs, ordered markers,
   observed controller/settings and actual outcome; explicitly distinguish an
   unobserved value from zero or success. Record run order and retained state.
4. For later generated candidates, clean source commit, lockstep package versions,
   generation command and generated hashes, plus the original native comparison
   files. A generated candidate is never an original vendor export.

The existing receipt validator accepts failure/CSV suites only. It does not
validate this thermal matrix; do not relabel these measurements to obtain a
success result. No machine-readable file enables the compiler. Review association,
controls, precision and behavior using the existing evidence hierarchy.

Only after evidence is sufficient may an unlock PR define the exact immutable
profile constructor and binding example in the [authority](../../docs/refactor/autosuite-expansion/01-contract.md#native-profile-entry-gate--r53),
then implement a typed payload adapter. Limit support to the measured profile,
mode, expression forms and ranges. Preserve standard core SI and make any proven
vendor conversion explicit in that adapter. Retain all unproven gates, including
dynamic selection and runtime checks dependent on fatal propagation. If preserving
the accepted semantics requires changed lifetime, implicit start, discarded
configuration or error continuation, stop for the plan's class D decision.

## Current reproducible checks

The existing source/IR examples and gate tests are runnable without native access:

```console
uv run python examples/warm_sample.py
uv run python -m examples.developer.warm_sample_ir
uv run pytest src/sciloom/core/interpreter/device_state_heating_test.py packages/sciloom-autosuite/src/sciloom_autosuite/codegen_temperature_test.py
uv run python autosuite/tools/audit_corpus.py
```

The author example reports the missing native profile; the reference example
reports 10 virtual seconds, a disabled heater and a retained 293.15 K target.
The tests verify logical semantics and explicit native rejection. None ran
Executor. Q6, Q7 and Q9 remain pending until actual receipts are reviewed.
