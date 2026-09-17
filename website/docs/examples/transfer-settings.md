# Transfer settings and typed locations

Flow rate and length express physical dimensions without embedding a vendor
tool or channel. This example calculates settings; it does not transfer liquid.

```python
--8<-- "examples/transfer_settings.py"
```

Run `uv run python examples/transfer_settings.py` to observe the explicit native
encoding gate. For developers, `uv run python -m examples.developer.transfer_values_ir`
compares source, direct IR, JSON and specialized reference execution. With
`factor=60`, it reports `Flow: 60.0 mL/min; clearance: 2.0 mm`.

The canonical values are 1e-6 m3/s and 0.002 m. These values support typed fields,
lists, arithmetic and explicit-unit CSV reads. See [physical values](../user-guide/reference/runtime-language.md#flow-and-length-values).

[Author Python](../_generated/examples/transfer_settings.py) ·
[Direct IR Python](../_generated/examples/developer/transfer_values_ir.py) ·
[Complete JSON](../_generated/examples/developer/transfer_values_ir.json)

## Contributor location arguments

`examples/developer/location_command_ir.py` extends `Agitator` by subclassing it
with an `inspect(source: Zone, destination: Zone, flow: FlowRate)` signature.
Run `uv run python -m examples.developer.location_command_ir`. The output lists
`source, destination, flow` in declaration order and reports that reference
execution rejects the unknown command. The contributor's target records JSON;
it does not implement hardware execution or claim AutoSuite compatibility.

Zone parameters use the same immutable well identities as other location values.
Properties remain scalar or homogeneous scalar lists; Zone properties and
`list[Zone]` are rejected. Defining a typed command alone does not supply an
effect. See [device contracts](../developer/reference/device-contracts.md).

[Contributor Python](../_generated/examples/developer/location_command_ir.py) ·
[Complete command JSON](../_generated/examples/developer/location_command_ir.json)
