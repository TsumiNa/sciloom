# Stir a rack of samples

StirRack is the program the User Guide tutorial builds one class per page:
measure the largest volume in a rack, choose a speed for it, then configure and
start the bound shaker or stop it. This page is the runnable, downloadable form;
the [tutorial](../user-guide/tutorial/index.md) explains each step.

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
