# Record a sample and its volume

Keep a sample label next to a supplied volume in the generated program's log.
This function first records the label under `recipe/sample`, then uses that
label as the category for the volume record.

```console
uv run python examples/record_values.py
```

```text
record_values.asfp
```

The file appears beside the Python source. When AutoSuite calls the function
with `sample="A"` and `amount=1 mL`, its two records are `recipe/sample="A"`
and `A/volume=1 mL`. Change the inputs at the runtime call site, or change the
category/stream text in the source to organize the records differently.

These values come from the caller, not an instrument measurement. Compilation
does not execute the logging steps. The generated task mapping still needs
Executor verification of persisted values, units and text on the deployed host.

```python
--8<-- "examples/record_values.py"
```

[Download Python](../_generated/examples/record_values.py) ·
[Download ASFP](../_generated/examples/record_values.asfp)

See [recording rules](../user-guide/reference/runtime-language.md#record-values)
for supported types and argument evaluation order.
