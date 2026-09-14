# 6. Adapt with comptime

A compile-time query asks about the bound device and keeps only the branch that
applies. Both branches are type-checked first, so the branch you did not take is
still valid code.

<!-- tutorial: step -->
```python
class Adaptive(Function):
    """Write a setpoint only on a heater that accepts one.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        done: Set once the hold has been requested.
    """

    heater: Heater
    temperature: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        if comptime.can_write(self.heater, "setpoint"):
            self.heater.setpoint = self.temperature
        self.heater.hold(30.0)
        self.done = True


for label, profile in (("a writable heater", BenchHeater()), ("a read-only heater", FixedHeater())):
    selected = Adaptive().compile(target=BenchTarget(devices={"heater": profile})).specialized_ir
    print(f"adaptive on {label}:", ", ".join(type(node).__name__ for node in selected.functions[0].body))
```

<!-- tutorial: checkpoint -->
```text
adaptive on a writable heater: ConfigureProperty, DeviceCommand, Assignment
adaptive on a read-only heater: DeviceCommand, Assignment
```

The same source compiles for both profiles, and the configuration write simply
is not in the selected program for the read-only one. `can_write` asks about a
property, `supports` about a command, and `is_device` narrows to a specific
profile type; the rules an author follows when writing them are on the User
Guide's [device-dependent branches](../../user-guide/advanced/device-branches.md).

Use this when a program is genuinely correct on both kinds of instrument. Do not
use it to paper over a deployment that cannot run the experiment; a rejection
the author can read is better than a program that silently does less than they
wrote. That is the whole decision between this page and the previous one.

Next: [7. Execute what you can](execute-what-you-can.md).
