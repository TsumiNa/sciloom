# Corpus and provenance

The reference collection was supplied on 2026-09-10 and organized under
`autosuite/` on 2026-09-11. The refactor relies on XML and documented semantics;
no colleague-specific ASPY toolchain is required.

## Original evidence

- `autosuite/archives/app_type_files.zip`: the unchanged original archive, 68 APP entries.
- `autosuite/archives/asfp_type_files.zip`: the unchanged original archive, 59 ASFP entries.
- `autosuite/app/`: all 68 distinct APP files, each gzip-compressed XML.
- `autosuite/asfp/`: 58 byte-distinct ASFP files. The archive entry
  `GetAspirateChunkVol - Copy.asfp` is identical to `GetAspirateChunkVol.asfp`;
  only the latter is expanded on disk.
- `autosuite/manual/1001.9796.T AutoSuite Software Manual.pdf`: the supplied manual.
- `autosuite/recipe/input_0908.csv`: the supplied recipe, with its validator and analysis.

APP/ASFP files include production exports, version snapshots, minimal schema
probes, generated candidates and AutoSuite FIXED/re-exports. A location in the
reference collection does not make every candidate an accepted serialization.
Use the [fixture matrix](07_GOLDEN_FIXTURE_MATRIX.md) to distinguish them.

## Current application and derived references

`autosuite/app/config20260909_polymerization.app` is the primary current application.
`autosuite/extracted/latest_app/application.xml` matches its decompressed bytes.
The 52 single-function packages under `autosuite/extracted/latest_app/functions/`
match its function XML trees, including IDs, values, metadata and child order.
Function indexes, globals, zones and a static call graph remain available there.

The per-file mapping is recorded in
[`function_sources.csv`](../extracted/latest_app/function_sources.csv): all 52
packages (50 ordinary functions and two event functions) map to
`config20260909_polymerization.app`. Each row records the package path/hash,
reference APP path/hash, one-based XPath position, function ID, name, type,
event type and verified XML-tree match. Paths in that CSV are relative to `autosuite/`.
The comparison ignores XML indentation and attribute order, while preserving
IDs, values, metadata and child order.

These packages are retained for convenient browsing and future tests. They add
no independent source evidence beyond the APP and can be reconstructed from its
function nodes; reproducing the original file formatting is a separate concern.

These equality checks establish correspondence, not the historical direction
of generation or the identity of the original authoring tool. The original
function extraction/rendering implementation is not supplied. Summarized views
were removed because the refactor can work directly from XML.

## Integrity and provenance records

- `autosuite/MANIFEST.csv`: current relative paths, sizes and SHA-256 hashes for
  reference files, derived documentation and tools; excludes itself and caches.
- `autosuite/catalogs/relocation.csv`: original paths and unchanged content hashes
  for relocated evidence. Old paths here are historical identifiers, not live links.
- `autosuite/catalogs/archive_members.csv`: each original APP/ASFP archive member
  mapped to its current expanded file, including the duplicate archive alias.
- `autosuite/catalogs/app_catalog.*` and `asfp_catalog.*`: current expanded-file catalogs.

The schema profiles/template occurrence counts describe the original collection
of 68 APP and 59 ASFP entries, before dropping the duplicate expanded ASFP.
They are historical measurements, not a vendor XSD or a count of current unique files.

## Removed material

The historical compiler, seven ASPY inputs, ASPY ZIP, 53 summarized text views,
ASPY catalogs, duplicate canonical/reference directory aliases, obsolete packaging
manifest, legacy design note and superseded cleanup/repack reports were removed.
The minimal XML candidates and their FIXED/re-export counterparts remain because
their differences are useful serialization evidence.

Run `uv run python autosuite/tools/audit_corpus.py` to check the retained archives,
expanded files, XML correspondence, catalogs, templates, relocation hashes and manifest.
Static checks do not replace AutoSuite Executor acceptance.
