# Composition and shared devices

A Function can call other Functions. The child is created in the parent's
`__init__`, called from the parent's runtime method, and its outputs are bound
by assignment. This program goes one step further: the child and the parent use
the same shaker.

```python
from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class SetSpeed(Function):
    """Save a speed on a shared shaker without starting it.

    Attributes:
        shaker: Logical agitator shared with the parent.
        speed: Speed to save.
    """

    shaker: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.shaker.speed = self.speed


class StirStage(Function):
    """Configure through a child, then start from the parent.

    Attributes:
        shaker: Logical agitator; the child shares it.
        speed: Speed passed to the child.
    """

    shaker: Agitator
    speed: Input[RotationalSpeed]

    def __init__(self) -> None:
        self.stage = SetSpeed()
        self.stage.shaker = self.shaker

    @runtime
    def run(self) -> None:
        self.stage(speed=self.speed)
        self.shaker.start()


target = AutoSuiteTarget(
    devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
)
result = StirStage().compile(target=target)
assert result.artifact.suffix == ".asfp"
```

## Calling a child

A call is a statement. Supply each input exactly once, positionally or by
keyword. Bind one output with one assignment destination, several outputs with a
tuple destination in declaration order, and call a child with no outputs as a
bare statement. Outputs bind to whole fields, never to list elements. Calls are
never nested inside arithmetic: bind the output, then use the field.

Inputs are copied into a fresh frame and outputs are copied back after the call
returns, so parent and child never share a list. A child's `Var` state persists
across calls; calling the same instance twice continues its state, while a second
instance created in `__init__` has state of its own. A child the runtime method
never calls is left out of the compiled program. The
[function-call example](../../examples/function-call.md) shows the plain form.

## Sharing a logical device

`self.stage.shaker = self.shaker` in the constructor makes the child's slot refer
to the parent's logical device. Without that line the child's slot is a device
of its own, bound by the target under the component path `stage.shaker`. With it,
both procedures name one resource with one configuration state, bound once under
`shaker`.

Sharing lets configuration and lifecycle live in different Functions: here the
child saves the speed and the parent starts. The compiler still proves that every
required value is configured on every path that reaches a `start()`, following
calls in both directions, within one invocation of the entry Function. It never
assumes that an earlier invocation left the device configured.
