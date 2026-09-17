# Authoritative expansion interface and behavior contract

## Status and invariants

All interfaces introduced here are **planned**, not currently importable unless
explicitly called current. Availability is tied to the named PR and its merge,
not to presence of these examples. Reassess under
[execution rules](02-execution-rules.md) before implementing each section.

Keep existing author APIs, JSON v4 shapes, dedicated agitation nodes and Target
protocol. Core never imports author device implementations or AutoSuite.
Each addition is handled or explicitly rejected by every consumer in its PR.
Vendor restrictions stay in target validation; native proof is separate.

## R1: Deployment conditions and review artifacts

Current: AutoSuiteTarget(version=..., devices=..., layout=...) emits ASFP.
CompileResult contains original and specialized IR, target identity and Artifact;
its write method writes only the artifact. Keep these current behaviors.

### Planned after R1.1

Public imports from sciloom_autosuite:

- `AutoSuiteDeployment.from_app(path: str | Path) -> AutoSuiteDeployment`.
  Immutable facts: exact input-byte SHA-256, product version, configuration label
  if present, and `reset_variables: bool | None`. Missing reset information is
  unknown, never False. Reject malformed/ambiguous values and malformed APPs.
  A configuration label is not a fabricated globally unique APP identity.
- `AutoSuiteDeploymentStatus`: COMPATIBLE, INCOMPATIBLE, UNKNOWN.
- `AutoSuiteDeploymentReport`: typed immutable status, target identity,
  source hash when known, checked settings, ordered requirements/reasons with
  affected node identities, and separate native status. `to_json() -> str`
  emits deterministic report data, not a Program/v4 document.
- Add `app_sha256: str | None = None` to target-only AutoSuiteLayout.
  from_app computes it from the same exact input bytes as deployment reading;
  manually constructed layouts default to unknown provenance. Do not include
  provenance in semantic JSON, vendor XML or existing identity seeds.

### Planned after R1.2

`AutoSuiteTarget(..., deployment: AutoSuiteDeployment | None = None)`.
`target.deployment_report(program: Program) -> AutoSuiteDeploymentReport`
accepts validated, already-specialized IR. It performs no resolution,
specialization, file read or mutation. The compile path calls the same assessment
after specialization and rejects INCOMPATIBLE in target.validate.

Requirements initially cover every internal Var and saved device configuration
that can persist across calls. Conservatively require compatible reset behavior;
do not remove requirements based on speculative liveness analysis. Report exact
affected functions/resources and why they require persistent state.

A supplied, unsupported product version or conflicting known layout/APP hashes
is incompatible. An unknown hash/settings/profile is unknown, not compatible.
Known reset-enabled APPs are incompatible for persistent-state programs; reset
settings do not obstruct programs without that requirement. COMPATIBLE certifies
only these checked conditions, never Executor acceptance.

Retain offline ASFP generation with UNKNOWN deployment status. Supply a
target-owned review exporter with this planned signature:

```python
from pathlib import Path

from sciloom.core.compiler import CompileResult
from sciloom_autosuite import AutoSuiteDeploymentReport, AutoSuiteTarget

def write_autosuite_review(
    result: CompileResult,
    *,
    target: AutoSuiteTarget,
    path: str | Path,
) -> AutoSuiteDeploymentReport:
    ...
```

The exporter writes the ASFP and a same-base `.deployment.json` sidecar.
Report the actual artifact SHA-256 and the canonical specialized Program digest
along with deployment facts. Validate the target identity and selected bindings
against the result and verify that this target's validated deterministic emission
matches the supplied artifact before writing; reject mismatches rather than
attaching a report for another deployment. This is an export utility, not a
second compiler or a mutable target cache. It must not re-resolve the authored
Program, introduce an implicit specialization or change CompileResult.write.
Do not promise atomic multi-file writes; report IO failure normally.

Planned usage after R1.2 (requires a known compatible APP):

```python
from sciloom import Function, Input, Output, Var, runtime
from sciloom_autosuite import (
    AutoSuiteDeployment,
    AutoSuiteLayout,
    AutoSuiteTarget,
    write_autosuite_review,
)

class Accumulator(Function):
    amount: Input[int]
    total: Var[int] = 0
    result: Output[int]

    @runtime
    def run(self) -> None:
        self.total += self.amount
        self.result = self.total

deployment = AutoSuiteDeployment.from_app("compatible.app")
layout = AutoSuiteLayout.from_app("compatible.app")
target = AutoSuiteTarget(deployment=deployment, layout=layout)
compiled = Accumulator().compile(target=target)
report = write_autosuite_review(compiled, target=target, path="accumulator.asfp")
```

Expected: reference session with two amount=1 calls returns 1, then 2.
Known reset-enabled APP: compilation rejects. No deployment: ASFP plus UNKNOWN
report, native status pending. No APP settings are edited. Original Var lifetime
and snapshot behavior are unchanged.

## R2: Evidence and native unlocking

Reuse existing generators and manifest fields; extend only where a receipt lacks
a fact needed for acceptance. Receipt validation is tooling, not a runtime
capability-discovery or bypass system. A caller-supplied receipt cannot change
AutoSuiteTarget's support set.

Failure, CSV literal conversion, per-column status aggregation, append encoding,
append preservation and fault propagation are independently verified claims.
Record exact case coverage and limits. Unlock only the proven version/profile
and retain rejection for other variants. Class D escalation applies if native
behavior cannot preserve the agreed core semantics.

## R3: Ordered text and yes/no results

### Author API — planned after R3.1

```python
from sciloom import Duration

def request_text(message: str, *, timeout: Duration | None = None) -> str:
    ...

def ask_yes_no(message: str, *, timeout: Duration | None = None) -> bool:
    ...
```

These are runtime markers, lazily exported from sciloom with implementation
ownership in flow. Only a whole assignment RHS is supported. Destination is an
existing declared text/bool runtime field. No tuple unpacking, nested invocation,
ordinary-expression getter, implicit host prompt or discarded result.

Message evaluates once, then timeout once; validate before consuming a response.
None means no timeout; a supplied duration is finite and positive. Deadline
expiry terminates, with no default result. Empty text is valid; No returns False.
Cancel, Stop, timeout and missing/exhausted service terminate execution. Failed
interaction leaves destination unchanged and emits no later task effects.

New ordered statements `RequestText` and `AskYesNo` carry target Reference,
message Expression and optional timeout Expression. Add their own stable kinds;
do not add result fields to existing Notify. Timeout is represented explicitly
as null or a Duration expression in these new records. Reference response events
capture the request, outcome and successful value as immutable records; report
consumed failed outcomes before raising, but no consumed-response event for
invalid arguments or absent/exhausted service.

### Reference service — planned after R3.1

Public imports from sciloom.core.interpreter:
`QueuedDialogResponses`, `DialogResponse`, `DialogOutcome`.
Use distinct outcome values ACCEPTED, CANCELLED, STOPPED, TIMED_OUT.
A DialogResponse holds outcome, optional str/bool value and nonnegative Duration
elapsed. Accepted text/bool must match the operation; non-accepted has no value.
An explicit elapsed time reaching/exceeding timeout terminates, even if a late
accepted value is supplied. Do not sleep, sample host time, or advance an unrelated
virtual clock implicitly. ReferenceEnvironment gains optional `dialogs`.

```python
from sciloom import Function, Output, ask_yes_no, request_text, runtime, s
from sciloom.core.interpreter import (
    DialogOutcome,
    DialogResponse,
    Interpreter,
    QueuedDialogResponses,
    ReferenceEnvironment,
)

class IdentifySample(Function):
    barcode: Output[str]
    accepted: Output[bool]

    @runtime
    def run(self) -> None:
        self.barcode = request_text("Scan barcode", timeout=30 * s)
        self.accepted = ask_yes_no("Use this sample?")

environment = ReferenceEnvironment(dialogs=QueuedDialogResponses((
    DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001", elapsed=2 * s),
    DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False, elapsed=1 * s),
)))
result = Interpreter(IdentifySample().to_ir(), environment=environment).run()
# Expected outputs: {"barcode": "S-001", "accepted": False}.
```

Do not merge existing QueuedAcknowledgements into the new service or change
Notify semantics. Reference response allocation/shared environment rules follow
existing explicit services. Exact exception diagnostics distinguish missing
service, invalid response, cancel, stop and timeout.

### AutoSuite availability — R3.2

Native mapping requires valid result-bearing dialog exports and acceptance of
normal/No/cancel/Stop/timeout paths. Keep unsupported variants rejected until
proven. A timeout-answer text is not an equivalent implementation of fatal
timeout. Native probes may be generated as measurement artifacts while public
compilation remains gated. Do not silently reduce the API to a weaker policy.

## R4: Explicit command effects and typed configuration

### Additive device contract — planned after R4.1

Keep existing CommandContract and DeviceCommand fields unchanged. Extend the
typed operations union with `LifecycleCommandContract`, a new wire kind carrying
semantic_id, name, typed parameters, required_configuration property IDs and a
`LifecycleEffect` value: APPLY_AND_ENABLE or DISABLE.

The effect wire values are `apply_and_enable` and `disable` respectively.
APPLY_AND_ENABLE requires and snapshots complete required configuration and
enables/reapplies. DISABLE disables, preserving saved/applied configuration.
Reference execution of a trusted matching lifecycle contract is defined; an
ordinary unknown native DeviceCommand remains rejected. Do not infer effects
from start/stop method names. Old agitation still uses its dedicated nodes and
unchanged serialized contracts.

Extend the existing author decorator without changing its default behavior:

```python
from collections.abc import Callable
from typing import ParamSpec
from sciloom.core.ir import LifecycleEffect

P = ParamSpec("P")

def operation(
    *,
    id: str,
    lifecycle: LifecycleEffect | None = None,
    requires: tuple[str, ...] = (),
) -> Callable[[Callable[P, None]], Callable[P, None]]:
    ...
```

The decorator preserves the current wrapped method's parameter types.
requires contains author property names resolved to semantic IDs. An applying
command requires the union of its explicit requires and the owning device's
required_configuration. A disabling command has no implicit configuration
requirement. Using requires without lifecycle is rejected in this first version.
Ordinary operations keep the exact old contract shape.

A claimed lifecycle contract is validated against the supplied trusted binding
where supplied, just like other device contracts; IDs never import code.
The effect only specifies logical state, not measured physical success.

### Contributor example — planned after R4.1

A contributor extends a family, adds a property and explicit lifecycle command;
it does not patch BaseDevice or Agitator:

```python
from typing import ClassVar
from sciloom.core.ir import LifecycleEffect
from sciloom.devices import Agitator, operation

class AdjustableAgitator(Agitator):
    device_type_id: ClassVar[str] = "example.adjustable-agitator/v1"
    required_configuration: ClassVar[tuple[str, ...]] = ("speed", "gain")

    @property
    def gain(self) -> float:
        raise TypeError("Runtime configuration is write-only.")

    @gain.setter
    @operation(id="example.adjustable-agitator.gain/v1")
    def gain(self, value: float) -> None:
        ...

    @operation(
        id="example.adjustable-agitator.apply/v1",
        lifecycle=LifecycleEffect.APPLY_AND_ENABLE,
    )
    def apply(self) -> None:
        ...

class BenchAgitator(AdjustableAgitator):
    device_type_id: ClassVar[str] = "example.bench-agitator/v1"
    writable_properties = ("speed", "gain")
    supported_operations = (
        Agitator.start,
        Agitator.stop,
        AdjustableAgitator.apply,
    )
```

A minimal independent recording target remains possible without modifying core
or installing a plugin (complete planned contributor example):

```python
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import Program, to_json
from sciloom.devices.declarations import bind_device

class RecordingTarget:
    target_id = "example.recording/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(devices=(
            bind_device(
                logical_id="agitator",
                device=BenchAgitator(),
                physical_id="bench-actuator-1",
            ),
        ))

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()

    def emit(self, program: Program) -> Artifact:
        return Artifact(
            content=to_json(program).encode("utf-8"),
            media_type="application/json",
            suffix=".json",
        )
```

This target records validated intent, not AutoSuite XML or instrument I/O.
Tests must include ConfigureProperty(speed), ConfigureProperty(gain), apply and
a changed gain followed by apply; verify complete captured/applied snapshots and
a JSON-restored program. Unknown ordinary commands still fail reference execution.

### AutoSuite configuration — planned after R4.2

Key saved backend state by (resource_id, property semantic ID), retaining typed
values and call transport. Keep all private context variables out of Program.
Generalization must preserve existing agitation ASFP bytes and identity seeds;
a required serialization behavior change triggers class D review first.

Use explicit typed dispatch for supported profiles/tasks, not a generic dict or
discovery registry. Do not publish a new profile plugin protocol merely to wrap
one implementation. R5.3's real second profile validates the needed shared seam;
its concrete constructor must be specified here after profile evidence is obtained
and before that implementation begins.

Conflict identity is an installed physical actuator, not a well-zone name or
bare vendor device number. Separate controllers may share a zone; the same
actuator cannot be bound twice. Preserve current shaker ancestry checks and
physical-identity spelling for existing profiles. Do not fake independence by
adding a family prefix without installed-component evidence.

## R5: Physical temperature and a fixed thermal family

### Quantity API — planned after R5.1

Lazy author imports from sciloom:
`Temperature`, `TemperatureDifference`, `TemperatureRate`,
`degC`, `kelvin`, `delta_degC`, `delta_kelvin`, `degC_per_min`,
`kelvin_per_s`.

Canonical immutable constructors:
`Temperature(kelvin: float)`,
`TemperatureDifference(kelvin: float)`,
`TemperatureRate(kelvin_per_second: float)`.
All reject bool/nonfinite values; absolute temperature rejects values below zero
kelvin. Difference/rate can be signed in core; device limits belong to profiles.
Constructing a Celsius literal uses the standard offset 273.15, never a vendor
offset. A unit literal such as 20 * degC constructs a temperature, not scaling
an existing absolute temperature.

Supported operations: same-type comparison/assignment; absolute − absolute →
difference; absolute ± difference → absolute; difference + absolute → absolute;
difference arithmetic and numeric scaling; rate arithmetic and numeric scaling.
No absolute + absolute or arbitrary scaling of absolute values. No new
cross-dimension multiplication/division algebra is promised in this stage.
Add scalar values `temperature`, `temperature_difference`, `temperature_rate`,
typed list support and all-consumer handling; unsupported
AutoSuite uses get explicit diagnostics until mapped.

```python
from sciloom import Temperature, degC, delta_degC

initial = 20 * degC
target = initial + 5 * delta_degC
assert target == Temperature(kelvin=298.15)
# Illustrative mathematical result: target - initial is a 5 K difference.
```

Validate floating results with existing numerical conventions, not cross-vendor
bit-identical physical claims. Runtime examples cover declared Input/Output/Var
and JSON as well as these host values.

### Heater author family — planned after R5.2

`from sciloom import Heater`; family ownership in sciloom.devices.
Write-only properties temperature: Temperature and ramp_rate: TemperatureRate;
both must be configured before start. Explicit start applies the complete saved
configuration; explicit stop retains it. Native zero-rate semantics and accepted
ranges are profile evidence, not generic defaults.

Use new lifecycle contracts with ConfigureProperty/DeviceCommand, not
device-model-specific IR nodes. No getter, automatic stop at scope exit, dynamic
thermal selection, feedback or implied reach-temperature.

```python
from sciloom import Function, Heater, degC, degC_per_min, runtime, s, wait

class WarmSample(Function):
    heater: Heater

    @runtime
    def run(self) -> None:
        self.heater.temperature = 20 * degC
        self.heater.ramp_rate = 1 * degC_per_min
        self.heater.start()
        wait(10 * s)
        self.heater.stop()
```

After R5.2 this converts to IR/JSON and reference state/events. The numbers
illustrate syntax, not a process recipe. Ten seconds does not mean temperature
was reached. AutoSuite support remains gated until R5.3's exact mapping is proven.

### Native profile entry gate — R5.3

Before implementing a profile constructor, obtain a valid original export,
installed controller identity/mode/ranges and precision-preserving temperature/
gradient measurements. Update this contract with its exact immutable dataclass
constructor and a runnable binding example. The supplied incomplete test.asfp
does not justify inventing them. If evidence is absent, R5.3 may land diagnostic/
probe/documentation work with native emission rejected; do not publish a fake
unusable hardware profile. Keep Q6–Q9 pending.

## R6: Location arguments and bounded transfer

### Parameters and quantities — planned after R6.1

Expand CommandParameter.type to the existing ValueType union including ZoneType.
Existing scalar/list contracts encode identically. PropertyContract remains
scalar/list; no arbitrary records, nested lists or object parameters.
Capture a Zone as the existing immutable ordered unique well value.

Add FlowRate(m3_per_second: float) and Length(metres: float), plus author unit
literals `mL_per_min`, `m3_per_s`, `mm`, `metre`. Core quantities are finite
and signed; an operation/profile imposes positive flow and valid position limits.
Include like-dimension arithmetic/comparison and numeric scaling, using existing
quantity conventions. Do not add mass/pressure or broad dimension inference.
Their ScalarType wire values are `flow_rate` and `length` respectively; canonical
JSON literal numbers are m3/s and metres, with no display-unit field added to
existing literals.

### LiquidHandler family — planned after R6.2

Lazy author import `LiquidHandler`, owned by sciloom.devices. Write-only
configuration properties: aspirate_flow: FlowRate, dispense_flow: FlowRate,
air_gap: Volume. All are required explicitly; no hidden values from screenshots.

```python
from sciloom import Volume, Zone
from sciloom.devices import BaseDevice, operation

class LiquidHandler(BaseDevice):
    # Method-signature excerpt; required property declarations are specified above.
    device_type_id = "sciloom.liquid-handler/v1"

    @operation(id="sciloom.liquid-handler.transfer/v1")
    def transfer(self, source: Zone, destination: Zone, volume: Volume) -> None:
        ...
```

This is an instance device operation, not a global flow helper. It lowers to
DeviceCommand with its registered semantic ID and named typed arguments.
Transfer is a known ordered effect, not an applying start/stop lifecycle command.
Core recognizes its defined family semantics without importing the author class;
unknown ordinary operation IDs remain rejected. No fake enable/disable transition.

```python
from sciloom import (
    Function, Input, LiquidHandler, Volume, Zone, mL, mL_per_min, runtime,
)

class TransferOne(Function):
    liquid: LiquidHandler
    source: Input[Zone]
    destination: Input[Zone]
    amount: Input[Volume]

    @runtime
    def run(self) -> None:
        self.liquid.aspirate_flow = 1 * mL_per_min
        self.liquid.dispense_flow = 1 * mL_per_min
        self.liquid.air_gap = 0.01 * mL
        self.liquid.transfer(self.source, self.destination, self.amount)
```

After R6.2 this has reference semantics with explicit locations/bindings and
compatible trusted limits. AutoSuite initially requires statically proven named
single-well selections/parameters; this runtime-input form remains rejected
there until its checks have native proof. Provide a separate statically bound
author example when R6.3's profile is established, rather than falsely marking
this reference example as natively compilable.

Transfer captures source, destination and volume once in declaration order,
then snapshots its saved flow/air-gap configuration. Source and destination
must each be one known well and distinct. Volume and both flows must be positive;
air gap nonnegative. Validate allowed locations/tool capacity before any action.
A nonempty Zone spanning resources does not become a DeviceAt selection.

Reference acceptance requires explicit trusted transfer deployment facts:
physical actuator, allowed source/destination well sets and effective usable
capacity. Carry these in a target-neutral `TransferDeviceBinding` outside Program:
`binding: DeviceBinding`, `source_wells: Zone`, `destination_wells: Zone`,
`usable_capacity: Volume`. Require positive capacity and known allowed wells;
include it explicitly in DeviceBindings and every binding consumer. Introduce
this additive record rather than expanding existing
DeviceBinding's serialized contract or granting authority from user JSON.
Profile calibration/route feasibility must already be validated when producing
these facts. Requested volume plus air gap must not exceed the supplied usable
capacity. No implicit chunking, defaults or host equipment access.

A completed reference TransferEvent captures source/destination/volume,
configuration and physical identity. It records intent, not measured liquid
movement; it does not invent a mutable physical inventory. Failed preconditions
produce no transfer event or later action. No automatic recovery or retries.

### Native profile entry gate — R6.3

First profile: fixed tool, one explicit channel, exactly one source/destination
pair per operation. Tool/calibration/channel, needle/position policy and rinse
route/policy must be explicit validated deployment fields. Length supports those
position fields, not an invented universal needle-depth author API.

Before implementation, obtain a minimal valid export and complete its exact
typed constructor/binding example here. Never implicitly disable rinse, select
all channels or guess a tool/range from inactive fields. Keep native generation
gated if necessary evidence or runtime failure behavior is missing. Multi-row
packing, dynamic routes, split volumes and gravimetric feedback stay deferred.

## R7: Integrated results

Publish runnable source examples and developer direct-IR/JSON counterparts for:
barcode → single-well metadata → log; configured heater → fixed wait → stop;
single-pair transfer → log. Supply explicit reference services and deployment
conditions. Each example shows actual supported layers, not a single ambiguous
"supported" flag. Do not hide native failures behind a recording target whose
JSON output is labeled ASFP.

Long actual outputs are same-base-name companions; planned snippets above are
not generated results. Include mixed old/new devices and cross-function state.
Unknown deployments, profiles and commands fail diagnostically.

## Version

Version: none, this document specifies planned APIs without adding shipped code.
Individual implementation plans select normal PATCH/MINOR outcomes after their
preflight and re-evaluate after final review; no breaking migration is authorized.
