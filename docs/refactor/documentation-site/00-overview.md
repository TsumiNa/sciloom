# English documentation and versioned publication

Status: plan merged in PR #28 (`4a62f2e`); foundation merged in PR #29 (`3f91340`).
Stage 2 is implemented in its review branch.
This document is
the authoritative contract for this sequence. It changes documentation tooling,
not SciLoom execution semantics, Python APIs, package visibility or PyPI releases.

## Decision

Use Zensical with mkdocstrings-python, English Markdown under `docs/site/`, and
the Zensical-maintained mike fork pinned to a commit. Sphinx/MyST was considered;
the selected Zensical stack provides the desired reading experience while keeping
Python signatures generated from source. The mike integration is transitional:
upgrades require verification rather than tracking its default branch.

- [Zensical plugin compatibility](https://zensical.org/docs/compatibility/mkdocs/plugins/)
- [Zensical versioning](https://zensical.org/docs/compatibility/mkdocs/mike/)
- [Static Python API extraction](https://mkdocstrings.github.io/python/usage/configuration/general/#allow_inspection)

## Readers and publication boundary

| Section | Content |
|---|---|
| Introduction | Purpose, current capabilities, installation and quick start |
| User guide | Function, fields/types/units/lists, composition, devices, conditions, compilation |
| Developer guide | DSL, IR v4, specialization, compiler, interpreter, contributions and tests |
| Examples | Four author examples and four developer examples, with actual source and outputs |
| API reference | Curated author and contributor interfaces, generated from source and searchable |

Publish only this source tree, selected API descriptions and explicitly listed
example assets. Do not copy the raw `autosuite/` corpus, internal refactor plans,
historical proposals or the private source Git history into the site. Retain
internal design records in place. Replace superseded current-guide prose with
links to the authoritative public handbook, updating callers in the same stage.
Mark GUI/server, Application/global and other future capabilities as unimplemented.
Do not claim Executor or hardware validation from compilation/reference execution.

## Build and authoring contract

The following commands become runnable in stage 1:

```bash
uv sync --locked --group docs
uv run --group docs python docs/tools/site.py serve
uv run --group docs python docs/tools/site.py build --strict
uv run --group docs pytest docs/tools
```

`mkdocs.yml` configures Zensical. The small site tool prepares allowlisted assets
and source-version metadata, then invokes Zensical. Preview listens locally;
strict builds fail on documentation warnings. Generated inputs/output and caches
are ignored and may be recreated; source/example companions are not rewritten.
Dependencies are in the uv `docs` group, separate from runtime and dev dependencies.

API pages use explicit mkdocstrings directives, for example (stage 1 pilot;
complete catalogue in stage 3):

```markdown
::: sciloom.Function
    options:
      members: [compile, to_ir]
```

Use static source analysis with inspection disabled. Preserve public import paths,
decorator signatures, Annotated field roles, property types and dataclass fields.
Exclude private helpers and tests. The author catalogue covers root exports,
units, comptime and public AutoSuite classes. The contributor catalogue covers
device declarations, IR, compiler/bindings/specialization, interpreter and errors.
Use Google-style English docstrings: summary, Args, Returns, Raises and Attributes
where applicable. Explain semantics without duplicating type signatures manually.
Source/edit links remain disabled while the source repository is private.

Example pages include actual source, short module-docstring results and downloads
of committed companion files. Environment-dependent paths may be normalized only
in explicitly labelled display copies; raw companions remain unchanged. API and
example preparation must not execute device operations or arbitrary runtime code.

## Version and deployment contract (stage 4)

| Path | Source | Policy |
|---|---|---|
| dev/ | main | Rolling checked development snapshot |
| 0.1.0/ etc. | v0.1.0 etc. | Retained release snapshot |
| stable/ | Highest published stable semantic version | Redirect alias |
| / | stable, otherwise dev | Default redirect |

Only `vMAJOR.MINOR.PATCH` tags are automatic release candidates in this iteration.
Tag version must equal the package version in that commit. No tag or package
release is created by documentation publication; initially only dev exists.
Each version uses code, Markdown, examples and uv.lock from the same commit.
Do not rebuild an old tag with main's API or dependencies. Store this metadata in
each version's `build-info.json` and show version/short SHA on every page:

```json
{"version":"0.1.0","ref":"v0.1.0","commit":"<full source SHA>","package_version":"0.1.0"}
```

The development snapshot uses `version="dev"` and `ref="main"`; package_version
is read from that source commit's pyproject.toml, never replaced with "dev":

```json
{"version":"dev","ref":"main","commit":"<full main source SHA>","package_version":"0.1.0"}
```

These placeholders document the shape, not real deployed builds. PR artifacts
use version="preview", ref="refs/pull/<number>/head" and the PR head SHA. Local
builds use version="local" ("local-dirty" for uncommitted tracked changes), the
current branch name ("HEAD" when detached), and the full HEAD SHA. Only dev and
numeric release versions are publishable. Published builds must be clean.
An existing release tied to another SHA is an error, never an overwrite. Stable
is selected numerically, not by event time. Search is local to the selected version.
Serialize publication, reconcile missing eligible tags, and prevent stale main
builds from replacing newer dev. Keep immutable release content; do not retain a
separate site for every main commit. Version aliases use redirects, not symlinks.

PRs build/check and upload preview artifacts without deployment credentials.
Main/tag publication requires successful checks for that exact source commit.
Pin Actions by SHA; docs use Python 3.14 while existing CI retains 3.12–3.14.
Default to Pages on TsumiNa/sci-loom if its private-repository entitlement permits.
Otherwise publish generated assets to public TsumiNa/sciloom-docs using a dedicated
deployment credential. Source remains private. Choose the destination once during
setup; later opening the source repository does not move the site. Use the default
GitHub Pages domain. Build permissions are read-only; writes belong to publication.

## Sequential stages

This plan PR must pass review and merge before stage 1. Each subsequent PR follows
review → corrections → checks on latest head → confirmed squash merge → next stage.

| Stage | Plan | Status |
|---|---|---|
| 1 | [Site foundation](01-site-foundation.md) | Merged: PR #29, 3f91340 |
| 2 | [Reader handbooks](02-reader-handbooks.md) | Implemented; awaiting review/merge |
| 3 | [Generated API reference](03-api-reference.md) | Pending |
| 4 | [Versioned publication](04-versioned-publication.md) | Pending |

## Acceptance

Validate public-path API rendering, field aliases/properties/decorators/protocols,
search-to-symbol links, internal links/anchors, Mermaid, responsive navigation,
downloads, version switches and base URL prefixes. Simulate two release versions
and a dev update, including tag/SHA conflicts and preserved history. Assert that
unselected repository content never enters the publication tree. Strict builds
must leave tracked files unchanged. Run existing pytest, mypy, smoke, recipe and
example checks for implementation stages. Hardware simulation remains separate.

No GUI/server implementation, translation framework, PyPI publication, experimental
API changes, automatic source-repository visibility change or custom domain.
