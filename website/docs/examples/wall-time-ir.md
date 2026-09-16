# Supply a reference wall clock

Use a fixed, timezone-aware instant to make timestamp tests reproducible.
This example constructs ReadWallTime directly, restores the program from JSON,
and records one completed read.

```console
uv run python -m examples.developer.wall_time_ir
```

```text
wall_time_ir.json
2026-09-16_140506
Wall-time reads: 1
```

```python
--8<-- "examples/developer/wall_time_ir.py"
```

[Download Python](../_generated/examples/developer/wall_time_ir.py) ·
[Download JSON](../_generated/examples/developer/wall_time_ir.json)

The supplied instant has UTC+09:00 as its offset. Formatting uses its calendar
fields without consulting the computer's timezone or locale. Call `clock.set()`
to change the instant before another run; earlier events retain their text.
Omitting the service raises `missing_environment_service` at the read.
See [reference clocks](../developer/reference/interpreter.md#wall-clock-input).
