# Choose settings before compilation

Use constructor arguments for settings that should stay fixed in a generated
program. For example, vials and flasks can use the same speed-selection logic
with different thresholds.

The program below produces two packages. Each still takes a `volume` input;
its threshold and two speed choices are fixed when you compile it. The numbers
are examples of configuration, not experimental recommendations.

```python
from sciloom import Function, Input, Output, RotationalSpeed, rpm, runtime
from sciloom_autosuite import AutoSuiteTarget


class ChooseSpeed(Function):
    """Choose a speed with thresholds fixed when the instance is created.

    Args:
        threshold: Volume below which the gentle speed applies.
        gentle: Speed for small volumes.
        fast: Speed otherwise.

    Attributes:
        volume: Sample volume in millilitres.
        speed: Chosen speed.
    """

    volume: Input[float]
    speed: Output[RotationalSpeed]

    def __init__(self, threshold: float, gentle: RotationalSpeed, fast: RotationalSpeed) -> None:
        self.threshold = threshold
        self.gentle = gentle
        self.fast = fast

    @runtime
    def run(self) -> None:
        if self.volume < self.threshold:
            self.speed = self.gentle
        else:
            self.speed = self.fast


vials = ChooseSpeed(threshold=1.0, gentle=200 * rpm, fast=400 * rpm)
flasks = ChooseSpeed(threshold=5.0, gentle=300 * rpm, fast=600 * rpm)
for name, function in (("vials", vials), ("flasks", flasks)):
    print(name, function.compile(target=AutoSuiteTarget()).write(f"choose_{name}.asfp").name)

```
```text
vials choose_vials.asfp
flasks choose_flasks.asfp
```

## Change a build-time setting or a runtime input

`ChooseSpeed(threshold=..., gentle=..., fast=...)` runs the Python constructor
and stores three settings. SciLoom reads them during compilation. Change them
and compile again to generate another program.

The `volume: Input[float]` field works differently: its value is supplied
each time the generated function is called. You do not need to compile again
for each volume.

| Value | When you choose it |
| --- | --- |
| `threshold`, `gentle`, `fast` | Before compilation, through the constructor |
| `volume` | At each call to the generated function |
| `speed` | Calculated by the runtime method and returned as an output |

The `for` loop below the class is ordinary Python. It runs on your computer
to produce two files. The restrictions inside `@runtime`, such as using
`while` instead of `for`, do not apply to this build code.

## Which settings can enter the procedure?

An ordinary attribute read through `self` can supply a `bool`, `int`,
`float` or `RotationalSpeed`. An unwrapped class declaration such as
`batch_size: int = 8` works the same way. A host list, string or arbitrary
object cannot be used as a runtime value.

Use a different name for host settings and runtime fields: a constructor must
not assign an `Input`, `Output` or `Var`. For an error involving a host
value, see [troubleshooting](../troubleshooting.md).
