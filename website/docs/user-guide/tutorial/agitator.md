# 4. Stirring with an Agitator

Now the experiment itself. `StirRack` uses the three Functions written so far
and adds the shaker.

<!-- tutorial: step -->
```python
from sciloom import Agitator


class StirRack(Function):
    """Stir a rack at a speed chosen from its largest sample, or stop.

    Attributes:
        volumes: Volume of every vial in the rack.
        enabled: Whether the rack should be stirring after this call.
        shaker: Logical agitator; the target binds the hardware.
        largest: Largest volume measured on this call.
        speed: Speed chosen for that volume.
    """

    volumes: Input[list[float]]
    enabled: Input[bool]
    shaker: Agitator
    largest: Var[float] = 0.0
    speed: Var[RotationalSpeed] = 0 * rpm

    def __init__(self) -> None:
        self.measure = LargestVolume()
        self.choose = ChooseSpeed()
        self.counter = CountStirs()

    @runtime
    def run(self) -> None:
        self.largest = self.measure(volumes=self.volumes)
        self.speed = self.choose(volume=self.largest)
        if self.enabled:
            self.shaker.speed = self.speed
            self.shaker.start()
            self.counter()
        else:
            self.shaker.stop()
```

`shaker: Agitator` declares a **logical device**: the program needs an agitator,
any agitator. It is not a piece of hardware and not a value; you never construct
one or assign one. Which shaker it becomes is decided when you compile, on the
next page.

`__init__` is ordinary Python. It runs on your computer when you write
`StirRack()`, and here it creates the three child Functions. In the runtime
method a child is called like a function and its outputs are bound by
assignment: `self.largest = self.measure(volumes=self.volumes)` passes the rack
in and copies the result out. A child with no outputs, `self.counter()`, is
called as a statement. Each child keeps its own state, so the counter keeps
counting across calls.

Configuring the shaker takes two steps on purpose. `self.shaker.speed = self.speed`
**saves** a configuration and changes nothing on the device. `self.shaker.start()`
**applies** everything saved and enables agitation. `self.shaker.stop()` disables
it and keeps the saved values. Assigning a speed of `0 * rpm` is a configuration,
not a stop. Before a `start()`, the speed must have been assigned on every path
that reaches it; the compiler checks this for you.

Compiling now fails, and the message says why: the program declares a device
that the target has not been told about.

<!-- tutorial: checkpoint -->
```python
try:
    StirRack().compile(target=AutoSuiteTarget())
except Exception as error:
    print(error)
```
```text
$.resources[0]: No compatible binding for device 'shaker'. [missing_resource_binding]
```

Next: [5. Bind and compile](compile.md).
