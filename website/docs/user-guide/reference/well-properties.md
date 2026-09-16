# Sample labels stored on wells

Use a well user property to keep a sample identifier with its location. For
example, `sample_ID` can hold `batch A` for every well selected by the caller.
This is stored text, not a sensor reading.

Declare the property in the Function's `__init__`, then write with an ordinary
indexed assignment:

```python
from sciloom import WellProperty

# In __init__:
self.sample_label = WellProperty("sample_ID", str)

# In @runtime:
self.sample_label[self.rack] = self.label
```

The property name and type are fixed when Python builds the program. The caller
can supply `rack` and `label` at runtime. The assignment saves the current text
on every selected well; changing `label` afterward does not change stored labels.
An empty rack makes no changes. Wells retain separate values even when two Zones
overlap or two Functions refer to the same property name.

## Read one label

```python
self.previous = self.sample_label.get(self.well, default="")
```

`well` must contain exactly one well. The explicit default returns an empty
string when that well has no text value for `sample_ID`. Omit the default for a
strict read that fails instead. A default cannot recover an empty/multiple-well
selection or an unknown well. The selection and default are evaluated once at
the read, even if a stored value exists.

Declare `previous` as `Output[str]` or `Var[str]`. Keep the read as the entire
right-hand side of its assignment. To add a suffix, read first, then write
`self.previous = self.previous + "_checked"`. Indexed reads and `+=` writes are
not supported. Only text user properties are available in this first version.

## Compile for AutoSuite

The [label-wells example](../../examples/label-wells.md) writes a whole selection
and reads it back inside a single-well loop. AutoSuite compilation accepts writes
and reads with a default where the compiler can prove the selection contains one
well, such as the unchanged target of `for self.well in self.rack`.

Strict reads and other selections currently produce
`unsupported_well_property_read`: their failure checks still need platform
verification. Reference execution supports the full read contract. Compiled
packages use the observed user-property tasks; run the deployment's Executor
simulation before handing them to equipment.
