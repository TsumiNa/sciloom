# AutoSuite reference guide

This directory collects the evidence needed to build SciLoom's Semantic IR and
versioned AutoSuite backend. It is reference material, not an implementation of
the new compiler. Paths in code-formatted examples are relative to the repository root.

| Location under `autosuite/` | Contents and purpose |
|---|---|
| `app/` | 68 distinct original applications; start with `config20260909_polymerization.app` |
| `asfp/` | 58 distinct function packages, including minimal probes and FIXED/re-export counterparts |
| `archives/` | Unchanged original APP and ASFP ZIP archives |
| `manual/` | Original AutoSuite 2.47.1.1 PDF |
| `extracted/latest_app/` | Decompressed current app, 52 matching function XML packages, indexes and analysis |
| `schema/` | Empirical profiles, 67 representative type templates and normalized comparison diffs |
| `recipe/` | Original CSV recipe, analysis and validator |
| `catalogs/` | File catalogs, function evolution and byte-level provenance |
| `tools/` | Read/inspect/validate XML and verify corpus integrity |
| `docs/` | AutoSuite semantics, serialization evidence and current workflow notes |
| `MANIFEST.csv` | Current hashes for the reference collection |

There are no symbolic-link aliases or ASPY source/view files in this collection.
XML candidates remain for comparison; use FIXED/re-export evidence and the real
application to establish accepted structure. Historical APP snapshots remain
because they capture distinct configurations and task/version combinations.

## Reading order

The 17 reference documents are in one directory, numbered 00–16. This guide is
00; read the following documents in order or jump to the relevant group.

### Sources and runtime semantics

- [01 · Corpus and provenance](01_CORPUS_AND_PROVENANCE.md)
- [02 · Manual-derived semantic reference](02_AUTOSUITE_CORE_REFERENCE.md)
- [03 · Known semantic traps](03_KNOWN_TRAPS.md)

### XML and schema evidence

- [04 · Schema extraction method](04_SCHEMA_EXTRACTION_METHOD.md)
- [05 · Confirmed XML structure](05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md)
- [06 · Semantic construct to XML mapping](06_SEMANTIC_TO_XML_MAPPING_REFERENCE.md)
- [07 · Golden fixture matrix](07_GOLDEN_FIXTURE_MATRIX.md)
- [08 · Type templates](08_TYPE_TEMPLATES.md)
- [16 · Agitation mapping evidence](16_AGITATION_MAPPING.md)

### Current application and workflow

- [09 · Version selection and evolution](09_VERSION_SELECTION_AND_EVOLUTION.md)
- [10 · Current polymerization workflow](10_CURRENT_POLYMERIZATION_WORKFLOW.md)
- [11 · CSV recipe contract](11_CSV_REAGENT_RECIPE.md)
- [12 · CSV loading](12_LOAD_REAGENT_CURRENT_SPEC.md)
- [13 · Dynamic transfer](13_DYNAMIC_TRANSFER_CURRENT_SPEC.md)
- [14 · Static call graph](14_LATEST_APP_CALL_GRAPH.md)

### Runtime validation

- [15 · Executor simulation](15_EXECUTOR_SIMULATION.md)

## Commands

```bash
uv run python autosuite/tools/audit_corpus.py
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python autosuite/tools/inspect_structure.py autosuite/app/config20260909_polymerization.app
uv run python autosuite/tools/validate_structure.py autosuite/asfp/Test11_FIXED_RealInOut_DirectSet.asfp
```

After an intentional reviewed reference update, regenerate the manifest and
archive mapping with `uv run python autosuite/tools/audit_corpus.py --write-manifest`.
Default audit mode verifies without rewriting evidence or its manifest.

`canonicalize_xml.py` is a lossy comparison helper that removes IDs and metadata;
its output must not be used for identity-preserving deduplication or serialization.
It writes a separate requested output path, which must be outside the evidence trees.

The compiler architecture and planned Python/xyflow/AI features are documented in
[the project design index](../../docs/INDEX.md).
