# Device contracts

How a device family, a profile and their members are declared, and how those
declarations become semantic IR. The walkthrough is
[add a device](../add-a-device.md); the shipped families and profiles are
`Agitator`, `AutoSuiteIndividualShaker` and, outside core, `DemoAgitator` in the
[independent contribution example](../../examples/demo-device.md).

## Identity

| Rule | Detail |
|---|---|
| every device class has its own `device_type_id` | a class variable such as `"example.heater/v1"`; a subclass never inherits its parent's |
| identifiers are namespaced and versioned | `[A-Za-z][A-Za-z0-9_.-]+/v[1-9][0-9]*` |
| built-in contracts are fixed | redefining `sciloom.device/v1` or `sciloom.agitator/v1`, or a built-in member signature, is refused |
| `BaseDevice` imposes nothing | no universal start or stop; each family declares its own lifecycle |

## Properties and commands

| Member | Declaration | Rule |
|---|---|---|
| configuration property | a Python `property` whose setter carries `@operation(id=...)` | the getter declares the type and raises; setter and getter types match; the setter takes one typed value and returns `None` |
| command | a method decorated with `@operation(id=...)` | typed positional arguments, no defaults or variadics, returns `None` |
| value types | `int`, `float`, `bool`, `RotationalSpeed`, or a homogeneous list of one of them | no other Python objects |

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

Only agitation has dedicated lifecycle nodes today; every other family speaks
through `ConfigureProperty` and `DeviceCommand`, each carrying the semantic id
from the declaring class. The authored program names the family's contract; the
selected program names the bound profile's, with the full ancestor directory.
Neither the IR nor the compiler knows or special-cases any author subclass.

## Required configuration

`required_configuration` is enforced at two points, and only two.
`bind_device` checks that every required property is writable on the profile.
The compiler's definite-configuration pass proves, on every reachable path
within one invocation of the entry Function and across calls, that each property
a `StartAgitation` node requires has been written before it. A generic
`DeviceCommand` neither requires nor supplies configuration, so a family without
a dedicated lifecycle node, such as the tutorial's heater, can declare
`required_configuration` and have it checked for writability, but nothing
enforces it before `hold` unless the target does so in its own `validate`.

## Rejections

A rejected declaration raises `IRValidationError` with a structured diagnostic:
code `class_schema` when a Function declares device slots, `device_contract`
when a device class declares its identity, properties or commands. That holds
wherever the declaration is read, including when `bind_device` builds a
profile's contract or its ancestors'. Two boundaries stay `TypeError`, because
neither reports a declaration: the host access guards, and `bind_device`'s own
checks on a profile's capability lists.
