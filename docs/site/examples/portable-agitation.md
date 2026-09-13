# Rebind one program to two targets

PortableAgitation declares the generic Agitator interface and preserves a DemoAgitator-specific gain branch in authored IR. The example restores that JSON and compiles it for AutoSuite and Demo targets.

## Run and inspect

```bash
uv run python -m examples.developer.portable_agitation
```

The same source has configured properties ['speed'] for AutoSuite and ['gain', 'speed'] for Demo. Both selected programs can be reference-executed because this example does not request native calibration. The base JSON preserves the conditional; .autosuite.asfp and .demo.json are the target artifacts. All branches are type-checked before selection, and compile-time binding remains explicit. JSON diagnostic paths are environment-dependent.

The module docstring below records expected terminal output. Compilation and
reference execution do not operate hardware or replace AutoSuite Executor checks.

## Source and generated files

[Download Python source](../_generated/examples/developer/portable_agitation.py)

- [portable_agitation.json](../_generated/examples/developer/portable_agitation.json)

- [portable_agitation.autosuite.asfp](../_generated/examples/developer/portable_agitation.autosuite.asfp)

- [portable_agitation.demo.json](../_generated/examples/developer/portable_agitation.demo.json)

```python
--8<-- "examples/developer/portable_agitation.py"
```

