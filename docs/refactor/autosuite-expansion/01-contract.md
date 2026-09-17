# Authoritative expansion interface and behavior contract

## Status and invariants

R1 facts/report records, layout provenance, target guards and review export are
**implemented** (R1.1 merged #104; R1.2 merged #105). R2.1 receipt tooling is
merged #106; R3.1 dialog semantics merged #107. R3.2 native measurement tooling
merged #108; R4.1/R4.2 merged #109/#110, R5.1–R5.3 merged #111–#113,
and R6.1 merged #114. R6.2 merged #115. R6.3 measurement documentation is implemented/gated in this PR, pending review/merge.
New AutoSuite dialog, thermal and transfer emission remains gated and native
acceptance pending.
Other interfaces introduced here are **planned**, not currently importable unless
explicitly called implemented. Availability is tied to the named PR and its merge,
not to presence of these examples. Reassess under
[execution rules](02-execution-rules.md) before implementing each section.

Keep existing author APIs, JSON v4 shapes, dedicated agitation nodes and Target
protocol. Core never imports author device implementations or AutoSuite.
Each addition is handled or explicitly rejected by every consumer in its PR.
Vendor restrictions stay in target validation; native proof is separate.

## R1: Deployment conditions and review artifacts

Current: AutoSuiteTarget(version=..., devices=..., layout=..., deployment=...)
emits ASFP when validation passes; missing deployment facts retain offline output.
CompileResult contains original and specialized IR, target identity and Artifact;
its write method writes only the artifact. Keep these current behaviors.

### Implemented in R1.1

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
  Its requirements and findings are immutable tuples of existing Diagnostic
  records; its native_status is always pending. The private shared assessment
  is shared by target validation and review export after R1.2.
- Add `app_sha256: str | None = None` to target-only AutoSuiteLayout.
  from_app computes it from the same exact input bytes as deployment reading;
  manually constructed layouts default to unknown provenance. Do not include
  provenance in semantic JSON, vendor XML or existing identity seeds.

### Implemented in R1.2

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
target-owned review exporter with this signature:

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

The result does not contain a separate physical-binding snapshot. Check its
specialized concrete resource contracts against target binding facts, then
compare full deterministic emission (including profile-dependent identities).
Reject remaining DeviceIf and invalid selected IR through existing validators.
The returned report carries optional artifact_sha256 and specialized_ir_sha256;
ordinary assessment leaves both None. Hash the exact artifact bytes and UTF-8
canonical to_json(specialized_ir), including supplied source metadata. Refuse an
output path equal to its sidecar path before writing either file.

Usage after R1.2 (requires a known compatible APP):

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

### Receipt tooling — implemented in R2.1

Checkout-only API (not a distributed author API):

```python
from pathlib import Path
from autosuite.tools.validate_native_receipt import ProbeSuite, validate_receipt

assessment = validate_receipt(
    manifest_path=Path("scratch/failure/manifest.json"),
    receipt_path=Path("received/failure/receipt.json"),
    suite=ProbeSuite.RUNTIME_FAILURE,
)
assert assessment.native_status == "pending_review"
```

Signature: validate_receipt(*, manifest_path: Path, receipt_path: Path,
suite: ProbeSuite) -> ReceiptAssessment. ProbeSuite has runtime_failure,
csv_read and csv_append values. ReceiptAssessment holds suite, source_commit,
product_version, profile, ordered case_names and constant native_status
pending_review. Invalid/incomplete/inconclusive receipts raise ValueError;
unreadable files raise OSError. No files are written. A successful check certifies
association/completeness only, never truth of human-recorded observations.

CLI: `uv run python -m autosuite.tools.validate_native_receipt --suite runtime_failure
--manifest scratch/failure/manifest.json --receipt received/failure/receipt.json`.
Exit 0 prints case count and pending_review; invalid receipts exit 2 with a reason.
The command requires actual host files; an example path is not a supplied receipt.

Receipt format 1 associates the exact manifest hash, source commit, package
versions, product version/profile and every generated case. Each run references
hashed original APP, native re-export, log and structured observations, with the
actual Executor argv and exit code. Observations record ordered markers, native
result/error, termination, values and notes. Failure controls require their full
successful sequence plus host.after. CSV cases require two runs and complete
before/after CSV byte files (null means absent), with original seeds and repeated
run continuity checked. Keep all native divergences visible for later review.
The exact receipt fields and host assembly example live in the AutoSuite receipt
reference added by R2.1; this tool does not synthesize observations.

Failure, CSV literal conversion, per-column status aggregation, append encoding,
append preservation and fault propagation are independently verified claims.
Record exact case coverage and limits. Unlock only the proven version/profile
and retain rejection for other variants. Class D escalation applies if native
behavior cannot preserve the agreed core semantics.

## R3: Ordered text and yes/no results

### Author API — implemented in R3.1

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

### Reference service — implemented in R3.1

Public imports from sciloom.core.interpreter:
`QueuedDialogResponses`, `DialogResponse`, `DialogOutcome`, `DialogEvent`.
Use distinct outcome values ACCEPTED, CANCELLED, STOPPED, TIMED_OUT.
A DialogResponse holds outcome, optional str/bool value and nonnegative Duration
elapsed. Accepted text/bool must match the operation; non-accepted has no value.
An explicit elapsed time reaching/exceeding timeout terminates, even if a late
accepted value is supplied. Do not sleep, sample host time, or advance an unrelated
virtual clock implicitly. ReferenceEnvironment gains optional `dialogs`.

Queue signature: QueuedDialogResponses(responses: Iterable[DialogResponse] = ()).
Its remaining property counts unused copied entries; respond() consumes exactly
one or raises LookupError when exhausted. Each frozen DialogResponse accepts
keyword-only outcome, value=None and elapsed=Duration(seconds=0). Accepted values
must be exactly str or bool; non-accepted responses must have value=None.

DialogEvent is a frozen record of node_id, source, operation (request_text or
ask_yes_no), message, timeout, outcome, elapsed, successful value and error_code.
A supplied accepted response at/after the deadline records TIMED_OUT with no
value. Wrong-type accepted responses record their ACCEPTED outcome, no successful
value and dialog_response_type. Other consumed failures record dialog_cancelled,
dialog_stopped or dialog_timeout. Exhaustion is dialog_response_required;
missing service uses the existing missing_environment_service diagnostic.
Invalid timeout is dialog_timeout_value. These failures preserve the destination
and existing prior effects, without executing following statements.

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

Runnable author declaration: examples/identify_sample.py. Its command verifies
the current AutoSuite rejection. The developer example
examples/developer/dialogs_ir.py executes this source and equivalent direct IR
with explicit responses, writes its complete JSON companion and checks outputs.

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

R3.2 measurement API (implemented in this PR):
`autosuite.tools.probe_dialog_results.generate(output_dir: Path, *,
source_asfp: Path, text_task_id: str, choice_task_id: str) -> Path` returns a
manifest path in a fresh directory outside corpus. It reads an explicit native
functions package and exact task IDs, requires the observed flat UserDialog
envelope and text/okstop or 1/0 yesnostop forms, and records exact source/payload
hashes. It never modifies the source or APP. It emits thirty native ASFP probes
with entry/child/loop marker controls and pending status. Text probes distinguish
normal, empty, window cancel, Stop and timeout. Choice probes distinguish Yes,
No, window cancel, Stop and timeout; they log the observed integer 1/0 encoding,
not a claimed portable bool result. Two loop iterations require two actions on
successful controls. Timeout candidates measure native continuation/defaults;
they do not implement the fatal semantic timeout contract. The host must record
the source product/profile version separately because ASFP may omit it.

CLI: `uv run python -m autosuite.tools.probe_dialog_results --source-asfp
received/test.asfp --text-task-id {A81CC6E9-0955-4426-8B55-B0BF65211699}
--choice-task-id {DCBC6267-E249-49AB-A45A-6326E5688DA8} --output-dir scratch/dialogs`.
IDs are explicit evidence selectors, not public author API or device bindings.
Native checks remain manual pending receipts; the existing failure/CSV receipt
validator must not certify this different interactive suite.

## R4: Explicit command effects and typed configuration

### Additive device contract — implemented in R4.1

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

The first two lifecycle effects are parameterless: the typed `parameters` field
must be empty. They apply saved properties or disable the resource; no argument
has a defined role in either effect. Declarations and direct IR with lifecycle
arguments are rejected rather than silently ignoring values. Ordinary commands
retain typed parameters, including the R6 transfer arguments.

A claimed lifecycle contract is validated against the supplied trusted binding
where supplied, just like other device contracts; IDs never import code.
The effect only specifies logical state, not measured physical success.

### Contributor example — runnable after R4.1

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
    required_configuration = ("speed", "gain")
    supported_operations = (
        Agitator.start,
        Agitator.stop,
        AdjustableAgitator.apply,
    )
```

A minimal independent recording target remains possible without modifying core
or installing a plugin (implemented contributor interface):

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
The complete runnable [contributor example](../../../examples/developer/lifecycle_commands.py)
also defines an explicit DISABLE command, checks capture before a variable change,
and commits its reproducible JSON companion. Run with
`uv run python -m examples.developer.lifecycle_commands`.

### AutoSuite configuration — implemented in R4.2

Key saved backend state by (resource_id, property semantic ID), retaining typed
values and call transport. Keep all private context variables out of Program.
Generalization must preserve existing agitation ASFP bytes and identity seeds;
a required serialization behavior change triggers class D review first.

Property storage retains the declared scalar/list type. Whole-list configuration
is copied on capture and private call transport uses separate input/output arrays
with copyback after normal return; no caller configuration array becomes an
aliased mutable argument. Allocation defaults never prove semantic configuration.
R4.2 generalizes capture and the existing agitation adapter; new lifecycle task
emission still requires R5's explicit profile evidence and remains rejected.

Use explicit typed dispatch for supported profiles/tasks, not a generic dict or
discovery registry. Do not publish a new profile plugin protocol merely to wrap
one implementation. A future evidence-backed thermal profile must validate the
needed shared seam; R5.3 delivered only capture documentation and did not establish
a second native profile. Specify its concrete constructor here after profile
evidence is obtained and before that implementation begins.

Conflict identity is an installed physical actuator, not a well-zone name or
bare vendor device number. Separate controllers may share a zone; the same
actuator cannot be bound twice. Preserve current shaker ancestry checks and
physical-identity spelling for existing profiles. Do not fake independence by
adding a family prefix without installed-component evidence.
Candidate well sets must remain disjoint within one logical selection so `at()`
chooses one controller. Different logical resources may share wells when their
trusted physical identities differ; all physical identity collisions still fail.

## R5: Physical temperature and a fixed thermal family

### Quantity API — implemented in R5.1, native encoding gated

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

R5.1 consumer boundary: absolute-unit construction is a numeric literal operation
in runtime source, not a general numeric-to-temperature cast. There is no
absolute-temperature ratio or division by an absolute unit. Signed differences
and rates support same-dimension ratios and division by their own unit, following
the existing quantity convention. No affine CSV read conversion is introduced:
all three thermal CSV column types are explicitly rejected in this stage, in
host descriptors and direct IR as well as source. Logging and CSV append preserve
canonical K / K/s values. AutoSuite rejects thermal scalar/list values until
exact native encodings and conversion behavior are established; no guessed
273.16 adjustment or generic real-number fallback is allowed.

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

Runnable author example: `uv run python examples/temperature_values.py` prints
298.15 K, 5 K and 1 K/s. `uv run python -m examples.developer.temperature_ir`
generates the complete JSON v4 companion and reference-executes the declared
Input/Output/Var fields twice, obtaining 5 K then 0 K changes. Direct IR tests
cover the same typed arithmetic and specialization without a Python frontend.
These examples do not claim native thermal control.

### Heater author family — implemented in R5.2, native profile gated

`from sciloom import Heater`; family ownership in sciloom.devices.
Write-only properties temperature: Temperature and ramp_rate: TemperatureRate;
both must be configured before start. Explicit start applies the complete saved
configuration; explicit stop retains it. Native zero-rate semantics and accepted
ranges are profile evidence, not generic defaults.

Use new lifecycle contracts with ConfigureProperty/DeviceCommand, not
device-model-specific IR nodes. No getter, automatic stop at scope exit, dynamic
thermal selection, feedback or implied reach-temperature.

Stable built-in contract IDs are `sciloom.heater/v1`,
`sciloom.heater.temperature/v1`, `sciloom.heater.ramp-rate/v1`,
`sciloom.heater.start/v1` and `sciloom.heater.stop/v1`. Start uses
`LifecycleCommandContract(APPLY_AND_ENABLE)` and stop uses `DISABLE`; device-wide
requirements are the two property IDs. Start also explicitly requires those
same two property IDs, so a derived profile cannot waive the family's mandatory
settings by narrowing its own device-wide requirements. Built-in signatures cannot be changed by
JSON or a contributor. Authors extend Heater by subclassing it and registering
additional capabilities. Binding examples use an explicit reference-only
contributor class with fixed `DeviceBinding` facts, never an invented AutoSuite
profile. Thermal `DeviceSelectionBinding` is explicitly rejected by shared
binding-use validation before compilation/reference execution, including derived
heater contracts. This enforces the fixed-only stage without changing generic
DeviceAt syntax or existing agitation selection.

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

Executable author example: `uv run python examples/warm_sample.py` reports the
current native profile gate. Contributor/direct-IR example:
`uv run python -m examples.developer.warm_sample_ir`, whose `BenchHeater` declares
explicit profile capabilities and `ThermalRecordingTarget` returns one trusted
fixed binding and JSON output. Its direct Program and the source program produce
the same saved/applied state with 10 seconds of explicit virtual waiting and a
final disabled state. The complete JSON companion is `warm_sample_ir.json`.

Minimal contributor declaration and binding (reference-only, runnable in R5.2):

```python
from typing import ClassVar
from sciloom import Heater
from sciloom.devices.declarations import bind_device

class BenchHeater(Heater):
    device_type_id: ClassVar[str] = "example.bench-heater/v1"
    writable_properties = ("temperature", "ramp_rate")
    required_configuration = ("temperature", "ramp_rate")
    supported_operations = (Heater.start, Heater.stop)

binding = bind_device(logical_id="heater", device=BenchHeater(),
                      physical_id="reference:heater-1")
# binding.contract preserves Heater's signatures and both requirements.
```

### Native profile entry gate — R5.3

Before implementing a profile constructor, obtain a valid original export,
installed controller identity/mode/ranges and precision-preserving temperature/
gradient measurements. Update this contract with its exact immutable dataclass
constructor and a runnable binding example. The supplied incomplete test.asfp
does not justify inventing them. If evidence is absent, R5.3 may land diagnostic/
probe/documentation work with native emission rejected; do not publish a fake
unusable hardware profile. Keep Q6–Q9 pending.

R5.3 has completed the evidence-limited documentation scope: the
[native thermal capture procedure](../../../autosuite/docs/37_FIXED_THERMAL_MEASUREMENTS.md)
records primary-APP task identities, exact input/re-export and lifecycle matrices,
receipt requirements and the later narrow unlock boundary. No precise nonzero
gradient/temperature or Executor receipt has arrived; no constructor or adapter
is implemented. Existing source/IR examples and target rejection tests remain
the executable diagnostics. Thermal receipt review is manual; the failure/CSV
validator does not accept this suite.

## R6: Location arguments and bounded transfer

### Parameters and quantities — implemented in R6.1, native encoding gated

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

R6.1 also supports scalar/list fields, typed log/append values, and reference CSV
reads with explicit matching flow/length units using the existing multiplicative
column contract. It adds no dimensional inference (for example flow × time) or
new CSV API. AutoSuite flow/length encoding remains explicitly rejected pending
native evidence, including direct emitter calls. Unknown device commands remain
rejected by reference execution; the defined transfer effect is implemented in R6.2.

Exact quantity usage (runnable in R6.1):

```python
from sciloom import FlowRate, Function, Input, Length, Output, mL_per_min, mm, runtime

class TransferSettings(Function):
    factor: Input[float]
    flow: Output[FlowRate]
    clearance: Output[Length]

    @runtime
    def run(self) -> None:
        self.flow = self.factor * mL_per_min
        self.clearance = 2 * mm
# factor=60 gives 1e-6 m3/s and 0.002 metres in reference execution.
```

Minimal contributor signature (source/IR/JSON available in R6.1; no execution
semantics or target support is implied):

```python
from typing import ClassVar
from sciloom import Agitator, FlowRate, Zone
from sciloom.devices import operation

class LocatedAgitator(Agitator):
    device_type_id: ClassVar[str] = "example.located-agitator/v1"

    @operation(id="example.located-agitator.inspect/v1")
    def inspect(self, source: Zone, destination: Zone, flow: FlowRate) -> None:
        ...
# Parameters have ZoneType(), ZoneType(), ScalarType.FLOW_RATE in that order.
# They remain typed named DeviceCommand arguments. Zone properties/list[Zone]
# and unknown-command reference execution are rejected.
```

Executable examples: `uv run python examples/transfer_settings.py` reports the
native gate; `uv run python -m examples.developer.transfer_values_ir` generates
its direct-IR JSON companion and compares source/JSON/specialized results.
`uv run python -m examples.developer.location_command_ir` supplies a full
contributor declaration and explicit recording target; it writes JSON in declared
argument order and demonstrates unknown-command rejection. These examples
control no hardware and have complete same-base-name companions.

### LiquidHandler family — implemented in R6.2, native gated

This first family implementation accepts fixed deployment only. Candidate
selection bindings are rejected even when the current program only configures
properties; this is a family availability boundary, matching the fixed Heater
stage, not an assertion that property writes perform a physical action.

Runnable author example: `uv run python examples/transfer_sample.py` reports
the native profile gate. Contributor example:
`uv run python -m examples.developer.transfer_sample_ir` compares source,
direct IR and JSON with explicit reference locations and a 1 mL tool capacity,
then reports the 0.25 mL transfer followed by a log. Its complete companion is
`transfer_sample_ir.json`; it does not simulate fluid motion or instrument precision.

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

This has reference semantics with explicit locations/bindings and
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

R6.2 implementation details (available in this implementation): stable IDs are
`sciloom.liquid-handler/v1`, `sciloom.liquid-handler.aspirate-flow/v1`,
`sciloom.liquid-handler.dispense-flow/v1`, `sciloom.liquid-handler.air-gap/v1`
and `sciloom.liquid-handler.transfer/v1`. The protected ordinary CommandContract
has `source: ZoneType`, `destination: ZoneType`, `volume: VOLUME`, in that order.
All three family properties plus any concrete profile requirements are mandatory
for transfer, even when a subclass narrows its device-wide requirement tuple.
No fields are added to the existing CommandContract wire form.

The immutable binding constructor is keyword-only:

```python
from typing import ClassVar
from sciloom import LiquidHandler, Zone, mL
from sciloom.core.bindings import DeviceBindings, TransferDeviceBinding
from sciloom.devices.declarations import bind_device

class BenchLiquidHandler(LiquidHandler):
    device_type_id: ClassVar[str] = "example.bench-liquid-handler/v1"
    writable_properties = ("aspirate_flow", "dispense_flow", "air_gap")
    required_configuration = ("aspirate_flow", "dispense_flow", "air_gap")
    supported_operations = (LiquidHandler.transfer,)

bindings = DeviceBindings(devices=(TransferDeviceBinding(
    binding=bind_device(logical_id="liquid", device=BenchLiquidHandler(),
                        physical_id="reference:liquid-1"),
    source_wells=Zone(well_ids=("well:source",)),
    destination_wells=Zone(well_ids=("well:destination",)),
    usable_capacity=1 * mL,
),))
```

This contributor is reference-only; it is not a native profile. The wrapper
requires a compatible fixed LiquidHandler binding supporting transfer, all
mandatory properties writable, nonempty immutable allowed Zones and positive
finite Volume capacity. Its logical/physical IDs, contracts and capabilities
are read-only projections of that binding. All allowed wells must exist in the
explicit LocationDirectory when transfer is requested. Candidate transfer
selection and `at()` on this fixed binding are rejected; no hidden one-controller
context substitutes for the two typed arguments.

`from sciloom.core.interpreter import TransferEvent` exposes a frozen record with
`node_id`, `resource_id`, `physical_id`, `source: Zone`, `destination: Zone`,
`volume: Volume`, `configuration: Mapping[str, OutputValue]` and the transfer
`operation_id`. Configuration is a detached immutable snapshot. Successful
transfer retains saved configuration and updates last-applied configuration;
logical/physical enabled flags remain unchanged. No inventory, measurement or
device I/O is simulated. A failed check updates neither last-applied state nor
the event history with a transfer; earlier configuration events remain visible.

### Native profile entry gate — R6.3

The current stage supplies the
[fixed-transfer measurement procedure](../../../autosuite/docs/38_FIXED_TRANSFER_MEASUREMENTS.md),
with primary task identities, raw row/mask evidence and paired Editor/re-export/
Executor cases. It ships no native profile constructor or adapter. The exact
native constructor example remains intentionally unset until valid profile
evidence can establish its fields; there is no callable placeholder API.

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
