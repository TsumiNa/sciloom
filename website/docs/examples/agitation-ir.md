# Persist and reference-execute agitation

This developer example reuses the author-facing agitation Function, writes JSON v4, restores it, and exercises configuration/start/stop in one reference session.

## Run and inspect

```bash
uv run python -m examples.developer.agitation_ir
```

At the configuration event, saved speed is 600 rpm while applied configuration is empty. After start, both are 600 rpm; stop clears enabled while retaining saved and applied values. The first result remains unchanged after the second run. JSON persistence is an intentional interchange test, not a required step before interpretation. SourceSpan paths in the downloadable JSON are relative to the repository root, so regenerating it in another checkout produces the same file.

The module docstring below records expected terminal output. Compilation and
reference execution do not operate hardware or replace AutoSuite Executor checks.

## Source and generated files

[Download Python source](../_generated/examples/developer/agitation_ir.py)

- [agitation_ir.json](../_generated/examples/developer/agitation_ir.json)

```python
--8<-- "examples/developer/agitation_ir.py"
```

