# Convert volumes and time intervals

Suppose a caller supplies a starting volume, a number of millilitres to add and
an elapsed time. This function returns the combined volume, the same amount as
a plain number of millilitres, and the difference from one minute.

`self.extra_ml * mL` attaches a unit to a runtime number. Dividing the result
by `mL` converts it back to a number. `Duration` can be negative when it represents
a difference; here 90 seconds produces a difference of −30 seconds.

```python
--8<-- "examples/quantity_conversion.py"
```

From a source checkout, run:

```console
uv run python examples/quantity_conversion.py
```

The command prints `quantity_conversion.asfp` and writes that file beside the
Python source. The generated function takes its inputs when called at runtime.

| Input | Value |
| --- | --- |
| `amount` | 1 mL |
| `extra_ml` | 2 |
| `elapsed` | 90 seconds |

The results are 3 mL, the number 3 and −30 seconds, subject to normal floating
rounding. This is a calculation example; it does not control equipment.

[Download Python](../_generated/examples/quantity_conversion.py) ·
[Download ASFP](../_generated/examples/quantity_conversion.asfp)

See [quantity rules](../user-guide/reference/runtime-language.md#physical-quantities)
for dimensional checks and current AutoSuite restrictions.
