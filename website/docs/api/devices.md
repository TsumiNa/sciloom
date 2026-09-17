# Device declarations

[Device contracts](../developer/reference/device-contracts.md) explains declarations and the [Target contract](../developer/reference/target-contract.md) trusted deployment facts.

::: sciloom.devices.BaseDevice

::: sciloom.Heater

::: sciloom.LiquidHandler

::: sciloom.core.bindings.TransferDeviceBinding

LiquidHandler provides bounded reference transfer intent with explicit fixed
deployment facts. Native transfer remains gated. See the
[single-well transfer example](../examples/transfer-sample.md).

Heater has core/reference semantics for fixed bindings. Both `temperature` and
`ramp_rate` are required before start; native AutoSuite mapping is still gated.
See the [complete author/contributor example](../examples/warm-sample.md).

::: sciloom.devices.operation

::: sciloom.devices.declarations.device_contract

::: sciloom.devices.declarations.bind_device
