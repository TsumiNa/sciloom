# Proposed frontend example code guide

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
