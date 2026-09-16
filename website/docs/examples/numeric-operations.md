# Calculate whole portions and a volume difference

Use this function to calculate how many whole 1 mL portions fit in a supplied
volume, then find its absolute difference from a reference volume.
It performs calculations only; it does not transfer or measure liquid.

| Inputs | Results when the function runs |
| --- | --- |
| `amount = 2.5 * mL`, `reference = 3 * mL` | `whole_portions = 2`, `difference = 0.5 * mL` |

`self.amount / mL` converts the quantity to a number before `floor` rounds down.
`abs(self.amount - self.reference)` keeps the volume unit and removes the sign
of the difference. Quantity arithmetic uses ordinary floating rounding.

```python
--8<-- "examples/numeric_operations.py"
```

From a source checkout, run:

```console
uv run python examples/numeric_operations.py
```

The command prints `numeric_operations.asfp` and writes the file beside the Python
source. AutoSuite supplies the inputs when it calls the generated function.

[Download Python](../_generated/examples/numeric_operations.py) ·
[Download ASFP](../_generated/examples/numeric_operations.asfp)

See [numeric function rules](../user-guide/reference/runtime-language.md#numeric-functions)
for result types and the current restriction on nearest-integer rounding.
