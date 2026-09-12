# Distinguish Python lowering from AutoSuite code generation

Historical implementation plan. Package paths are superseded by the
[package-layout contract](../package-layout/00-overview.md). The distinction
between Python lowering and target code generation remains in force.

Two modules named `lowering.py` obscure the distinction between Python source
analysis and target-specific generation. The accepted change keeps Python lowering
in the frontend and renames the AutoSuite module to `codegen.py`.

Keeping both names is conventional compiler terminology, but less clear for this
project's readers. Moving target generation into the generic compiler would mix
vendor serialization with the shared pipeline. The chosen rename preserves the
existing boundaries and updates references directly, without compatibility aliases.

## Non-goals

No changes to IR, target interfaces, serialization behavior, generated artifacts,
or the Python frontend. The backend helper `lower_asfp` still constructs the thin
serialization IR; XML encoding remains in `xml.py`.

## PR sequence

1. [Rename the AutoSuite code generation module](01-rename-codegen.md): move the
   implementation and colocated tests, update imports and documentation, and
   clarify the shared compiler/target relationship in one independently verifiable PR.
