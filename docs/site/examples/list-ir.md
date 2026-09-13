# Construct list IR directly

Build a typed Program directly, round-trip JSON and execute it without Python DSL lowering. The procedure copies a list, then changes the first element to 9.

## Run and inspect

```bash
uv run python -m examples.developer.list_ir
```

The read-only result exposes (9.0, 2.0); the caller's input remains [1.0, 2.0]. ListType describes the element type, Assignment copies the whole value and ListSet retains indexed-write intent. Every node occurrence has its own ID, while references share the destination symbol's ID. The example emits JSON, not equipment commands.

The module docstring below records expected terminal output. Compilation and
reference execution do not operate hardware or replace AutoSuite Executor checks.

## Source and generated files

[Download Python source](../_generated/examples/developer/list_ir.py)

- [list_ir.json](../_generated/examples/developer/list_ir.json)

```python
--8<-- "examples/developer/list_ir.py"
```

