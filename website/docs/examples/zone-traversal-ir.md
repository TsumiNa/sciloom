# Execute Zone indexing and grouped traversal

Read the first well of a four-well selection, then visit it in pairs. The direct
IR uses `ZoneGet` and `ForEachZone`; JSON v4 retains both operations. Reference
execution needs no location directory for indexing or grouping supplied values.

```console
uv run python -m examples.developer.zone_traversal_ir
```

```text
zone_traversal_ir.json
First well: ('well:27',)
Groups: 2
Last group: ('well:8', 'well:2')
```

??? example "Complete program"

    ```python
    --8<-- "examples/developer/zone_traversal_ir.py"
    ```

[Download Python](../_generated/examples/developer/zone_traversal_ir.py) ·
[Download JSON](../_generated/examples/developer/zone_traversal_ir.json)

The loop captures the ordered selection once and validates divisibility before
its first target write. An incomplete group raises an execution error without
running the body. An earlier assignment, such as selecting the first well, is
not rolled back. Empty input skips indexing through the explicit condition and
skips the loop, preserving the previous fragment.

AutoSuite currently accepts single-well traversal, demonstrated in
[Visit sample locations](visit-locations.md). Indexing and grouped traversal
remain target diagnostics until runtime failure propagation is verified.
