# Native commands

Every command declared with `@operation`, except the two built-in agitation
lifecycle commands, becomes a `DeviceCommand` node: a semantic id and typed
arguments, nothing more. That includes an extension command on an `Agitator`
subclass, such as `DemoAgitator.calibrate`. Reference execution depends on the
declared contract: ordinary native commands have no defined reference effect,
while explicit lifecycle contracts define apply/disable behavior.

## What a command carries

The node records the operation's semantic id and its arguments, each a typed
expression: scalars, quantities and homogeneous lists, bound positionally or by
keyword the way Python binds them. A profile lists the command in
`supported_operations`; the capability check refuses a selected program that
calls a command its bound profile does not list. The declaration rules are on
[device contracts](../reference/device-contracts.md).

## Reference effects and ordinary native commands

The reference interpreter defines SciLoom semantics. Property writes have a
meaning for every family: the value is saved on the resource. A native command
has a meaning only on its hardware, so the interpreter raises `ExecutionError`
with `unsupported_operation` rather than invent one, as the tutorial's
[execute what you can](../tutorial/execute-what-you-can.md) page shows. That
example's `hold` and the independent contribution's `calibrate` are ordinary
`CommandContract` operations and still fail with
`unsupported_operation Cannot execute DeviceCommand.`

Agitation's dedicated start/stop nodes and explicit `LifecycleCommandContract`
operations have defined reference effects. Declare a parameterless command with
`@operation(id=..., lifecycle=LifecycleEffect.APPLY_AND_ENABLE)` to apply the
complete saved configuration and enable, or `LifecycleEffect.DISABLE` to disable
while preserving configuration. Explicit property requirements are checked
before either effect; apply also requires the concrete device's configuration.
The command name does not choose its effect. See the executable
[lifecycle contribution](../../examples/lifecycle-commands.md) and
[configuration rules](../reference/device-contracts.md#required-configuration).

## How AutoSuite lowers device intent

The shipped target validates platform restrictions and translates high-level
operations to a private serialization model. Property writes save configuration,
`start` emits Stir with the stored speed and enabled state, and `stop` emits the
disabled state. Hidden call parameters propagate shared device configuration
without changing author entry parameters. Context copyback follows normal
function return; recovery after exceptional termination is not promised
equivalent across platforms.

Typed array encoding covers initialization, I/O binding, copies, lengths and
checked indexing. A statement the package format has no form for is refused with
`unsupported_operation`. The shipped profile declares no commands beyond the
dedicated agitation lifecycle. New lifecycle `DeviceCommand` nodes are rejected
earlier by target validation with `unsupported_device_command`; direct task
emission also rejects them. Reference effects do not supply an AutoSuite adapter
or native evidence. Static XML checks do not establish Executor acceptance.
