# Compile for AutoSuite

Bind each shaker your procedure needs to an existing AutoSuite configuration,
then write the function package. For example, this program starts two shakers
at the same supplied speed.

The example names and IDs below must be replaced with values from your own
configuration before deployment.

```python
from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget, AutoSuiteVersion


class TwoShakers(Function):
    """Start two shakers at one speed.

    Attributes:
        left: First logical agitator.
        right: Second logical agitator.
        speed: Speed for both.
    """

    left: Agitator
    right: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.left.speed = self.speed
        self.right.speed = self.speed
        self.left.start()
        self.right.start()


target = AutoSuiteTarget(
    version=AutoSuiteVersion.V2_47_1_1,
    devices={
        "left": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
        "right": AutoSuiteIndividualShaker(zone="Heater Shaker 24", device_id="24"),
    },
)
print(TwoShakers().compile(target=target).write("two_shakers.asfp").name)
```
```text
two_shakers.asfp
```

## Supply the binding

`"left"` and `"right"` match the Function's field names. Each profile supplies
a zone name and individual shaker ID from the installed AutoSuite configuration.
The ID identifies the shaker, not a vial or rack. Two separate logical devices
cannot bind to the same shaker ID; to share one device between steps, use
[a shared logical reference](composition.md). A zone name alone does not identify
an actuator. When a layout is supplied, each profile must independently match
the installed controller and the ancestry of every selected well. Offline
bindings do not establish that a declared combination fits the real APP.

Bind every declared device, including one its runtime method does not use.
Remove declarations you no longer need. For a child with a separate device,
use its component path, such as `"stage.shaker"`.

## Save and use the package

The example writes `two_shakers.asfp` in the directory where you run the
Python script. The package includes the procedure and any called Functions.
Here its caller supplies `speed` when AutoSuite runs it; that input is not a
parameter to `.compile()`.

`AutoSuiteVersion.V2_47_1_1` is the only supported serialization version and
the default, so you can omit the explicit `version=` argument. Keep the
`.asfp` extension when choosing a filename; `write()` does not add it.

Before equipment use, validate the generated package with AutoSuite Executor
on the deployment computer. SciLoom does not establish physical speed limits
or prove that a zone matches your instrument. See
[current validation limits](../../introduction/status.md#what-compilation-establishes).

## Current AutoSuite restrictions

| If your procedure needs… | Use… |
| --- | --- |
| Two Boolean conditions | Nested `if` statements; this target refuses `and` and `or` |
| Repeated work | A `while` loop; recursive Function calls are unsupported |
| An output list updated element by element | A whole-list assignment first, such as `self.result = self.values` |
| A new operation reporting `unsupported_runtime_guard` | Reference execution until AutoSuite failure propagation is verified; no override bypasses this check |

Assigning `self.result = []` is suitable when an empty list is the intended
output. It does not allocate elements for later indexed writes. To update
existing elements, initialize the required list values first.

A list output must be initialized on every path before it is read or updated.
A loop might run zero times, so initialize before the loop. For exact errors
and fixes, use [troubleshooting](../troubleshooting.md); for the complete source
subset, see [runtime syntax](../reference/runtime-language.md).
