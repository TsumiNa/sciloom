# JSON interchange and portability

A program's JSON is its portable form. It names the device family the author
wrote against, so the same file can be bound to different instruments by
different targets without going back to Python.

```python
from examples.developer.demo_contribution import DemoAgitator, DemoTarget
from examples.developer.portable_agitation import PortableAgitation
from sciloom.core.compiler import compile_ir
from sciloom.core.ir import from_json, to_json

program = PortableAgitation().to_ir()
text = to_json(program)
assert from_json(text) == program
assert to_json(from_json(text)) == text

selected = compile_ir(program, target=DemoTarget(devices={"agitator": DemoAgitator()})).specialized_ir
print("authored:", [contract.type_id for contract in program.device_types])
print("selected:", [contract.type_id for contract in selected.device_types])
```
```text
authored: ['sciloom.device/v1', 'sciloom.agitator/v1', 'example.demo-agitator/v1']
selected: ['example.demo-agitator/v1', 'sciloom.agitator/v1', 'sciloom.device/v1']
```

## What survives a round trip

Everything semantic: node ids, symbol ids, source spans, the device directory,
both branches of every device-dependent `if`. Export is deterministic, so a
program that was not changed produces the same bytes, and import validates, so a
file edited by hand is rejected at the first invalid field. The rules are
tabulated on [Semantic IR and JSON v4](../reference/ir.md).

## Why the authored file names the family

`PortableAgitation` asks `comptime.is_device(self.agitator, DemoAgitator)`, so
its authored directory carries the shipped agitator family and the demo
subclass side by side; nothing is selected yet. Binding it to `DemoTarget`
selects the branch and retypes the resource to the profile; binding the same
file to `AutoSuiteTarget` drops the branch, as the
[portable agitation example](../../examples/portable-agitation.md) shows with
both artifacts committed. Neither compilation touches the JSON, and neither
imports the other target's package: an inactive branch needs no implementation,
and no implementation is ever imported from a JSON identifier.

## Paths in committed files

Lowering records the absolute path of the defining file in every source span,
which identifies the generating checkout. The developer examples call
`repository_relative` from `examples/developer/source_paths.py` before writing
their companions, so the committed JSON is the same in every clone; that helper
is example support, not part of the SciLoom API.
