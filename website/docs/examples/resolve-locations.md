# Resolve sample locations

Supply two location names when calling the generated function. It returns their
combined Zone and the number of distinct wells. If both names describe the same
wells, the count does not double. An unknown name contributes no wells.

```python
--8<-- "examples/resolve_locations.py"
```

```console
uv run python examples/resolve_locations.py
```

```text
resolve_locations.asfp
```

[Download Python](../_generated/examples/resolve_locations.py) ·
[Download ASFP](../_generated/examples/resolve_locations.asfp)

The program resolves names at execution time in the deployed AutoSuite
configuration. Compiling it does not look up locations or move equipment.
The [Zone reference](../user-guide/reference/zones.md) describes value semantics
and the current target restrictions. Enumeration and native expression behavior
still require Executor validation on the intended deployment.
