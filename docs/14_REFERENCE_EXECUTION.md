# Reference execution

`LiquidHandler.transfer` has bounded reference semantics using explicit
`TransferDeviceBinding` facts from `sciloom.core.bindings` and an explicit
`ReferenceEnvironment.locations` directory. It captures source, destination and
volume once in declared order, checks distinct allowed single wells, positive
volume/flows, nonnegative air gap and usable capacity before recording a
`TransferEvent`. All three family settings plus concrete profile requirements
must be configured. Saved configuration persists across calls; successful
transfer updates last-applied snapshots without changing enabled state. Failed
transfers leave applied state and transfer history unchanged and stop later
effects. This models intent, not liquid inventory or physical precision.
See `examples/developer/transfer_sample_ir.py` for source/direct-IR/JSON parity.

The current handbook is maintained in [Reference execution semantics](../website/docs/developer/reference/interpreter.md).
This file is an index for existing repository links; update the handbook when
behavior changes, rather than maintaining a second current description here.

See the [documentation index](INDEX.md) for internal design history and reference
material. Proposed frontend examples are not supported runtime APIs.
