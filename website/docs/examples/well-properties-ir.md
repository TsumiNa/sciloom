# Execute well metadata operations

Build the same write/readback procedure as [Label selected wells](label-wells.md)
directly in IR. `WellPropertySpec` carries a fixed name and type;
`WriteWellProperty` and `ReadWellProperty` retain ordered external operations.
The property store is supplied separately from the immutable location directory.

```console
uv run python -m examples.developer.well_properties_ir
```

```text
well_properties_ir.json
Last label: batch A
Properties: {('rack/2', 'sample_ID'): 'batch A', ('rack/1', 'sample_ID'): 'batch A'}
```

??? example "Complete direct IR program"

    ```python
    --8<-- "examples/developer/well_properties_ir.py"
    ```

[Download Python](../_generated/examples/developer/well_properties_ir.py) ·
[Download JSON](../_generated/examples/developer/well_properties_ir.json)

`snapshot()` copies the store into a read-only mapping. Later writes do not alter
that snapshot or earlier event records. Passing the same environment to another
interpreter explicitly shares the stored labels; creating a new store isolates
them. Nothing in this example accesses equipment or host files.
