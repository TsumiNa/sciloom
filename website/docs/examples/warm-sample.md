# Fixed heater intent

Declare a `Heater` dependency, assign both its absolute `temperature` and
`ramp_rate`, then explicitly call `start()` and `stop()`. Setting a property saves
the value at assignment; it does not change already applied settings. Calling
`start()` again applies the complete updated configuration. Stopping retains
both saved and last-applied values.

```python
--8<-- "examples/warm_sample.py"
```

```sh
uv run python examples/warm_sample.py
```

This command reports that the AutoSuite heater profile awaits native validation.
The numerical settings illustrate the language, not a process recipe. A fixed
ten-second wait does not mean the target temperature was reached. There are no
temperature getters or feedback control in this family.

For contributors, the complete example below declares a fixed reference profile
and an independent recording target, builds the same flow directly in IR, and
compares its state with the Python program using an explicit virtual clock:

```python
--8<-- "examples/developer/warm_sample_ir.py"
```

```sh
uv run python -m examples.developer.warm_sample_ir
```

It writes `warm_sample_ir.json` and reports 10 seconds elapsed, heater disabled,
and a retained target of 293.15 K. This records ordered intent, not physical
heat transfer or a measured temperature. The recording target emits JSON only.

| Layer | Status |
| --- | --- |
| Python, direct IR, JSON v4 | Implemented |
| Reference state and event order | Implemented with explicit fixed binding and virtual clock |
| AutoSuite thermal profile and static emission | Gated pending exact native mapping |
| Executor / instrument acceptance | Not verified |

Extend Heater through a subclass when an instrument needs additional properties
or registered operations; do not modify Heater or BaseDevice for that instrument.
Required additional properties must be configured before an applying command.
Use fixed `DeviceBinding` facts; heater candidate selection is currently rejected,
including for derived contracts. Unknown commands still require defined semantics.

[Download author Python](../_generated/examples/warm_sample.py) ·
[Download contributor Python](../_generated/examples/developer/warm_sample_ir.py) ·
[Download direct IR JSON](../_generated/examples/developer/warm_sample_ir.json)

See [temperature values](temperature-values.md) and [device contracts](../api/devices.md).
