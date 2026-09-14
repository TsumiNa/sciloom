# Host-time specialization

`__init__` runs on your computer. Values it stores on the instance are read when
the source is compiled and become literals in the program, so one class can
yield differently tuned programs.

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


class Limits(Function):
    """A host list cannot enter a runtime expression.

    Attributes:
        volume: Sample volume in millilitres.
        small: Whether the volume is below the first limit.
    """

    volume: Input[float]
    small: Output[bool]

    def __init__(self) -> None:
        self.limits = [1.0, 5.0]

    @runtime
    def run(self) -> None:
        self.small = self.volume < self.limits


try:
    Limits().compile(target=AutoSuiteTarget())
except Exception as error:
    print(error)
```

## What can be embedded

A host attribute read through `self` inside the runtime method is embedded as a
literal if it is a `bool`, `int`, `float` or `RotationalSpeed`. Anything else,
a list, a string, an object, is refused with `host_value`, as the second program
shows. An unwrapped class annotation such as `batch_size: int = 8` is host data
of the same kind, not runtime state.

Embedding happens when the source is read, so two instances built with different
constructor arguments compile to two different programs; the runtime inputs stay
inputs. Host attributes are ordinary Python: reading `self.threshold` from host
code works, and only the runtime fields are protected.

A constructor must not assign a name that is declared as a runtime field; that is
refused with `runtime_field_write`, because the class declaration owns the
schema. Child Function instances are stored the same way, as host attributes,
which is how [composition](composition.md) works.
