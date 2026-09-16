# Append a sample label

Supply a file path and sample label when calling the generated function. The
function appends the label as one CSV cell. Commas, quotes and newlines in a label
remain part of that cell in reference execution.

```python
--8<-- "examples/append_sample_log.py"
```

[Download Python](../_generated/examples/append_sample_log.py)

```console
uv run python examples/append_sample_log.py
```

```text
AutoSuite CSV append awaits mode and encoding validation.
```

This checks the current compilation restriction and produces no ASFP. The
observed AutoSuite export setting still needs confirmation that it appends rather
than overwrites. For executable reference results, see the developer
[CSV append example](csv-append-ir.md). The [CSV reference](../user-guide/reference/csv.md#append-one-row)
describes existing-file requirements and failures.
