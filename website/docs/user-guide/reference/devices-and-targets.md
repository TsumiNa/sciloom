# Devices and targets

Declare the device your procedure needs; bind it to an instrument when compiling.

## Agitator

`Agitator` is the built-in device family. Declare `shaker: Agitator` in
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
| Separate logical devices | Must have different IDs and zones |
| Generated file | UTF-8 XML function package, with an `.asfp` extension |
| `result.write(path)` | Write bytes, create parent directories and return the path; no extension added |

Zone names must be nonempty single-line strings. SciLoom does not discover
zones or check which physical instrument is connected.
See [AutoSuite compilation](../advanced/autosuite.md) for package handoff and
target-specific language restrictions.

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
