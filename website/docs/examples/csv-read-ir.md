# Execute a typed CSV read

Construct ReadCsv directly, restore it from JSON v4, and provide fixed bytes with
MemoryFiles. The two lists stay aligned when an empty volume cell uses a default.

```console
uv run python -m examples.developer.csv_read_ir
```

```text
csv_read_ir.json
IDs: ('E01', 'E02')
Volumes (mL): (1.5, 0.0)
Status: DEFAULT_USED
```

```python
--8<-- "examples/developer/csv_read_ir.py"
```

[Download Python](../_generated/examples/developer/csv_read_ir.py) ·
[Download JSON](../_generated/examples/developer/csv_read_ir.json)

The quantity unit in CsvColumn is a typed literal containing the SI value of one
input unit: `1e-6` m³ for millilitres. A default is already in canonical units.
STATUS mode puts an integer destination before the column destinations.

Reference execution records one CsvReadEvent with captured selectors and outcome,
including failed read attempts. It does not record file bytes or mutable result
arrays. AutoSuite compilation remains unavailable until its parser and error
behavior can satisfy this contract.
