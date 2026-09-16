# Visit sample locations

Count the wells supplied by the caller and return the last visited well. No
equipment is started. A Zone containing wells in order `27, 0, 8` produces
`count=3` and a one-well Zone for `8`; those labels are not loop indices.

```python
--8<-- "examples/visit_locations.py"
```

```console
uv run python examples/visit_locations.py
```

```text
visit_locations.asfp
```

[Download Python](../_generated/examples/visit_locations.py) ·
[Download ASFP](../_generated/examples/visit_locations.asfp)

The count resets on each call because the first runtime statement assigns zero.
The current well persists. Calling again with an empty Zone returns zero visits
and the previous well; a fresh session starts with an empty value.

Compilation writes the function package. The loop runs when AutoSuite calls that
function. Its sequential Macro structure follows the supplied XML evidence;
Executor validation remains required on the intended deployment. See
[sample locations](../user-guide/reference/zones.md) for grouping and index limits.
