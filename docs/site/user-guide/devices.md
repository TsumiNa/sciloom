# Devices and explicit start/stop

Declare `agitator: Agitator` on a Function to express a logical dependency.
Device slots are separate from Input/Output/Var. Do not construct a logical device
object or put a concrete hardware profile into the Function.

Assign parameters with ordinary Python property syntax, then explicitly start:

```python
self.agitator.speed = self.shaker_speed
self.agitator.start()
```

This fragment belongs inside a runtime method with declared device and speed
fields. The [complete agitation example](../examples/agitation.md) also shows
target binding and conditional stop.

| Operation | Effect |
|---|---|
| `speed = value` | Evaluate now and save configuration; running state is unchanged |
| `start()` | Apply the complete saved configuration and enable agitation |
| Repeated `start()` | Reapply the current configuration while remaining enabled |
| `stop()` | Disable; retain saved and last-applied values |
| `speed = 0 * rpm` | Configure zero speed; it is not a stop command |

Changing the source variable after assignment does not change a saved value.
Writing configuration while running does not change the last-applied snapshot
until start is called again. A missing parameter is not interpreted as zero.
Reads and `+=` on device properties are explicitly unsupported; no measured getter
is provided. Timing and automatic timed stopping are not part of Agitator.

## Hardware binding

Compile with `AutoSuiteTarget(devices={...})`, mapping logical field/component paths
to immutable `AutoSuiteIndividualShaker` profiles. Profiles describe deployment,
not live hardware connections. Missing/unknown names, incompatible contracts and
duplicate physical-device bindings are errors. A device-free Function uses
`AutoSuiteTarget()` without device mappings.

## Device-dependent branches

The [portable example](../examples/portable-agitation.md) defines one experiment
with a demo-only adjustment and compiles it for two targets:

```python
if comptime.is_device(self.agitator, DemoAgitator):
    self.agitator.gain = 0.5
self.agitator.speed = self.speed
self.agitator.start()
```

The fragment uses `comptime` from sciloom and the example's DemoAgitator definition.
`is_device` narrows the true branch's type. `can_write(device, "name")` and
`supports(device, Agitator.start)` query explicit capabilities without narrowing.
The second argument to `supports` is a registered command method.
Property names must be declared, unambiguous string literals.

Queries take two positional arguments and occur only as whole if/elif conditions.
Use nested branches to combine queries. All branches must be valid typed source;
only selected branches need support from the chosen target. Missing bindings are
errors, not false query results. Unrelated and sibling device-type queries are
rejected, including inside already narrowed branches.

Portability is constrained by device capabilities. Unsupported selected operations
or unprovable declared device limits fail compilation; SciLoom does not silently
clamp values or invent hardware behavior.
