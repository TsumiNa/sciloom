# Device contracts

How a device family, a profile and their members are declared, and how those
declarations become semantic IR. The walkthrough is
[declare a family](../tutorial/declare-a-family.md); the shipped families and profiles are
`Agitator` and `Heater`, with the native `AutoSuiteIndividualShaker` profile.
Outside core, `DemoAgitator` appears in the
[independent contribution example](../../examples/demo-device.md), and the
[fixed heater example](../../examples/warm-sample.md) supplies a reference-only
profile. AutoSuite thermal profiles remain gated pending native evidence.

## Identity

| Rule | Detail |
|---|---|
| every device class has its own `device_type_id` | a class variable such as `"example.heater/v1"`; a subclass never inherits its parent's |
| identifiers are namespaced and versioned | `[A-Za-z][A-Za-z0-9_.-]+/v[1-9][0-9]*` |
| built-in contracts are fixed | redefining `sciloom.device/v1`, `sciloom.agitator/v1` or `sciloom.heater/v1`, or a built-in member signature, is refused |
| `BaseDevice` imposes nothing | no universal start or stop; each family declares its own lifecycle |

## Properties and commands

| Member | Declaration | Rule |
|---|---|---|
| configuration property | a Python `property` whose setter carries `@operation(id=...)` | the getter declares the type and raises; setter and getter types match; the setter takes one typed value and returns `None` |
| command | a method decorated with `@operation(id=...)` | typed positional arguments, no defaults or variadics, returns `None` |
| lifecycle command | `@operation(id=..., lifecycle=LifecycleEffect.APPLY_AND_ENABLE)` or `DISABLE` | parameterless; optional `requires=("property_name", ...)` |
| value types | `int`, `float`, `bool`, `str`, `RotationalSpeed`, `Volume`, `Duration`, `Temperature`, `TemperatureDifference`, `TemperatureRate`, or a homogeneous list of one of them | no other Python objects |

The compiler reads declarations statically and never executes their bodies.
Host access is guarded: reading a device property or calling a runtime method
from host Python raises `TypeError`. Registered parameters are written by
assignment; there are no `set_*` methods and no getters.

## Profiles

A profile is a concrete subclass carrying immutable deployment data (a frozen
dataclass with fields such as `channel` or `zone`) and three explicit capability
lists:

| List | Meaning |
|---|---|
| `writable_properties` | property names the instrument accepts writes to |
| `required_configuration` | property names that must be written before the family's lifecycle start |
| `supported_operations` | command methods the instrument runs |

Capabilities are never inherited: `bind_device` refuses a profile that omits any
of the three lists, or that names a member the family never declared, with a
`TypeError`. Every required property must be writable.

## Declarations become IR

| Declaration | Statement in the program | Node |
|---|---|---|
| `self.heater.setpoint = value` | property write | `ConfigureProperty` |
| `self.heater.hold(30.0)` | command call | `DeviceCommand` |
| `self.shaker.start()`, `self.shaker.stop()` | agitation lifecycle | `StartAgitation`, `StopAgitation` |
| `self.heater.temperature = value`, `self.heater.ramp_rate = value` | built-in thermal configuration | `ConfigureProperty` |
| `self.heater.start()`, `self.heater.stop()` | explicit thermal lifecycle contracts | `DeviceCommand` |

Only agitation has dedicated lifecycle nodes today; every other family speaks
through `ConfigureProperty` and `DeviceCommand`, each carrying the semantic id
from the declaring class. The authored program names the family's contract; the
selected program names the bound profile's, with the full ancestor directory.
Neither the IR nor the compiler knows or special-cases any author subclass.

## Required configuration

`bind_device` checks required properties are writable. The compiler proves
configuration on every reachable path within one entry invocation, across calls
and loops; it does not assume a previous invocation configured the resource.
`StartAgitation` uses the concrete device's `required_configuration`.

An explicitly declared lifecycle command uses a new `LifecycleCommandContract`
inside the existing `DeviceCommand` node:

```python
from sciloom.core.ir import LifecycleEffect
from sciloom.devices import operation

@operation(id="example.controller.apply/v1", lifecycle=LifecycleEffect.APPLY_AND_ENABLE)
def apply(self) -> None:
    ...
```

`APPLY_AND_ENABLE` requires the union of the concrete device's configuration
requirements and the command's explicit `requires` property names. It snapshots
all saved values and enables or reapplies. `DISABLE` checks only its explicit
requirements and retains saved and applied values. Writes capture values without
applying them; no command method name implies an effect. Both effects currently
require no arguments. Unknown or repeated property names, lifecycle setters and
`requires` without `lifecycle` are rejected.

Heater's protected start command explicitly requires both `temperature` and
`ramp_rate`, in addition to any concrete profile requirements. A derived profile
cannot waive those family requirements by clearing its own list, and a profile
supporting start must make both properties writable. Stop has no mandatory
configuration. Heater and its subclasses currently require fixed bindings;
candidate selection is rejected before compilation/reference execution.

Reference execution implements these effects and checks requirements before
changing state or recording an action. Supplied bindings must exactly match
serialized contracts; IDs never load Python implementations. A plain
`CommandContract` still has no reference effect or implicit configuration
requirements, so ordinary commands remain target-defined. Existing agitation
nodes and contracts keep their wire forms. See the runnable
[lifecycle contribution](../../examples/lifecycle-commands.md). AutoSuite rejects
new lifecycle commands until an explicit profile adapter is verified.

## Rejections

A rejected declaration raises `IRValidationError` with a structured diagnostic:
code `class_schema` when a Function declares device slots, `device_contract`
when a device class declares its identity, properties or commands. That holds
wherever the declaration is read, including when `bind_device` builds a
profile's contract or its ancestors'. Two boundaries stay `TypeError`, because
neither reports a declaration: the host access guards, and `bind_device`'s own
checks on a profile's capability lists.
