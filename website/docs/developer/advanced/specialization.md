# Specialization internals

`specialize(program, bindings)` is the step that turns the authored program into
the selected one. It is a pure function of its two arguments and never imports
a device implementation.

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

## What it does, in order

1. Validates the authored program.
2. Validates the bindings against it: every declared resource has one compatible
   binding, no binding is stray, and no two bindings disagree about a type
   (`missing_resource_binding`, `unknown_resource_binding`, `device_type`,
   `device_contract`).
3. Answers every device-dependent `if` from the binding of its resource:
   `IsDevice` by the profile's type and ancestry, `CanWrite` by its writable
   properties, `SupportsOperation` by its supported operations. The winning
   branch is spliced inline; the other is dropped. A query about a resource with
   no binding is an error even when its answer would have been false.
4. Prunes functions that no longer have a caller.
5. Retypes each resource to the bound profile's type and rebuilds the device
   directory from the bindings' trusted contracts, discarding the serialized
   ones. A selected query whose signature differs from the trusted contract is
   `device_contract`.
6. Validates the result.

Node ids and source spans survive, so a diagnostic raised later still points at
the author's line. The authored program is left unchanged and is returned as
`CompileResult.semantic_ir`; the tutorial's
[adapt with comptime](../tutorial/adapt-with-comptime.md) page shows the
selected bodies for two profiles.
