# Example code guide

## Runnable examples

| Audience | Example | Purpose |
|---|---|---|
| Experiment authors | [Function composition](../examples/function_call.py) | Define and compose Functions, then compile to ASFP |
| Experiment authors | [Conditional agitation](../examples/agitation.py) | Define runtime behavior and configure a compilation target |
| SciLoom developers | [Agitation IR](../examples/developer/agitation_ir.py) | Reuse the same Function; inspect, persist and reference-execute its IR |

Run user examples with `uv run python examples/function_call.py` and
`uv run python examples/agitation.py`. They only generate ASFP under `dist/`.
Run the developer example from the repository root with
`uv run python -m examples.developer.agitation_ir`; its JSON output is under
`dist/developer/`. None of these examples sends commands to hardware.

## Proposed frontend designs

The files in `examples/proposed_frontend/` are **architecture examples**, not an implemented public API. Names such as `sciloom.runtime`, `Input`, `Integer` and `Function` are placeholders used to make the intended source-language semantics concrete.

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
