# Target contract

A target turns a selected program into a platform artifact. Independent packages
use the same public interfaces as the shipped `sciloom-autosuite` member; no
plugin registry or namespace installation is required. This page is the
reference; the walkthrough is [write a target](../tutorial/write-a-target.md), and device
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
| `resolve_devices` | `(program: Program) -> DeviceBindings` | answers each declared DeviceResource from the target's own deployment data; sees the authored program |
| `validate` | `(program: Program) -> tuple[Diagnostic, ...]` | returns diagnostics for what the platform cannot do; sees the selected program |
| `emit` | `(program: Program) -> Artifact` | returns bytes, a media type and a suffix, never a hardware connection |

`Artifact(content, media_type, suffix)` is immutable; `CompileResult.write(path)`
writes its bytes. A target rejects only what it can prove: an unprovable
declared limit is a rejection, never a clamp.

## Bindings

`resolve_devices` returns `DeviceBindings`. Each entry is a fixed `DeviceBinding`
or a `DeviceSelectionBinding` with explicit candidates. For a fixed profile,
`bind_device(logical_id=..., device=..., physical_id=...)` builds this record:

| Field | Meaning |
|---|---|
| `logical_id` | the slot name the program used: a field name or component path |
| `physical_id` | the target-defined identity of the instrument |
| `contract` | the profile's trusted data contract |
| `base_contracts` | the complete ancestor directory, family and `BaseDevice` included |
| `writable_properties` | semantic ids the profile accepts writes to |
| `supported_operations` | semantic ids the profile runs |

A selection wraps each fixed binding in `DeviceCandidate(binding=..., wells=...)`
and supplies the tuple to `DeviceSelectionBinding(logical_id=..., candidates=...)`.
Candidates share one concrete contract, ancestor directory and capability sets.
They have distinct physical identities and disjoint nonempty well sets. The
selection exposes the common contract/capabilities but has no single `physical_id`.
Physical actuator identities cannot overlap across logical resources. Well sets
may overlap between different logical selections with distinct trusted actuators;
within one selection they remain disjoint so a Zone resolves to one controller.

`DeviceAt` captures a Zone for a selection-bound resource. Shared compilation
checks its scope across function calls; a target must implement it or return an
explicit unsupported diagnostic. The [complete workflow example](../../examples/runtime-workflows-ir.md)
shows both a selection binding and an independent reference-archive target.

| Rule | Detail |
|---|---|
| empty envelope | valid only for a device-free program |
| coverage | every DeviceResource needs exactly one compatible binding; a binding with no device resource, a duplicate logical or physical id, or a conflicting contract for one type id is an error |
| trust | the compiler substitutes the binding's contracts for the serialized ones; a serialized contract that differs from the trusted one is `device_contract` |
| purity | specialization is a pure function of the program and the bindings: it selects device branches, prunes unreachable functions and their timers, and retypes device resources, leaving the authored program unchanged |
| no discovery | inactive branches need no implementation package; no implementation is imported from a JSON identifier |

Function-owned TimerResource records need no device binding. Targets must either
implement their timing statements or report a specific unsupported capability.
Shared compilation proves timer starts on all relevant paths; native timer
visibility and duration limits remain target checks.

Capabilities may use scalar, quantity and list value types only; no arbitrary
Python objects or dynamic imports enter JSON. A registered native command is not
automatically executable by the reference interpreter.
