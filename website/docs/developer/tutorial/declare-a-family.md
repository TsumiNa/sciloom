# 1. Declare a family

A family says what any instrument of this kind can be asked to do. It never says
which instrument, and it never touches hardware.

<!-- tutorial: step -->
```python
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from sciloom import Function, Input, Output, comptime, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import CompilationError, Diagnostic, DiagnosticError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import DeviceCommand, Literal, Program, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.devices import BaseDevice, operation
from sciloom.devices.declarations import bind_device, device_contract

HOLD_ID = "example.heater.hold/v1"


class Heater(BaseDevice):
    """A device family: what every heater can be asked to do."""

    device_type_id: ClassVar[str] = "example.heater/v1"

    @property
    def setpoint(self) -> float:
        raise TypeError("Device property reads are not supported yet.")

    @setpoint.setter
    @operation(id="example.heater.setpoint/v1")
    def setpoint(self, value: float) -> None:
        """Save the target temperature to apply when heating starts."""

    @operation(id=HOLD_ID)
    def hold(self, seconds: float) -> None:
        """Hold the saved setpoint for a duration."""


family = device_contract(Heater)
print("family:", family.type_id, "extends", list(family.base_type_ids))
print("properties:", [prop.semantic_id for prop in family.properties])
print("commands:", [command.semantic_id for command in family.operations])
```

<!-- tutorial: checkpoint -->
```text
family: example.heater/v1 extends ['sciloom.device/v1']
properties: ['example.heater.setpoint/v1']
commands: ['example.heater.hold/v1']
```

The imports at the top are everything the series will use; each name is
explained where it first matters. Four rules are doing work in the class.

The `device_type_id` is namespaced and versioned, and every device class needs
its own. It is the identity that reaches JSON, so it outlives your Python class.

A parameter is a property whose **setter** carries `@operation(id=...)`. Authors
then write `self.heater.setpoint = 60.0`, an assignment, rather than a `set_*`
method. The getter must exist so the types are declared in one place, and it
raises, because reading a device is not supported yet.

A command is a method carrying `@operation(id=...)` that returns `None` and takes
typed arguments. `float`, `int`, `bool`, physical quantities and homogeneous lists
of those are available; arbitrary Python objects are not, because the argument
has to survive serialization.

Bodies are never executed. `device_contract` reads the signatures and type hints
statically, which is why the printed contract exists before any target or
instrument does, and why a docstring is a complete implementation for a
declaration. The full rules are on [device contracts](../reference/device-contracts.md).

Next: [2. Declare profiles](declare-profiles.md).
