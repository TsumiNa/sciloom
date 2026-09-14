# Devices and targets

## Agitator

`Agitator` is the one device family in this release. Declare a slot with
`shaker: Agitator`; never construct a device or put a profile in the Function.
Explained in [tutorial 4](../tutorial/agitator.md).

| Operation | Effect |
|---|---|
| `self.shaker.speed = value` | evaluate now and save the configuration; running state unchanged |
| `self.shaker.start()` | apply the complete saved configuration and enable agitation |
| repeated `start()` | reapply the current configuration, staying enabled |
| `self.shaker.stop()` | disable; saved and last-applied values are kept |
| `self.shaker.speed = 0 * rpm` | configure zero speed; not a stop |

Changing the source variable after the assignment does not change the saved
value. Writing configuration while running does not change the applied snapshot
until the next `start()`. A missing parameter is not read as zero. Property reads
and `+=` are refused; there is no measured getter. Timing and timed stops are not
part of `Agitator`. Before every `start()`, `speed` must have been assigned on
every path that reaches it, across calls within the same invocation.

## Binding names

| Slot | Name in `devices` |
|---|---|
| a field on the entry Function | the field name, `shaker` |
| a field on a child that is not shared | the component path, `stage.shaker` |
| a child's slot shared with the parent | the parent's name only |

Every declared slot needs a binding, whether or not the runtime method uses it.
Explained in [composition](../advanced/composition.md).

## AutoSuite target

| Parameter | Value |
|---|---|
| `AutoSuiteTarget(version=..., devices={...})` | `version` defaults to `AutoSuiteVersion.V2_47_1_1`, the only supported version |
| `AutoSuiteIndividualShaker(zone=..., device_id=...)` | a non-empty single-line zone name; a positive decimal shaker id |
| uniqueness | no two slots may share a `device_id` or a `zone` |
| artifact | UTF-8 XML, media type `application/xml`, suffix `.asfp` |
| `result.write(path)` | writes the bytes, creates parent directories, returns the path; no suffix is added |

The target's own rules are listed on [AutoSuite rules](../advanced/autosuite.md).

## Compile-time queries

| Query | Second argument |
|---|---|
| `comptime.is_device(self.shaker, DemoAgitator)` | a device class on the slot's inheritance chain; narrows the branch |
| `comptime.can_write(self.shaker, "speed")` | a declared property name as a string literal |
| `comptime.supports(self.shaker, Agitator.start)` | a command method |

Queries appear only as the whole condition of an `if` or `elif`. Explained in
[device-dependent branches](../advanced/device-branches.md).
