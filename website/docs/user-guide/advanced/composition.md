# Share a shaker between steps

You may want one Function to choose or save a setting and another to start
the device. Give both steps a reference to the same shaker.

In this example, `SetSpeed` saves the requested speed. `StirStage` calls it
and then starts the shaker. Save the complete program to a `.py` file to
compile it.

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
print(result.write("shared_shaker.asfp").name)
```
```text
shared_shaker.asfp
```

## Share the device in the constructor

`self.stage = SetSpeed()` creates the child. The next line,
`self.stage.shaker = self.shaker`, makes it use the parent's logical shaker.
Both steps now save settings on the same device, so the target needs just one
binding, under `"shaker"`.

Without the sharing assignment, the child has its own shaker. Bind that separate
device using the name `"stage.shaker"`. Share a logical reference in the
constructor; supply concrete AutoSuite hardware data in the target.

## Pass values between steps

`self.stage(speed=self.speed)` supplies the child's input. This child has no
outputs. For a child with an output, receive it with an assignment, as in the
[volume calculation](../tutorial/agitator.md). Several outputs use a tuple
assignment in declaration order.

Supply each input once, by position or keyword. A call result must go to a
whole field; if you need it in a list element or an arithmetic expression,
store it in a field first.

A child receives a copy of each input list. Updating that copy does not change
the parent's list; output lists are copied back when the child returns.
Each child instance also keeps its own `Var` values between calls.

## Configure before starting

Here the child saves the speed and the parent starts. SciLoom checks the
configuration across both calls. If a branch skips `SetSpeed` but still
reaches `start()`, compilation fails. The check does not assume that a
previous call to the entry Function configured the device.
