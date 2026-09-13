# Site foundation

## Goal

Provide a reproducible English Zensical build and PR preview artifact.

## Scope

Follow the [authoritative contract](00-overview.md). Add locked docs dependencies,
website/mkdocs.yml, website/docs, the site build/preview tool and colocated tests. Prepare
version metadata and allowlisted example assets without modifying their sources.
Add a small real API pilot for Function, field aliases and Agitator. Enable search,
Mermaid, code copying and strict internal link checks. Add read-only docs CI on
Python 3.14. Document the exact local commands and update repository entry points.

## Non-goals

No remote deployment, complete manuals/catalogue or runtime/API changes. Later
sections may be omitted from navigation until their real content exists.

## Acceptance

Run the contract's strict build and website/tools tests. Verify pilot API headings,
types, metadata, build failure on invalid links and publication exclusions. Run
existing pytest, mypy, smoke, recipe, all current examples and proposed-example
syntax checks. Check git diff --check and that builds do not modify tracked files.
Review and squash merge before stage 2 begins.

## Implementation evidence

The real Zensical build renders Function, Annotated aliases and Agitator property
types through the public root exports. Seven tooling regressions cover source
metadata, exact allowlisted copies, symlink escape rejection, API HTML/revision
stamping, metadata/public-directory symlink rejection and strict broken-link failure.
Local acceptance: 328 tests, mypy on 63
source files, smoke, recipe, eight examples, proposed syntax and diff checks pass.
Remote review/CI and merge remain the gate for the next stage.

Browser verification confirms rendered Mermaid, search-to-Agitator navigation,
property/signature display and working navigation at a 390px viewport. Copilot's
metadata symlink finding is covered by the new no-overwrite regression. Search
was already enabled natively by Zensical; it is now also explicit in configuration.
