# A numerical minimum algorithm

NonZeroArrayMin finds the smallest element greater than 1e-8 and below the initial sentinel 999999. For [0, 4, 2, 0], the reference result is 2; empty or all-zero input returns 999999.

## Run and inspect

```bash
uv run python examples/non_zero_array_min.py
```

This is a dimensionless adaptation of the retained Non Zero Array Min procedure from config20260909_polymerization.app. It removes the original volume unit while retaining the numerical threshold and sentinel. Values at or below the threshold are ignored; values above the sentinel do not replace it. Nested if statements preserve the intended conditional evaluation on AutoSuite without using unverified and/or lowering.

The module docstring below records expected terminal output. Compilation and
reference execution do not operate hardware or replace AutoSuite Executor checks.

## Source and generated files

[Download Python source](../_generated/examples/non_zero_array_min.py)

- [non_zero_array_min.asfp](../_generated/examples/non_zero_array_min.asfp)

```python
--8<-- "examples/non_zero_array_min.py"
```

