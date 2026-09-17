# AutoSuite reference guide

This directory collects the evidence needed to build SciLoom's Semantic IR and
versioned AutoSuite backend. It is reference material, not an implementation of
the new compiler. Paths in code-formatted examples are relative to the repository root.

Material from the vendor and the instruments lives under `corpus/`, which is
shared inside the team and is not in git; see [the directory guide](../README.md)
for how to obtain it. Everything else is written by this project and is tracked.
A checkout may hold no corpus, or only the part a developer needed, so the
commands and tests that read it skip what is absent.

| Location under `autosuite/corpus/` | Contents and purpose |
|---|---|
| `app/` | Original applications; start with `config20260909_polymerization.app` |
| `asfp/` | Function packages, including minimal probes and FIXED/re-export counterparts |
| `archives/` | Unchanged original APP and ASFP ZIP archives |
| `manual/` | Original AutoSuite 2.47.1.1 PDF |
| `extracted/latest_app/` | Decompressed current app, its matching function XML packages, indexes and analysis |
| `type_templates/` | Representative type templates extracted from the applications |
| `golden_diffs/` | Normalized comparison diffs between fixture pairs |
| `catalogs/` | File catalogs, function evolution and byte-level provenance |
| `MANIFEST.csv` | Hashes of the corpus as it stands in this checkout |

| Location under `autosuite/` | Contents and purpose |
|---|---|
| `schema/` | Empirical type catalog, path profiles and variable-storage observations |
| `recipe/` | CSV recipe, analysis and validator |
| `tools/` | Read/inspect/validate XML and check a received corpus |
| `docs/` | AutoSuite semantics, serialization evidence and current workflow notes |

There are no symbolic-link aliases or ASPY source/view files in this collection.
XML candidates remain for comparison; use FIXED/re-export evidence and the real
application to establish accepted structure. Historical APP snapshots remain
because they capture distinct configurations and task/version combinations.

## Reading order

The 38 reference documents are in one directory, numbered 00–37. This guide is
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
- [17 · Array mapping and checked-index evidence](17_ARRAY_MAPPING.md)
- [18 · Capability gaps and runtime Zone parameters](18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md)
- [19 · Runtime text mapping](19_TEXT_MAPPING.md)
- [20 · Volume and duration mapping](20_QUANTITY_MAPPING.md)
- [21 · Numeric expressions and rounding](21_NUMERIC_MAPPING.md)
- [22 · Typed runtime logging](22_LOGGING_MAPPING.md)
- [23 · OK acknowledgement messages](23_NOTIFICATION_MAPPING.md)
- [24 · Runtime failure propagation gate](24_RUNTIME_FAILURE_GATE.md)
- [25 · Wall-time text mapping](25_WALL_TIME_MAPPING.md)
- [26 · Wait and timer mapping](26_TIMING_MAPPING.md)
- [27 · CSV reads and parsing gate](27_CSV_READ_MAPPING.md)
- [28 · CSV append and native export measurements](28_CSV_APPEND_MAPPING.md)
- [29 · Zone values and read-only APP layout](29_ZONE_VALUES_AND_LAYOUT.md)
- [30 · Zone indexing and sequential traversal](30_ZONE_TRAVERSAL_MAPPING.md)
- [31 · Stored well text properties](31_WELL_PROPERTY_MAPPING.md)
- [32 · Dynamic device locations](32_DYNAMIC_DEVICE_LOCATIONS.md)

### Current application and workflow

- [09 · Version selection and evolution](09_VERSION_SELECTION_AND_EVOLUTION.md)
- [10 · Current polymerization workflow](10_CURRENT_POLYMERIZATION_WORKFLOW.md)
- [11 · CSV recipe contract](11_CSV_REAGENT_RECIPE.md)
- [12 · CSV loading](12_LOAD_REAGENT_CURRENT_SPEC.md)
- [13 · Dynamic transfer](13_DYNAMIC_TRANSFER_CURRENT_SPEC.md)
- [14 · Static call graph](14_LATEST_APP_CALL_GRAPH.md)

### Runtime validation

- [15 · Executor simulation](15_EXECUTOR_SIMULATION.md)
- [33 · Deployment conditions and state lifetime](33_DEPLOYMENT_STATE_LIFETIME.md)
- [34 · Editor screenshot evidence](34_EDITOR_SCREENSHOT_EVIDENCE.md)
- [35 · Native measurement receipts](35_NATIVE_MEASUREMENT_RECEIPTS.md)
- [36 · Result-dialog probes and host acceptance](36_DIALOG_RESULT_PROBES.md)
- [37 · Fixed thermal measurements and native profile gate](37_FIXED_THERMAL_MEASUREMENTS.md)

## Commands

```bash
uv run python autosuite/tools/audit_corpus.py
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python autosuite/tools/inspect_structure.py autosuite/corpus/app/config20260909_polymerization.app
uv run python autosuite/tools/validate_structure.py autosuite/corpus/asfp/Test11_FIXED_RealInOut_DirectSet.asfp
```

The first three commands work without a corpus; the last two read one. After
intentionally adding or updating references, regenerate the manifest and archive
mapping with `uv run python autosuite/tools/audit_corpus.py --write-manifest`.
Default audit mode verifies without rewriting evidence or its manifest: a file
whose content changed is an error, while files you added or have not received are
reported rather than rejected.

`canonicalize_xml.py` is a lossy comparison helper that removes IDs and metadata;
its output must not be used for identity-preserving deduplication or serialization.
It writes a separate requested output path, which must be outside the evidence trees.

The compiler architecture and planned Python/xyflow/AI features are documented in
[the project design index](../../docs/INDEX.md).
