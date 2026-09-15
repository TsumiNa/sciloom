# Adapt to different devices

Suppose one agitator accepts a gain setting and another does not. Keep the
shared stirring steps in one Function, and put the extra setting in a device
condition.

This example uses AutoSuite and a demonstration target from the checkout.
The demo is a test implementation, not another supported physical instrument.

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
```text
.asfp .json
```

The same `Portable` source produces an AutoSuite `.asfp` and a demo `.json`.
The compiler keeps the gain assignment for `DemoAgitator` and removes it for
the AutoSuite shaker. Both versions save the requested speed and start.

To run this example, save it at the checkout root so the
`examples.developer.demo_contribution` import is available, then run it with
`uv run python <your_file>.py`. The
[portable agitation example](../../examples/portable-agitation.md) provides a
ready-to-run file and both generated outputs.

## Choose a condition

Use `comptime.is_device` when you need a property introduced by a particular
device type. Inside that branch, `self.shaker.gain` is recognized as a property
of `DemoAgitator`.

Use `comptime.can_write(self.shaker, "speed")` to ask whether the selected
device accepts a declared property. Use
`comptime.supports(self.shaker, Agitator.start)` to ask about a command.

A device query must be the entire condition of an `if` or `elif`. To require
two conditions, nest the `if` statements. Property names are string literals;
the other arguments identify a declared device slot and a device class or command.

## What is checked?

The compiler checks the source and types in every branch. It then chooses
branches using the target's bindings and checks whether the selected device
supports those operations. A missing binding is an error; it is not treated as
a false condition.

Keep runtime decisions, such as `if self.enabled:`, separate from device
queries. A device query is decided during compilation and does not inspect a
running instrument.

Different hardware may need different settings or experimental steps. Device
conditions let you write those differences explicitly; SciLoom does not invent
equivalent commands or adjust values for you.
