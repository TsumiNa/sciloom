# Devices and targets

Declare the device your procedure needs; bind it to an instrument when compiling.

## Agitator

`Agitator` is a built-in device family. Declare `shaker: Agitator` in
the Function. The slot already provides a logical reference; you do not need to
create an Agitator object. Concrete hardware profiles belong in the target.
See [lesson 1](../tutorial/first-function.md).

| Operation | Effect |
| --- | --- |
| `self.shaker.speed = value` | Save the value for the next start; leave running state unchanged |
| `self.shaker.start()` | Apply the complete saved configuration and enable agitation |
| Repeated `start()` | Apply the current configuration again and remain enabled |
| `self.shaker.stop()` | Stop agitation; retain saved and last-applied configurations |
| `self.shaker.speed = 0 * rpm` | Save zero speed; this assignment does not stop the device |

Assignment captures the value immediately. Changing the variable that supplied
it does not change the saved configuration. While running, a new assignment
takes effect at the next `start()`.

Before agitation starts, all properties required by the bound device must be
configured on every path that reaches the call. For the AutoSuite shaker, this
means `speed`. Configuration may come from a child called earlier in the
same invocation; compilation does not assume a previous invocation supplied it.

Property reads and augmented assignments such as `+=` are not supported.
There is no measured getter, generic duration parameter or timed stop.

## LiquidHandler

Declare `liquid: LiquidHandler` from `sciloom`. Assign `aspirate_flow` and
`dispense_flow` as FlowRate values, and `air_gap` as a Volume. All three settings
are required explicitly. `transfer(source: Zone, destination: Zone, volume: Volume)`
captures one source, one distinct destination and a positive amount, then checks
the fixed tool's allowed locations and usable capacity before acting.

Reference execution requires explicit locations and a `TransferDeviceBinding`;
it records ordered intent without modelling liquid inventory or precision.
Dynamic tool selection and native AutoSuite transfer profiles remain unavailable.
See the [complete example](../../examples/transfer-sample.md).

## Heater

Declare `heater: Heater` using `from sciloom import Heater`. Its two write-only
properties are `temperature: Temperature` and `ramp_rate: TemperatureRate`.
Configure both before calling `start()`. Assignments capture values without
changing applied settings; repeated start applies the complete saved configuration.
`stop()` disables the heater while retaining saved and applied settings.

The core/reference implementation supports fixed bindings only. Candidate
selection is rejected for Heater and its subclasses. AutoSuite thermal profiles
remain gated pending native evidence; there is no measured temperature getter,
automatic stop or wait-to-temperature operation. A fixed `wait(10 * s)` requires
an explicit reference clock and does not establish that a temperature was reached.
See the [complete author and contributor example](../../examples/warm-sample.md).

## Binding names

| Logical device | Key in the target's `devices` |
| --- | --- |
| Entry Function field | `"shaker"` |
| Separate device on a child | `"stage.shaker"` |
| Child sharing the parent's logical reference | The parent's `"shaker"` only |

Every declared slot needs a binding, including unused slots. Share a logical
reference in the constructor with `self.stage.shaker = self.shaker`;
do not assign a hardware profile to a Function field.
See [the complete sharing example](../advanced/composition.md).

## AutoSuite target

| Item | Rule |
| --- | --- |
| Import | `from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget` |
| `AutoSuiteTarget(version=..., devices={...})` | Defaults to `AutoSuiteVersion.V2_47_1_1`, the only supported serialization version |
| `AutoSuiteIndividualShaker(zone=..., device_id=...)` | Existing zone name and positive decimal individual shaker ID |
| Separate logical devices | Must have distinct physical actuator identities; a shared zone name alone is not a conflict |
| Generated file | UTF-8 XML function package, with an `.asfp` extension |
| `result.write(path)` | Write bytes, create parent directories and return the path; no extension added |

Zone names must be nonempty single-line strings. An optional
`layout=AutoSuiteLayout.from_app(path)` validates fixed profiles against APP
well/controller ancestry. It does not contact the instrument. See
[runtime device locations](device-locations.md) for bounded candidate bindings
and the current dynamic-compilation gate.
See [AutoSuite compilation](../advanced/autosuite.md) for package handoff and
target-specific language restrictions.

### Inspect application settings

`AutoSuiteDeployment.from_app(path)` reads the product version, configuration
label and Macro variable-reset setting without changing the application. Missing
settings stay `None`; duplicate or malformed reset settings are rejected.

```python
from sciloom_autosuite import AutoSuiteDeployment, AutoSuiteLayout

deployment = AutoSuiteDeployment.from_app("instrument.app")
layout = AutoSuiteLayout.from_app("instrument.app")
assert deployment.app_sha256 == layout.app_sha256
print(deployment.product_version, deployment.reset_variables)
```

The hash identifies the exact compressed APP bytes. A manually constructed layout
has unknown provenance by default. The configuration label is only a display
name, not a unique application identity.

Pass both records to the target to check deployment conditions:

```python
from sciloom_autosuite import AutoSuiteTarget, write_autosuite_review

target = AutoSuiteTarget(deployment=deployment, layout=layout)
compiled = program.compile(target=target)  # Supply devices=... for device resources.
report = write_autosuite_review(compiled, target=target, path="procedure.asfp")
print(report.status, report.native_status)
```

Known product-version or APP-source conflicts reject compilation. A reset-enabled
APP also rejects programs with internal `Var` fields or saved device configuration:
their values must persist across calls. SciLoom neither changes the APP nor moves
state into global variables. Missing settings or provenance give `unknown` status.

For offline review, use `AutoSuiteTarget()` and the same exporter. It writes
`procedure.asfp` and `procedure.deployment.json`, including state requirements,
missing facts and hashes of the artifact and canonical specialized IR. The
exporter rechecks the selected contracts, target restrictions and exact emission
before writing; a mismatched target, binding or artifact is rejected. Supply the
target whose settings you intend to assess. `compiled.write(...)` continues to
write only ASFP. The two review files are not written atomically; IO errors propagate.

A report's `compatible` status means only its checked deployment conditions match;
its separate `native_status` remains `pending`. It does not certify native lifetime
behavior or instrument acceptance. See the
[settings API](../../api/autosuite.md#read-only-application-settings).

## Compile-time queries

| Whole `if` / `elif` condition | Meaning |
| --- | --- |
| `comptime.is_device(self.shaker, DemoAgitator)` | Select by a device class on the slot's inheritance chain; narrow the type within that branch |
| `comptime.can_write(self.shaker, "speed")` | Check a declared property's writability; name must be a string literal |
| `comptime.supports(self.shaker, Agitator.start)` | Check a declared command |

All source branches must satisfy SciLoom's language and type rules. The target's
capabilities are checked for the selected branch. Queries use the supplied
device bindings, not live instrument detection.
See [device-dependent branches](../advanced/device-branches.md).
