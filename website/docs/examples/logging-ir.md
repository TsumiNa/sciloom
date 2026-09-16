# Inspect a typed log event

Construct one volume log directly in IR, save and restore JSON, then run the
reference interpreter. The resulting event carries a Volume rather than a
formatted string. This example does not access files during reference execution
or send commands to equipment; the script itself writes the JSON companion.

```console
uv run python -m examples.developer.logging_ir
```

```text
logging_ir.json
recipe/volume: 1.0 mL
```

```python
--8<-- "examples/developer/logging_ir.py"
```

[Download Python](../_generated/examples/developer/logging_ir.py) ·
[Download JSON](../_generated/examples/developer/logging_ir.json)

LogValue stores the expression and both text labels; expression typing supplies
the result type. LogEvent records the captured public value. The
[execution reference](../developer/reference/interpreter.md#typed-log-events)
describes ordering and failure behavior.
