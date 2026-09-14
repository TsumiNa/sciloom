# 3. Write a Function against the family

An experiment names the family, never the profile.

<!-- tutorial: step -->
```python
class Anneal(Function):
    """Set a temperature and hold it.

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
        self.heater.setpoint = self.temperature
        self.heater.hold(30.0)
        self.done = True


program = Anneal().to_ir()
print("nodes:", ", ".join(type(node).__name__ for node in program.functions[0].body))
print("resources:", [resource.logical_id for resource in program.resources])
print("contracts:", [contract.type_id for contract in program.device_types])
```

<!-- tutorial: checkpoint -->
```text
nodes: ConfigureProperty, DeviceCommand, Assignment
resources: ['heater']
contracts: ['sciloom.device/v1', 'example.heater/v1']
```

`heater: Heater` declares a device slot, not a runtime variable. The slot is how
the same program survives being deployed onto a different heater later.

`to_ir()` produces the authored program without any target, and three things are
worth noticing in what it prints. The property write became `ConfigureProperty`
and the command became a generic `DeviceCommand`; only agitation has dedicated
lifecycle nodes today, as [device contracts](../reference/device-contracts.md#declarations-become-ir)
records. The program declares one resource under the slot's name. And the
recorded contracts are the **family's**, not any profile's: the program was
written against `Heater`, so its JSON can be rebound to any heater profile
without recompiling from Python, the mechanism the
[portable agitation example](../../examples/portable-agitation.md) demonstrates.

Next: [4. Write a target](write-a-target.md).
