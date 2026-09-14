# Target contract

A target turns a selected program into a platform artifact. Independent packages
use the same public interfaces as the shipped `sciloom-autosuite` member; no
plugin registry or namespace installation is required. This page is the
reference; the walkthrough is [add a target](../add-a-target.md), and device
declarations are on [device contracts](device-contracts.md).

## A minimal target

This complete target accepts a device-free program and emits a textual summary:

```python
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import FunctionIR, Program


class SummaryTarget:
    target_id = "example.summary/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings()

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=f"functions={len(program.functions)}\n".encode(),
                        media_type="text/plain", suffix=".txt")


program = Program(entry_function_id="empty", functions=(FunctionIR(node_id="empty", name="Empty"),))
assert compile_ir(program, target=SummaryTarget()).artifact.content == b"functions=1\n"
```

It has the same four members as the tutorial's `BenchTarget`; that target adds
deployment data checked in its constructor, real bindings and a platform rule in
`validate`. A target is recognised structurally: it implements the four members, and no
target base class is required.

## Members

| Member | Signature | Contract |
|---|---|---|
| `target_id` | `str` | a namespaced, versioned identifier recorded in `CompileResult` |
| `resolve_devices` | `(program: Program) -> DeviceBindings` | answers each declared resource from the target's own deployment data; sees the authored program |
| `validate` | `(program: Program) -> tuple[Diagnostic, ...]` | returns diagnostics for what the platform cannot do; sees the selected program |
| `emit` | `(program: Program) -> Artifact` | returns bytes, a media type and a suffix, never a hardware connection |

`Artifact(content, media_type, suffix)` is immutable; `CompileResult.write(path)`
writes its bytes. A target rejects only what it can prove: an unprovable
declared limit is a rejection, never a clamp.

## Bindings

`resolve_devices` returns `DeviceBindings`, an envelope of `DeviceBinding`
records that `bind_device(logical_id=..., device=..., physical_id=...)` builds
from a profile:

| Field | Meaning |
|---|---|
| `logical_id` | the slot name the program used: a field name or component path |
| `physical_id` | the target-defined identity of the instrument |
| `contract` | the profile's trusted data contract |
| `base_contracts` | the complete ancestor directory, family and `BaseDevice` included |
| `writable_properties` | semantic ids the profile accepts writes to |
| `supported_operations` | semantic ids the profile runs |

| Rule | Detail |
|---|---|
| empty envelope | valid only for a device-free program |
| coverage | every declared resource needs exactly one compatible binding; a binding with no resource, a duplicate logical or physical id, or a conflicting contract for one type id is an error |
| trust | the compiler substitutes the binding's contracts for the serialized ones; a serialized contract that differs from the trusted one is `device_contract` |
| purity | specialization is a pure function of the program and the bindings: it selects device branches, prunes unreachable functions and retypes resources, leaving the authored program unchanged |
| no discovery | inactive branches need no implementation package; no implementation is imported from a JSON identifier |

Capabilities may use scalar, quantity and list value types only; no arbitrary
Python objects or dynamic imports enter JSON. A registered native command is not
automatically executable by the reference interpreter.
