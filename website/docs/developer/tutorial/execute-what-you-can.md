# 7. Execute what you can

The reference interpreter defines SciLoom semantics. It will not invent
behaviour for a command only your hardware understands, and it says so.

<!-- tutorial: step -->
```python
try:
    Interpreter(result.specialized_ir).run(inputs={"temperature": 60.0})
except ExecutionError as error:
    print("interpreter:", error.diagnostics[0].code, error.diagnostics[0].message)


class Preheat(Function):
    """Save a setpoint; every statement has reference semantics.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        done: Set once the setpoint is saved.
    """

    heater: Heater
    temperature: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        self.heater.setpoint = self.temperature
        self.done = True


selected = Preheat().compile(target=BenchTarget(devices={"heater": BenchHeater()})).specialized_ir
snapshot = Interpreter(selected).run(inputs={"temperature": 60.0})
print("preheat:", snapshot.outputs["done"], dict(snapshot.resources["resource:heater"].configuration))
```

<!-- tutorial: checkpoint -->
```text
interpreter: unsupported_operation Cannot execute DeviceCommand.
preheat: True {'setpoint': 60.0}
```

`result` is the `Anneal` program compiled on page 4. Its selected program is
valid and its artifact was emitted, but its `hold` is a native command with no
reference semantics, so the interpreter refuses to run it. Compilation and
target emission still work; only simulated execution stops.

`Preheat` writes a property and nothing else. Property writes have reference
semantics for every family, so the session runs, reports the output, and shows
the saved configuration on the resource. The interpreter takes the **selected**
program: a program with device branches still in it is refused at construction.
What a session records, and its limits, are on
[reference execution](../reference/interpreter.md).

--8<-- "website/snippets/hardware-boundary.md"

Next: [8. The complete program](complete-program.md).
