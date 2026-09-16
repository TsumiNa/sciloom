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
| `selection[index]` | One-well Zone at a nonnegative integer position |
| `for self.well in self.rack` | Visit one well at a time, in selection order |
| `zones.fragments(self.rack, size=2)` | Visit complete groups of two inside a `for` loop |

`Var[Zone]` state persists across calls. Reset it explicitly if needed. Use
`len(self.selected) > 0` in a condition: Zones have no implicit truth value.
`list[Zone]`, arithmetic and whole-Zone comparisons are not supported. A well's
displayed number is not its position in a Zone: index `0` selects the first well,
even when its label ends in `27`. Boolean, negative and out-of-range indices fail.

## Visit the selected wells

Declare the current well as `Var[Zone]`, then use an ordinary `for` loop:

```python
--8<-- "examples/visit_locations.py"
```

The loop captures `rack` once. Reassigning `rack` inside it does not change the
remaining visits. Each iteration assigns the next well to `well` before running
the body. An empty rack skips the body and leaves `well` unchanged; after a
nonempty loop, its last value remains available, including across calls.

For pairs, replace the loop header with
`for self.well in zones.fragments(self.rack, size=2):`. The size must be a positive
integer literal or an ordinary host-time `self` attribute. A rack of four wells
produces two groups; three wells cause an error before any loop-body operation.
An empty rack produces no groups. There is no shorter final group.

Loop targets must be `Var[Zone]` fields, rather than inputs, outputs or newly
created Python names. `break`, `continue`, `for/else`, slices and coordinated
multi-Zone iteration are not supported.

## AutoSuite support

Use a [well user property](well-properties.md) to store text such as a sample
identifier on these locations. A property write can select several wells; a read
selects exactly one.

AutoSuite currently compiles Zone inputs, outputs, empty state, assignment,
`find`, `combine`, length queries and single-well `for` loops. It rejects indexing
and groups larger than one until reliable bounds/divisibility failure propagation
is verified. These operations already work in reference execution.
It also rejects nonempty host literals containing
opaque well IDs and `well_name`, whose single-well runtime check still needs
platform validation. Supply Zone parameters from AutoSuite or resolve names at
runtime. [Dynamic device selection with `at()`](device-locations.md) works in
reference execution; AutoSuite emission remains gated on verified runtime
failure propagation. Fixed hardware bindings keep their existing behavior.

The [location example](../../examples/resolve-locations.md) compiles a complete
function. The [developer example](../../examples/zone-ir.md) executes it against
an explicit directory without equipment. The [visit example](../../examples/visit-locations.md)
compiles a single-well loop; the [grouping example](../../examples/zone-traversal-ir.md)
demonstrates indexing and complete groups through reference execution.
