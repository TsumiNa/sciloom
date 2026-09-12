# Device configuration and explicit agitation lifecycle

Device contracts define parameters and commands, Semantic IR describes the
experiment, and a Target binds logical dependencies to concrete equipment.
The [device refactor contract](refactor/device-abstraction/00-overview.md) is
authoritative. Property configuration and explicit lifecycle are implemented;
independent native commands also compile; device condition specialization is the next stage.

## Author interface

```python
from sciloom import Agitator, Function, Input, RotationalSpeed, runtime
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget

class Mix(Function):
    agitator: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.agitator.speed = self.speed
        self.agitator.start()

result = Mix().compile(target=AutoSuiteTarget(devices={
    "agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
}))
# The ASFP keeps the public speed input, captures it into private configuration
# storage, then emits Stir(switchon=1) using that saved value.
```

The executable [author example](../examples/agitation.py) adds conditional stopping
and writes its generated [ASFP companion](../examples/agitation.asfp). It does not
execute hardware. Runtime source currently comes from ordinary `.py` files.

`agitator: Agitator` is a device slot, separate from Input/Output/Var. Root slots
use field names; nested slots use paths such as `stage.agitator`. Assign an
existing logical reference during construction to share equipment:
`self.stage.agitator = self.agitator`. All declared slots on compiled Functions
require explicit target bindings. Different logical devices cannot alias the
same physical shaker or zone. Lowering does not mutate the author instance.

## Configuration and execution

| Operation | Effect |
|---|---|
| `device.speed = value` | Evaluate and save the value now; preserve applied configuration and running state |
| `device.start()` | Require complete configuration, apply the saved snapshot and enable; repeat to apply new values |
| `device.stop()` | Disable while preserving saved and last-applied values |
| Configure `0 * rpm` | Save a valid zero speed; stopping remains explicit |

Subsequent changes to the RHS variable do not change saved configuration. Device
values follow scalar/list copy rules. Configuration is shared across calls using
the same resource; resources and reference sessions are independent. Getter,
augmented assignment and indexed property updates are unsupported. Registered
parameters only use property assignment; set_speed and SetAgitation are removed.

The compiler proves required configuration using interprocedural guaranteed-write
and incoming-requirement summaries. Branch guarantees intersect; possibly empty
loops cannot establish configuration after the loop. Parent-configure/child-start
and child-configure/parent-start both work. Compilation assumes no earlier entry
calls. Reference execution can use actual retained state, and errors when start
lacks required configuration.

RotationalSpeed is finite and nonnegative. `600 * rpm == 10 * rps`; canonical IR
values use revolutions per second. Unitless numbers are not implicitly speeds.
Mypy checks property value types and command signatures; SciLoom additionally
checks schema roles, device capabilities and configuration completeness.

## IR and reference snapshots

JSON v4 stores DeviceResource declarations and a data-only DeviceTypeContract
directory. ConfigureProperty carries property identity and a typed value;
StartAgitation/StopAgitation preserve lifecycle intent. Versioned IDs never cause
Python imports. Native DeviceCommand compiles only when the bound device provides
the matching trusted signature and explicit capability. The external
[Demo contribution](../examples/developer/demo_contribution/__init__.py) adds gain,
calibration and a recording target. Reference execution of unknown native commands
fails explicitly. DeviceIf can be exchanged but compilation awaits specialization.

DeviceState exposes read-only `configuration`, `applied_configuration` and
`enabled`. Mapping keys are property names; physical values are quantities and
lists are tuples. DeviceEvent stores its node, resource, semantic operation ID
and detached state snapshot. Writes and lifecycle operations each produce an
event. No snapshot is telemetry. The [developer example](../examples/developer/agitation_ir.py)
shows saved values before start and preserved values after stop.

## AutoSuite mapping and limits

AutoSuiteIndividualShaker is a frozen Agitator deployment profile. It explicitly
declares writable/required speed and supported start/stop; inheritance alone does
not establish capabilities. The target resolves immutable binding facts once.
Shared validation checks bindings, capabilities and configuration before emission.

Stir submits speed and on/off together. The backend stages configuration in a
private variable, reads it for start, and emits switchon=0 for stop. It does not
stage configuration through a disabled Stir. Entry-owned storage passes through
private callee inputs/outputs; outputs first copy incoming state so unchanged
branches return it. These records do not enter public semantic IR or change the
author's entry signature. Wire zero initializers are not semantic configuration.

Private output copy-back occurs on normal return. Recovery after fatal callee
failure before copy-back has no equivalence guarantee. The stop task's inactive
editor speed is not saved configuration. Timing, getters, recovery and device
limits remain in the collected [Q&A](refactor/device-abstraction/qa.md).

[Mapping evidence](../autosuite/docs/16_AGITATION_MAPPING.md) separates observed
task/variable/parameter structures from composed transport behavior. Static XML
checks do not establish Executor acceptance, speed attainment or equivalence of
mixing mechanisms. No universal speed bounds, clamping, duration or real
measurement APIs are introduced here.
