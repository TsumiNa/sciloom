# Share a reference event history

This developer example runs the agitation Function in two reference sessions.
The first saves a speed and starts its device; the second stops its own device.
An explicitly shared environment collects their events in execution order.

```python
--8<-- "examples/developer/reference_environment.py"
```

From a source checkout, run:

```console
uv run python -m examples.developer.reference_environment
```

```text
First run events: 2
Second run events: 1
Environment events: 3
First session enabled: True
Second session enabled: False
```

Each result is a snapshot of one run. Sharing the environment combines event
history; it does not merge the two sessions' device configurations or model two
connections to physical equipment. Creating a new environment starts a separate
history. See [environment ownership](../developer/reference/interpreter.md#explicit-environment).

[Download Python](../_generated/examples/developer/reference_environment.py)

The example reuses [the agitation Function](agitation.md); keep that source at
`examples/agitation.py` when running the downloaded file in a checkout.
