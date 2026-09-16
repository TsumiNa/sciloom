# Label selected wells

Store the caller's sample label on every well in a Zone, then read the labels
back in selection order. Two selected wells and the label `batch A` leave both
with `sample_ID="batch A"`; `last_label` returns `batch A`. An empty Zone changes
no properties and returns an empty string.

```python
--8<-- "examples/label_wells.py"
```

```console
uv run python examples/label_wells.py
```

```text
label_wells.asfp
```

[Download Python](../_generated/examples/label_wells.py) ·
[Download ASFP](../_generated/examples/label_wells.asfp)

Change `sample_ID` in `__init__` to use another text user-property name. The rack
and label are supplied when AutoSuite calls the compiled function. They are not
arguments to `.compile()`.

The read has a default and runs inside a single-well loop. See
[stored labels](../user-guide/reference/well-properties.md) for strict-read and
selection limits. Generated XML follows the supplied task evidence; it still
needs Executor validation on the intended deployment.
