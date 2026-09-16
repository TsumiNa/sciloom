# Execute location queries

This example supplies two overlapping selections in a fixed directory. Their
combined order is `27, 0, 8`; those labels identify wells rather than array indices.
The directory stays outside the JSON program, so another session can supply a
different directory without rewriting the algorithm.

```console
uv run python -m examples.developer.zone_ir
```

```text
zone_ir.json
Selected wells: ('well:27', 'well:0', 'well:8')
Count: 3
```

```python
--8<-- "examples/developer/zone_ir.py"
```

[Download Python](../_generated/examples/developer/zone_ir.py) ·
[Download JSON](../_generated/examples/developer/zone_ir.json)

To inspect a locally supplied APP, use
`AutoSuiteLayout.from_app(path).directory` from `sciloom_autosuite` as the
environment's `locations`. The parser reads the gzip file without changing it,
checks real well addresses and preserves the serialized enumeration order.
It rejects ambiguous addresses, unresolved references and unsupported layout
profiles. It does not import experimental tasks or validate a dynamic hardware
binding. No vendor APP is included in the public downloads.
