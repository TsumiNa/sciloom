# Choose a device location at runtime

Use a Zone input when the caller should choose where a step runs. A logical
device still has an explicit deployment binding, but that binding lists the
controllers allowed for this step.

**Current support:** this program can be represented and reference-executed.
AutoSuite can check its deployment facts but rejects dynamic compilation with
`unsupported_device_location` until native failure propagation is verified.
Fixed bindings used in the tutorial continue to compile.

```python
from sciloom import Agitator, Function, Input, RotationalSpeed, Zone, at, runtime


class StirSelected(Function):
    shaker: Agitator
    location: Input[Zone]
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.shaker.speed = self.speed
        with at(self.shaker, self.location):
            self.shaker.start()
            self.shaker.stop()
```

The assignment saves the speed on the logical shaker. `at()` captures the current
Zone, checks it, then runs its body once. Changing `location` inside the body
does not redirect the active shaker. A child sharing the same logical device
inherits its selected location.

The Zone must be nonempty and wholly inside one allowed controller's wells.
Unknown wells, wells outside the candidate set and selections spanning several
controllers fail before the body runs. Exiting `at()` does not stop or restore
equipment: write the stop explicitly. Selecting B after starting A leaves A
running. Configuration is shared by the logical device, while each controller
retains its own applied configuration and running state.

Commands on a selection-bound device must run inside `at()`. Configuration
assignments may run outside. Do not nest another `at()` for the same logical
device, including through a child call. Different devices may have nested scopes.
Use one context per `with` statement, without an `as` name.

## Declare the allowed AutoSuite controllers

```python
from sciloom_autosuite import (
    AutoSuiteAgitatorSelection, AutoSuiteIndividualShaker,
    AutoSuiteLayout, AutoSuiteTarget,
)

target = AutoSuiteTarget(
    layout=AutoSuiteLayout.from_app("configuration.app"),
    devices={
        "shaker": AutoSuiteAgitatorSelection(candidates=(
            AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
            AutoSuiteIndividualShaker(zone="Heater Shaker 24", device_id="24"),
        )),
    },
)
```

Replace the example names and IDs with your deployment. The APP is read without
modification. SciLoom checks the wells' actual owners and their shaker ancestors;
a matching Zone name alone is insufficient. Candidate controllers must share
the same concrete device contract. Different logical devices cannot overlap
physical candidate sets. Share a logical reference when steps use one device.

A single candidate is allowed. An ordinary fixed binding remains useful for
programs without `at()`. Supplying `layout` for that binding adds the same
ancestry check; it does not alter the emitted fixed-device program.

For an executable reference example, see [physical device snapshots](../../examples/device-locations-ir.md).
