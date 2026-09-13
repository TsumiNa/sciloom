# Site foundation

## Goal

Provide a reproducible English Zensical build and PR preview artifact.

## Scope

Follow the [authoritative contract](00-overview.md). Add locked docs dependencies,
mkdocs.yml, docs/site, the site build/preview tool and colocated tests. Prepare
version metadata and allowlisted example assets without modifying their sources.
Add a small real API pilot for Function, field aliases and Agitator. Enable search,
Mermaid, code copying and strict internal link checks. Add read-only docs CI on
Python 3.14. Document the exact local commands and update repository entry points.

## Non-goals

No remote deployment, complete manuals/catalogue or runtime/API changes. Later
sections may be omitted from navigation until their real content exists.

## Acceptance

Run the contract's strict build and docs/tools tests. Verify pilot API headings,
types, metadata, build failure on invalid links and publication exclusions. Run
existing pytest, mypy, smoke, recipe, all current examples and proposed-example
syntax checks. Check git diff --check and that builds do not modify tracked files.
Review and squash merge before stage 2 begins.
