# Copy and scale a list

ScaleValues copies a typed numeric input list and multiplies each element by factor. Input [1, 2, 3] with factor 2.5 produces [2.5, 5, 7.5] under reference semantics, leaving the input unchanged.

## Run and inspect

```bash
uv run python examples/scale_values.py
```

The whole-list assignment establishes an independent output before the loop, including empty input. index is persistent Var state but is explicitly reset for each invocation. batch_size is ordinary host configuration; it is not used by this runtime algorithm and does not become an ASFP runtime field.

The module docstring below records expected terminal output. Compilation and
reference execution do not operate hardware or replace AutoSuite Executor checks.

## Source and generated files

[Download Python source](../_generated/examples/scale_values.py)

- [scale_values.asfp](../_generated/examples/scale_values.asfp)

```python
--8<-- "examples/scale_values.py"
```

