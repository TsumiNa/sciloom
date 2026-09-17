# Temperature values

An absolute temperature and a temperature difference are distinct types.
`20 * degC + 5 * delta_degC` gives 25°C, stored as 298.15 K. Subtracting two
absolute temperatures produces a signed difference. A rate such as
`60 * degC_per_min` stores 1 K/s.

```python
--8<-- "examples/temperature_values.py"
```

Run the host-value example:

```sh
uv run python examples/temperature_values.py
```

It prints a target of 298.15 K, change of 5 K and rate of 1 K/s. The Function
declares typed runtime fields; its `saved` target persists across calls.

For developers, run the JSON/reference companion:

```sh
uv run python -m examples.developer.temperature_ir
```

It returns a 5 K change on the first call and 0 K on the identical second call.
The JSON still declares `format_version: 4`. No device is controlled: native
thermal encoding remains gated, and a supplied temperature is not a measurement.

[Download author Python](../_generated/examples/temperature_values.py) ·
[Download developer Python](../_generated/examples/developer/temperature_ir.py) ·
[Download JSON](../_generated/examples/developer/temperature_ir.json)

See [temperature rules](../user-guide/reference/runtime-language.md#temperature-values)
and the [units API](../api/units.md).
