# Execute three complete workflows from IR

These builders express the same procedures as the
[reagent table](read-reagent-table.md), [selected shaker](stir-selected-location.md)
and [well label log](label-sample-log.md) author examples. They construct typed
nodes directly, without analyzing Python source. Each program passes through an
independent Target, JSON serialization and restoration before reference execution.

```console
uv run python -m examples.developer.runtime_workflows_ir
```

```text
Reagent: reagent_A; IDs: ('E01', 'E02'); volumes: (1.5, 0.0) mL
Shaker: stopped after 5 s at 300 rpm
Label log: logs/2026-09-17_130000.csv; rows: 2
Contents: b'B:batch A\r\nA:batch A\r\n'
```

| Procedure | Explicit environment | Result |
|---|---|---|
| Reagent table | Sample CSV bytes in `MemoryFiles` | Heading plus aligned IDs and Volume lists |
| Selected shaker | Two candidate bindings, well directory and virtual monotonic clock | Only the selected controller runs; five seconds elapse before stop |
| Well label log | Well directory, property store, file store, aware wall clock and queued OK | Ordered property writes and two captured text records |

`ReferenceArchiveTarget` implements the existing `resolve_devices`, `validate`
and `emit` protocol. Its artifact is a reference JSON program, not an equipment
command file. It rejects `DeviceCommand`, whose contributor-defined native
behavior has no reference execution semantics. Common compilation still checks
types, bindings, specialization, configuration, timers and location scopes.

Only the shaker program receives device bindings; unused bindings would be an
error. Each workflow gets fresh mutable services. The CSV bytes are copied from
the project-authored fixture explicitly; the interpreter never reads host files
by default. The selected shaker is still running in its start event, and is
stopped in the final physical snapshot. The virtual wait does not sleep.

The tests compare outputs and ordered events across source, direct IR and JSON
paths. They also check empty data, repeated calls, rejected locations, absent
acknowledgements and partial file writes. A failed later write cannot undo a
completed label change or earlier file bytes. These checks establish SciLoom
reference behavior, not AutoSuite acceptance; the native gates remain active.

??? example "Complete builders, target and reference runner"

    ```python
    --8<-- "examples/developer/runtime_workflows_ir.py"
    ```

[Download Python](../_generated/examples/developer/runtime_workflows_ir.py) ·
[Sample CSV](../_generated/examples/read_reagent_table.csv) ·
[Reagent JSON](../_generated/examples/developer/runtime_workflows_ir.reagent.json) ·
[Shaker JSON](../_generated/examples/developer/runtime_workflows_ir.shaker.json) ·
[Label JSON](../_generated/examples/developer/runtime_workflows_ir.labels.json)
