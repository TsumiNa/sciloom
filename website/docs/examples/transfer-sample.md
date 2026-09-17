# Single-well transfer intent

Declare `liquid: LiquidHandler`, configure both flow rates and the air gap, then
call `transfer(source, destination, volume)`. Configuration writes save their
values without moving liquid. The command captures its three arguments once in
declared order and validates them before producing a transfer event.

```python
--8<-- "examples/transfer_sample.py"
```

Run `uv run python examples/transfer_sample.py`. It reports that the AutoSuite
transfer profile awaits native validation. The numbers illustrate typed intent;
they are not a validated process recipe.

For contributors, the example below adds a reference profile by subclassing
`LiquidHandler`, supplies fixed locations and a typed `TransferDeviceBinding`,
and compares Python, direct IR and JSON reference execution:

```python
--8<-- "examples/developer/transfer_sample_ir.py"
```

Run `uv run python -m examples.developer.transfer_sample_ir`. It writes the
complete `transfer_sample_ir.json` companion and reports a 0.25 mL transfer from
`well:source` to `well:destination`. The successful transfer is followed by a log.

Each argument must select one known, allowed well; source and destination must
differ. Volume and both flows must be positive, air gap nonnegative, and liquid
plus air gap must fit the explicit usable capacity. Missing facts or invalid
arguments stop execution before transfer and the following log. No tool,
channel, rinse setting or calibration is inferred for a real instrument.

The immutable transfer event records the applied configuration. Later writes
change saved settings; the next transfer applies them. There is no implicit
start/stop, inventory simulation, capacity splitting or precision guarantee.

| Layer | Status |
| --- | --- |
| Python, direct IR, JSON v4 | Implemented |
| Reference transfer intent | Implemented with explicit fixed binding and locations |
| AutoSuite static transfer generation | Gated pending verified tool profile and parameter encoding |
| Executor / instrument acceptance | Not verified |

[Author Python](../_generated/examples/transfer_sample.py) ·
[Contributor Python](../_generated/examples/developer/transfer_sample_ir.py) ·
[Complete JSON](../_generated/examples/developer/transfer_sample_ir.json)
