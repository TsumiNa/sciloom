# Native commands

Every command declared with `@operation`, except the two built-in agitation
lifecycle commands, becomes a `DeviceCommand` node: a semantic id and typed
arguments, nothing more. That includes an extension command on an `Agitator`
subclass, such as `DemoAgitator.calibrate`. The node is enough to serialize,
bind and emit, and not enough to execute.

## What a command carries

The node records the operation's semantic id and its arguments, each a typed
expression: scalars, quantities and homogeneous lists, bound positionally or by
keyword the way Python binds them. A profile lists the command in
`supported_operations`; the capability check refuses a selected program that
calls a command its bound profile does not list. The declaration rules are on
[device contracts](../reference/device-contracts.md).

## Why the interpreter refuses it

The reference interpreter defines SciLoom semantics. Property writes have a
meaning for every family: the value is saved on the resource. A native command
has a meaning only on its hardware, so the interpreter raises `ExecutionError`
with `unsupported_operation` rather than invent one, as the tutorial's
[execute what you can](../tutorial/execute-what-you-can.md) page shows. Only
agitation's `start` and `stop` have reference semantics, because they are
dedicated nodes with a defined effect on saved and applied configuration.

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
`unsupported_operation`; today that is any `DeviceCommand`, because the shipped
profile declares no commands beyond the agitation lifecycle. Static XML checks do
not establish Executor acceptance.
