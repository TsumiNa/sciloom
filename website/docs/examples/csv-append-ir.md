# Execute a CSV append

Build an AppendCsv node, restore it from JSON, and call it twice with MemoryFiles.
The second call keeps the first record. No CSV file is written to the host disk.

```console
uv run python -m examples.developer.csv_append_ir
```

```text
csv_append_ir.json
File bytes: b'"sample,A"\r\n"sample,A"\r\n'
Append events: 2
```

```python
--8<-- "examples/developer/csv_append_ir.py"
```

[Download Python](../_generated/examples/developer/csv_append_ir.py) ·
[Download JSON](../_generated/examples/developer/csv_append_ir.json)

AppendCsv captures path and values in order, then makes one append_bytes call.
CsvAppendEvent holds the requested typed row and its status. It does not assert
that every byte reached storage when a write failed partway through.

With CsvErrorPolicy.STATUS, bind status to an integer Reference. File errors
produce IO_ERROR and allow later statements; ordinary appends raise after
recording the failed attempt. Neither form rolls back partial writes or retries.
Reference snapshots remain immutable across subsequent calls.
