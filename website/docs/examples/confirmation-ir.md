# Supply a reference confirmation

Construct a notification, restore it from JSON, and give the interpreter one
explicit OK response. This lets a test pass the confirmation step without
opening a dialog or relying on a human response.

```console
uv run python -m examples.developer.confirmation_ir
```

```text
confirmation_ir.json
Acknowledged: Samples are ready. Confirm to continue.
Responses remaining: 0
```

```python
--8<-- "examples/developer/confirmation_ir.py"
```

[Download Python](../_generated/examples/developer/confirmation_ir.py) ·
[Download JSON](../_generated/examples/developer/confirmation_ir.json)

Running the same session again raises `acknowledgement_required`: its one
response has already been consumed. Omitting the acknowledgement service raises
`missing_environment_service`. Neither failure proceeds to the next statement.
See [reference execution](../developer/reference/interpreter.md#explicit-confirmation)
for history and service ownership.
