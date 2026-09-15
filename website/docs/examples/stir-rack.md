# Stir a rack of samples

StirRack is the completed program from the User Guide's five lessons. It finds
the largest supplied sample volume, chooses a speed, then starts or stops the
bound shaker. The [last lesson](../user-guide/tutorial/compile.md) adds a counter;
the [tutorial overview](../user-guide/tutorial/index.md) links all earlier versions.

## Run and inspect

```bash
uv run python examples/stir_rack.py
```

The program composes three child Functions: a loop with a persistent index that
is reset on every call, a two-branch speed choice, and a counter whose state
survives across calls. The parent binds their outputs by assignment, then either
saves the chosen speed and starts the shaker or stops it.

The module docstring below records expected terminal output.

--8<-- "website/snippets/hardware-boundary.md"

## Source and generated files

[Download Python source](../_generated/examples/stir_rack.py)

- [stir_rack.asfp](../_generated/examples/stir_rack.asfp)

```python
--8<-- "examples/stir_rack.py"
```
