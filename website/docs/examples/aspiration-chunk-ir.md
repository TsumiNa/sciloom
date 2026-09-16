# Resume a volume calculation after JSON restoration

This runner converts [AspirationChunk](aspiration-chunk.md) from Python to IR,
writes the full JSON, restores it and executes two calls in one reference
session. The second call receives the first call's residual explicitly.

```console
uv run python -m examples.developer.aspiration_chunk_ir
```

```text
aspiration_chunk_ir.json
First: next=2, residual=3 mL, aspirate=4.25 mL
Resumed: next=3, residual=0 mL, aspirate=3.25 mL
```

The runner normalizes only diagnostic `SourceSpan.path` values to repository-relative
paths in a detached JSON document. Line numbers and semantic fields remain
unchanged. This makes the committed learning artifact portable; normal
compilation does not rewrite source paths.

This is a source-derived program, unlike the independent builders in
[the workflow example](runtime-workflows-ir.md). Tests cover partial fills, exact
capacity, the retained tolerance, group boundaries, empty and invalid inputs,
and reset behavior. No environment services are needed for this pure calculation.
There is no liquid-handling driver or simulated fluid transfer.

```python
--8<-- "examples/developer/aspiration_chunk_ir.py"
```

[Download runner](../_generated/examples/developer/aspiration_chunk_ir.py) ·
[Download author source](../_generated/examples/aspiration_chunk.py) ·
[Download JSON](../_generated/examples/developer/aspiration_chunk_ir.json)
