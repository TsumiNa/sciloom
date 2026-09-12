# Example code guide

## Runnable examples

| Audience | Example | Purpose |
|---|---|---|
| Experiment authors | [Function composition](../examples/function_call.py) | Define and compose Functions, then compile to ASFP |
| Experiment authors | [Conditional agitation](../examples/agitation.py) | Define runtime behavior and configure a compilation target |
| SciLoom developers | [Agitation IR](../examples/developer/agitation_ir.py) | Reuse the same Function; inspect, persist and reference-execute its IR |
| SciLoom developers | [Independent device](../examples/developer/demo_device.py) | Extend properties/commands and compile with an external recording Target |
| SciLoom developers | [Portable agitation](../examples/developer/portable_agitation.py) | Rebind authored JSON to AutoSuite/Demo; inspect and execute specialized IR |

Run user examples with `uv run python examples/function_call.py` and
`uv run python examples/agitation.py`. Their complete generated outputs are
[function_call.asfp](../examples/function_call.asfp) and
[agitation.asfp](../examples/agitation.asfp), beside their source files.
Run the developer example from the repository root with
`uv run python -m examples.developer.agitation_ir`; it writes
[agitation_ir.json](../examples/developer/agitation_ir.json) beside its source.
The module docstrings show the expected terminal output and explain each result.
Rerunning an example refreshes its companion file. Source-location metadata in
the JSON reflects the generating checkout. None of these examples sends commands
to hardware.

Run `uv run python -m examples.developer.demo_device` and
`uv run python -m examples.developer.portable_agitation` for contributor and
device-specialization examples. Portable agitation keeps its authored `.json`
alongside `.autosuite.asfp` and `.demo.json` target artifacts. All share the source
base name, and the module docstrings explain their expected outputs.

For implemented direct list semantics, run
`uv run python -m examples.developer.list_ir`. Its
[source](../examples/developer/list_ir.py) and [JSON](../examples/developer/list_ir.json)
show copying and element updates with JSON v4. This is a developer example;
Python list authoring and AutoSuite generation are implemented. Run
`uv run python examples/scale_values.py` and
`uv run python examples/non_zero_array_min.py` for author examples with complete
same-name ASFP companions. The latter removes volume units from the original
Non Zero Array Min algorithm; it is a numeric adaptation.

## Proposed frontend designs

The files in `examples/proposed_frontend/` are **architecture examples**, not
runnable applications. Function, Input/Output/Var and runtime are implemented;
Application, Zone/Volume, event/fault handling and the illustrative task calls
remain proposed. These examples use the current native declaration spelling
but do not establish support for those future operations.

- `01_minimal_function.py` — class-level runtime schema, instance construction and `instance.compile()`.
- `02_dynamic_transfer.py` — native `while`/`if`, arrays, units and AutoSuite function/task calls.
- `03_instance_specialization.py` — `__init__` as ordinary Python host-time specialization; no `@comptime` decorator.
- `04_error_handling.py` — fatal structured handler using `except ... raise` and a separate recoverable result-style branch.
- `05_application_events.py` — Main/OnStart/OnError/OnStop semantic roles.
- `06_ir_projection.json` — illustrative normalized semantic graph independent of Python formatting.
- `07_xyflow_view_projection.json` — illustrative GUI-only layout keyed by semantic `node_id`.
- `08_error_lowering_ir.json` — illustrative fatal fault-region IR and proposed lowering hint.
- `09_class_schema_and_instance.py` — class-schema introspection versus specialized instance values.

These examples are intentionally independent of exact AutoSuite XML IDs. The serialization backend is responsible for target IDs and schema mechanics.
