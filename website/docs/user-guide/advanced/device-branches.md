# Device-dependent branches

One program can serve two instruments. A compile-time query asks what the bound
device is or can do, and the compiler keeps only the branch that applies to the
selected target.

```python
from examples.developer.demo_contribution import DemoAgitator, DemoTarget
from sciloom import Agitator, Function, Input, RotationalSpeed, comptime, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class Portable(Function):
    """Stir on any agitator; tune the gain where the instrument has one.

    Attributes:
        shaker: Logical agitator bound by the selected target.
        speed: Speed to save and apply.
    """

    shaker: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if comptime.is_device(self.shaker, DemoAgitator):
            self.shaker.gain = 0.5
        self.shaker.speed = self.speed
        self.shaker.start()


autosuite = Portable().compile(
    target=AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
    ),
)
demo = Portable().compile(target=DemoTarget(devices={"shaker": DemoAgitator()}))
print(autosuite.artifact.suffix, demo.artifact.suffix)
```

`DemoAgitator` and `DemoTarget` come from the
[independent device example](../../examples/demo-device.md): an agitator with an
extra `gain` property, and a target that emits JSON. The same source compiles for
AutoSuite, where the gain branch is dropped, and for the demo target, where it is
kept. The [portable agitation example](../../examples/portable-agitation.md)
shows the two artifacts.

## The three queries

| Query | Asks | Effect on the branch |
|---|---|---|
| `comptime.is_device(self.shaker, DemoAgitator)` | is the bound device this class or a subclass | the branch sees the device as that class, so `self.shaker.gain` type-checks |
| `comptime.can_write(self.shaker, "speed")` | does the bound device accept writes to this property | none beyond selection |
| `comptime.supports(self.shaker, Agitator.start)` | does the bound device support this command | none beyond selection |

A query takes two positional arguments: a declared device slot and, in order, a
device class, a property name as a string literal, or a command method. It must
be the whole condition of an `if` or `elif`; combine queries by nesting, not with
`and`. The arguments never depend on runtime values.

Every branch is compiled and type-checked, so a branch for an instrument you are
not deploying today must still be valid source. Only the selected branch must be
supported by the chosen target. A missing binding is an error, never a false
answer. A query about a device class unrelated to the slot's declared type, or
about a sibling class inside an already narrowed branch, is refused.

## Portability has limits

The target reports what its instrument can do; SciLoom does not clamp a value,
substitute a command or invent behaviour. If the selected branch uses an
operation the bound profile lacks, or a target's own rule cannot be proven,
compilation fails with a diagnostic naming the statement.
