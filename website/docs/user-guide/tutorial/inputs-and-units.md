# 2. Inputs, outputs and speeds

The counter kept state but exchanged nothing. Most Functions receive values and
hand results back. Add a Function that turns a sample volume into a stirring
speed.

<!-- tutorial: step -->
```python
from sciloom import Input, Output, RotationalSpeed, rpm


class ChooseSpeed(Function):
    """Choose a stirring speed from a sample volume.

    Attributes:
        volume: Sample volume in millilitres.
        speed: A gentle speed for small volumes, a faster one otherwise.
    """

    volume: Input[float]
    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if self.volume < 2.0:
            self.speed = 300 * rpm
        else:
            self.speed = 600 * rpm
```

An `Input` is supplied by whoever calls the Function; an `Output` is written back
when the call returns. Neither has a default on the class, and every `Output`
must be assigned on every path through the method, which is why the `else`
branch is not optional here.

`RotationalSpeed` is the one physical quantity in this release. A speed is
written as a number times a unit, `300 * rpm`; revolutions per second, `rps`,
is the canonical form and the two compare equal:

<!-- tutorial: checkpoint -->
```python
from sciloom import rps

print(600 * rpm == 10 * rps)
print(ChooseSpeed().compile(target=AutoSuiteTarget()).write("choose_speed.asfp").name)
```
```text
True
choose_speed.asfp
```

A bare number is not a speed. Types are checked before anything is generated,
so assigning `600` to a speed output is refused with the path of the offending
statement:

<!-- tutorial: checkpoint -->
```python
class BareNumber(Function):
    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.speed = 600


try:
    BareNumber().compile(target=AutoSuiteTarget())
except Exception as error:
    print(error)
```
```text
$.functions[0].body[0]: Cannot assign integer to rotational_speed. [type_mismatch]
```

The same checker widens an integer to a float where that is safe and never
narrows a float to an integer; `bool` is its own type, and a condition must be
a Boolean rather than a number.

Next: [3. Lists and loops](lists-and-loops.md).
