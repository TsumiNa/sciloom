# Find the smallest qualifying value

`NonZeroArrayMin` scans a numeric list and finds the smallest value greater
than `1e-8`. Its initial result is `999999.0`; only a smaller qualifying
value replaces it.

Expected procedure results:

| Input `values` | Output `minimum` |
| --- | --- |
| `[0.0, 4.0, 2.0, 0.0]` | `2.0` |
| `[]` or `[0.0, 0.0]` | `999999.0` |
| `[1e-8, 3.0]` | `3.0` |
| `[1000000.0]` | `999999.0` |

Values at or below the threshold, including negative numbers, are ignored.
The result `999999.0` means no qualifying value smaller than that initial
value was found. It is not a general minimum over all possible floats.

## Read the loop

The method resets both the result and index on each call. The outer `if`
checks the threshold; the inner one checks whether the value improves the
current result. Nested conditions work with the AutoSuite target, which
currently refuses `and` and `or`.

This example adapts an original AutoSuite procedure. It retains its numeric
threshold and initial result, but removes the original volume unit. Its inputs
are dimensionless numbers; it performs no physical volume conversion.

## Compile the example

```bash
uv run python examples/non_zero_array_min.py
```

```text
non_zero_array_min.asfp
```

The Python command writes the package beside the source. AutoSuite supplies
`values` when calling the generated function. The results above describe the
algorithm under reference execution, not an instrument run. Validate the
package on the deployment computer before equipment use.

## Source and generated package

[Download Python source](../_generated/examples/non_zero_array_min.py) ·
[Download ASFP](../_generated/examples/non_zero_array_min.asfp)

```python
--8<-- "examples/non_zero_array_min.py"
```
