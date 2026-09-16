# Sample locations

Use a `Zone` to pass a selection of wells into or out of a Function. The wells
have a defined order and each appears once. A Zone identifies locations; it
does not bind or start a device.

```python
from sciloom import Function, Input, Output, Var, Zone, runtime, zones


class SelectLocations(Function):
    name: Input[str]
    extra: Input[Zone]
    selected: Output[Zone]
    count: Output[int]
    working: Var[Zone] = Zone.empty()

    @runtime
    def run(self) -> None:
        self.working = zones.find(self.name)
        self.selected = zones.combine(self.working, self.extra)
        self.count = len(self.selected)
```

The caller supplies `name` and `extra` when the generated function executes.
`find` uses the exact name in the location directory; an unknown name returns an
empty Zone. `combine` keeps the first Zone's wells, then adds previously absent
wells from the second in their original order. Assigning a Zone copies its value;
reassigning `working` later does not change `selected`.

| Operation | Result |
| --- | --- |
| `Zone.empty()` | No selected wells; also a valid `Var[Zone]` initial value |
| `zones.find(name)` | Named selection or an empty Zone |
| `zones.combine(left, right)` | Ordered union without duplicate wells |
| `len(selection)` | Well count, including zero for an empty Zone |
| `zones.well_name(selection)` | Display label of exactly one known well |

`Var[Zone]` state persists across calls. Reset it explicitly if needed. Use
`len(self.selected) > 0` in a condition: Zones have no implicit truth value.
`list[Zone]`, indexing, traversal, arithmetic and whole-Zone comparisons are not
supported in this stage. A well's displayed number is not its position in a Zone.

AutoSuite currently compiles Zone inputs, outputs, empty state, assignment,
`find`, `combine` and length queries. It rejects nonempty host literals containing
opaque well IDs and `well_name`, whose single-well runtime check still needs
platform validation. Supply Zone parameters from AutoSuite or resolve names at
runtime. Dynamic device selection with `at()` is not implemented yet; fixed
hardware bindings keep their existing behavior.

The [location example](../../examples/resolve-locations.md) compiles a complete
function. The [developer example](../../examples/zone-ir.md) executes it against
an explicit directory without equipment.
