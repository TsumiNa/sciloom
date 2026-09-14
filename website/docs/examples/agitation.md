# Configure and switch an agitator

ConfigureAgitation declares a logical agitator and two runtime inputs. The target binds that resource to Heater Shaker 23.

## Run and inspect

```bash
uv run python examples/agitation.py
```

When enabled is true, the procedure captures shaker_speed and explicitly starts agitation. Otherwise it stops. Assignment alone never starts the device, and zero speed is not a stop. The source's XML excerpts are abbreviated; the companion is the complete generated package. This is a focused operation from an original workflow, not a reproduction of the full experiment.

The module docstring below records expected terminal output.

--8<-- "website/snippets/hardware-boundary.md"

## Source and generated files

[Download Python source](../_generated/examples/agitation.py)

- [agitation.asfp](../_generated/examples/agitation.asfp)

```python
--8<-- "examples/agitation.py"
```

