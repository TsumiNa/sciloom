# Generated API reference

## Goal

Make the public author and contributor interfaces discoverable from source.

## Scope

Follow the [authoritative contract](00-overview.md). Complete the explicit API
catalogue and Google-style docstrings. Generate signatures and annotations from
source with runtime inspection disabled. Cover root exports, units/comptime,
AutoSuite public classes, device declarations, IR, compiler, bindings,
specialization, interpreter and diagnostics. Prefer documented public import paths.
Keep tests/private implementation out of the index. Add focused catalogue checks
for missing members/docstrings and search/anchor coverage.

## Non-goals

No changes to execution, Python signatures or semantic JSON. No runtime imports to
work around documentation extraction and no parallel handwritten signature list.

## Acceptance

Strict build; verify Input/Output/Var, property types, decorated methods, dataclass
fields and Target signatures. Search representative symbols and follow results to
their API descriptions. Run catalogue tests plus existing checks; check that
docstring-only edits preserve semantic output. Review and squash merge before 4.

## Implementation evidence

The explicit catalogue covers all root, IR, device, interpreter and AutoSuite
exports, plus the selected compiler, binding, declaration and diagnostic APIs.
Static Griffe checks require a source docstring for every indexed object; real
HTML checks verify all catalogue anchors, properties and protocol methods.
Private/dunder helpers are filtered from generated members.

All 344 tests, mypy, smoke/recipe validation and eight runnable examples pass.
Example companions remain byte-identical. Browser search for ConfigureProperty
opens its exact generated object anchor; Target signatures and dataclass fields
render with source-derived types. No runtime semantics or signatures change.
