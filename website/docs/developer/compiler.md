# Compiler and specialization

`Function.compile(target=...)` first converts the instance to IR. The public
`compile_ir(program, target=...)` accepts directly constructed or JSON-loaded IR.

The shared compiler validates authored IR, resolves explicit device bindings,
specializes device branches, checks capabilities and definite configuration, then
calls Target.validate and Target.emit. Target resolution sees authored IR once;
validation and emission see the selected high-level program.

```python
from examples.scale_values import ScaleValues
from sciloom_autosuite import AutoSuiteTarget
from sciloom.core.compiler import compile_ir
from sciloom.core.ir import from_json, to_json
from sciloom.core.specialization import specialize

program = from_json(to_json(ScaleValues().to_ir()))
target = AutoSuiteTarget()
selected = specialize(program, bindings=target.resolve_devices(program))
result = compile_ir(program, target=target)
assert result.semantic_ir == program
assert result.specialized_ir == selected
assert result.artifact.media_type == "application/xml"
```

CompileResult retains semantic_ir, specialized_ir, target_id, artifact and
diagnostics. Artifact carries bytes, a media type and a file suffix. Its write
operation belongs to CompileResult. Backend-private variables/parameters never
enter either public semantic Program.

## Trusted bindings

DeviceBindings contains DeviceBinding facts: logical/physical identity, concrete
contract, complete base_contracts, writable property IDs and supported command IDs.
An empty envelope is valid only for a device-free program. Duplicate/missing/unknown
bindings, incompatible types and inconsistent ancestry are errors.

Specialization is a pure function: it retains source identity, selects device
branches and prunes unreachable functions, leaving the authored Program unchanged.
Serialized selected extensions must match the target's trusted contract directory.
Inactive extension branches do not require importing an implementation package.
No implementation is discovered or imported from a JSON identifier.

## AutoSuite boundary

The target validates platform restrictions and translates high-level operations
to a private serialization model. Property writes save configuration, start emits
Stir with the stored speed and enabled state, and stop emits the disabled state.
Hidden call parameters propagate shared device configuration without changing
author entry parameters. Context copyback follows normal function return; recovery
after exceptional termination is not promised equivalent across platforms.

Typed array encoding covers initialization, I/O binding, copies, lengths and
checked indexing. Static XML checks do not establish Executor acceptance. Semantic
JSON changes can change deterministic UUID hashes; compare structure rather than
claiming byte stability across semantic-contract revisions.
