# Validation status

Reference reorganization validation, 2026-09-11:

- Original APP archive: all 68 entries match 68 distinct expanded gzip/XML files.
- Original ASFP archive: all 59 entries match 58 distinct expanded XML files; the duplicate entry maps to its retained original.
- Current application: decompressed XML matches byte-for-byte; all 52 function packages match the application's XML nodes.
- Schema references: 67 type templates parse and have valid source paths and matching type IDs.
- Reference catalogs, relocation hashes and the current manifest: verified.
- Package smoke and supplied CSV validation: pass.
- Six proposed Python frontend examples: syntax-check pass; they remain design examples, not an implemented runtime API.
- Structural inspector: traverses untyped XML containers to display nested typed tasks.

The historical compiler and ASPY inputs/views are no longer part of the repository
or its test suite. XML candidates and AutoSuite-fixed counterparts remain reference evidence.

## Commands

```bash
uv run pytest src/sciloom/ir
uv run python autosuite/tools/audit_corpus.py
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
```

## Semantic IR stage

Colocated tests cover typed/JSON round-trip, semantic occurrence IDs, source
diagnostics, variable ownership, numeric and boolean expressions, nested control
flow, complete call bindings and recursion rejection. CI runs those tests and the
existing smoke/recipe checks on Python 3.12, 3.13 and 3.14. The ignored local manual
is not required by these CI checks; a full corpus audit still requires the local
reference materials listed in the manifest.

No Python frontend or ASFP serializer is implemented in this stage, so these tests
must not be described as Python-to-ASFP or Executor acceptance.

`AutoSuiteExecutor.exe` is not available here. Static validation does not establish
Executor acceptance; generated applications must still pass the real integration gate:

```text
AutoSuiteExecutor.exe generated.app /r /sim 100 /s /c
```
