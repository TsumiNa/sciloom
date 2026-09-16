# Choose a reagent column

The table has experiment IDs in its first column and one column per reagent.
Supply `reagent_index=0` for reagent A or `1` for reagent B. The first read gets
the column heading; the second reads aligned IDs and volume lists.

```csv
--8<-- "examples/read_reagent_table.csv"
```

For reagent A the heading is `reagent_A`, IDs are E01 and E02, and volumes are
1.5 mL and 0 mL. The blank cell uses the explicit zero default. A file error does
not use that cell default.

```python
--8<-- "examples/read_reagent_table.py"
```

[Download Python](../_generated/examples/read_reagent_table.py) ·
[Download sample CSV](../_generated/examples/read_reagent_table.csv)

```console
uv run python examples/read_reagent_table.py
```

```text
AutoSuite CSV compilation awaits parser and failure validation.
```

This example verifies the compilation diagnostic and produces no ASFP. Its flow
is covered by reference tests. Developers can run the [CSV IR example](csv-read-ir.md)
to inspect data using an explicit in-memory file service.
See the [CSV reference](../user-guide/reference/csv.md) for read and error rules.
