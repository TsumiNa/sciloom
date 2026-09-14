# An independent device contribution

DemoExperiment uses an independent DemoAgitator profile with speed, gain and a native calibrate command. DemoTarget records the selected semantic program as JSON.

## Run and inspect

```bash
uv run python -m examples.developer.demo_device
```

The emitted node sequence is ConfigureProperty, ConfigureProperty, StartAgitation, DeviceCommand, StopAgitation. The target conservatively accepts only literal gain values in [0, 1]. The extension adds a property and command without changes to core. calibrate has no reference execution semantics, so recording its request does not imply the interpreter or hardware can execute it. SourceSpan paths in the JSON are relative to the repository root, so the companion file is reproducible.

The module docstring below records expected terminal output.

--8<-- "website/snippets/hardware-boundary.md"

## Source and generated files

[Download Python source](../_generated/examples/developer/demo_device.py)

- [demo_device.json](../_generated/examples/developer/demo_device.json)

```python
--8<-- "examples/developer/demo_device.py"
```

## Independent contribution implementation

This implementation can live in a separate Python package. Its only SciLoom
imports are contributor contracts, and it performs no hardware I/O.

[Download contribution source](../_generated/examples/developer/demo_contribution/__init__.py)

```python
--8<-- "examples/developer/demo_contribution/__init__.py"
```

