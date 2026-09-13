# Composing Functions

Create child Function instances in the parent's constructor. Call those components
from its runtime method and assign the declared outputs to runtime fields.

The [complete function-call example](../examples/function-call.md) constructs an
Identity child, embeds the parent's host value `2.5`, and stores the returned value
in the parent's persistent `result` field.

Inputs may use positional or keyword binding; supply each input exactly once.
For one output, use one assignment destination. For multiple outputs, use tuple
destinations in declaration order. A standalone call requires a child with no
outputs. Indexed destinations for Function outputs are unsupported.

Calls copy inputs into fresh frames and write outputs back after normal return.
Internal child state persists across calls. Reusing the same child instance shares
that child's state; constructing another instance creates independent state.
Unused child components are omitted from the compiled instance graph.

## Sharing a logical device

Given parent and child Functions declaring compatible agitator slots, this host-
time constructor fragment shares the parent's logical device:

```python
def __init__(self) -> None:
    self.stage = ConfigureAgitation()
    self.stage.agitator = self.agitator
```

`ConfigureAgitation` is the class in the [agitation example](../examples/agitation.md).
Without sharing, a child's slot uses a component path such as `stage.agitator`.
With sharing, both procedures refer to one logical resource and one configuration
state. Bind the resulting resource explicitly through the target.

Compilation checks configuration across calls: a parent may configure a device
before a child starts it, and a child may configure it before the parent starts it.
The compiler must prove every required value was configured on every reachable
path; it cannot assume a previous entry invocation configured the device.
