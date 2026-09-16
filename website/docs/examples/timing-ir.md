# Advance a reference clock

Construct a Function-owned timer and two ordered waits directly in IR. Supply a
VirtualClock to execute the program without sleeping or reading the host clock.

```console
uv run python -m examples.developer.timing_ir
```

```text
timing_ir.json
Elapsed: 5.0 s
Waits: [(0.0, 2.0), (2.0, 5.0)]
```

```python
--8<-- "examples/developer/timing_ir.py"
```

[Download Python](../_generated/examples/developer/timing_ir.py) ·
[Download JSON](../_generated/examples/developer/timing_ir.json)

TimerResource appears in Program.resources with an owning Function ID. It needs
no device binding. StartTimer captures an origin; WaitUntil refers to that timer
and captures a Duration threshold. The completed WaitEvents expose actual
intervals on the virtual time axis. JSON restoration preserves this behavior.

A new entry run must start the timer again. Sharing an environment can share
elapsed time and history between sessions, but cannot share timer origins.
The [interpreter guide](../developer/reference/interpreter.md#elapsed-time-input)
describes failure behavior and clock ownership.
