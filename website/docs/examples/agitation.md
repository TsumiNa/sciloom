# Start or stop an agitator

Use this procedure when the caller supplies both a requested speed and an
enable/disable choice. The logical device is named `agitator`; the target maps
it to the example AutoSuite shaker.

When the generated function is called:

| Inputs | Behaviour |
| --- | --- |
| `shaker_speed=600*rpm`, `enabled=True` | Save the supplied speed, then start |
| `shaker_speed=300*rpm`, `enabled=False` | Stop; leave the saved speed unchanged |

Both inputs are required on either branch. The speed supplied on a stop call
is not applied. Assigning a property saves its value; only `start()` applies
it, and only `stop()` disables agitation.

## Compile for your shaker

```bash
uv run python examples/agitation.py
```

```text
agitation.asfp
```

Change the `zone` and `device_id` in the target to match your AutoSuite
configuration. They identify a zone and an individual shaker, not a sample.
The runtime inputs remain parameters of the generated function.

The package is written beside the source. Before equipment use, validate it
with AutoSuite Executor on the deployment computer. Compilation does not
operate the shaker. See [binding and validation](../user-guide/advanced/autosuite.md).

## Source and generated package

[Download Python source](../_generated/examples/agitation.py) ·
[Download ASFP](../_generated/examples/agitation.asfp)

```python
--8<-- "examples/agitation.py"
```
