# Keep the shaker running through a wait

Start a shaker, record a timer origin, and stop it after an elapsed-time wait.
The first wait uses two seconds; the second waits only for the remaining time
to the five-second threshold. Calling `stop()` is a separate step.

```console
uv run python examples/timed_agitation.py
```

```text
timed_agitation.asfp
```

The generated file appears beside the source. Compilation does not wait or
control hardware. The speed and durations demonstrate programming and are not
recommended process settings.

```python
--8<-- "examples/timed_agitation.py"
```

[Download Python](../_generated/examples/timed_agitation.py) ·
[Download ASFP](../_generated/examples/timed_agitation.asfp)

Change the two Duration values to alter the waits. `wait_until(5 * s)` means
five seconds from the latest timer start, not five more seconds. Steps between
start and wait count toward elapsed time. If that time has already passed, the
program continues immediately. A wait never stops the shaker by itself.

The native Wait task disables its cancel-wait button. Timer reset, scope,
elapsed behavior and this setting still need AutoSuite Executor validation.
See [timing rules and target limits](../user-guide/reference/runtime-language.md#wait-and-timer).
