# Capture a barcode for one well

This workflow validates a single known well, asks for text, saves that text as
sample_ID metadata and logs it. Empty text is a valid answer; the experiment may
choose additional validation. Cancel, Stop and timeout terminate before the
metadata write and log. No automatic default answer is supplied.

```python
--8<-- "examples/capture_barcode.py"
```

```console
uv run python examples/capture_barcode.py
```

Expected output: `AutoSuite barcode workflow awaits native dialog validation.`
The source language supports this workflow. AutoSuite compilation remains gated
pending native result/termination and dynamic single-well validation; this command
does not open a dialog or execute equipment.

For developers, run the equivalent direct IR with explicit services:

```console
uv run python -m examples.developer.barcode_ir
```

```text
barcode_ir.json
Barcode: S-001
Stored: S-001
Events: DialogEvent, WellPropertyWriteEvent, LogEvent
```

The complete JSON companion and deterministic responses specify reference
behavior. They do not establish Executor acceptance. See
[response services](../developer/reference/interpreter.md#text-and-yesno-responses).

[Author Python](../_generated/examples/capture_barcode.py) ·
[Developer Python](../_generated/examples/developer/barcode_ir.py) ·
[Complete JSON](../_generated/examples/developer/barcode_ir.json)
