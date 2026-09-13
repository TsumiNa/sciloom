# Standalone documentation website

Status: implemented in [PR #37](https://github.com/TsumiNa/sciloom/pull/37).

The public documentation, theme and build tools were mixed with internal design
records. Group all website-specific sources under `website/`, while keeping
internal architecture and refactor records under `docs/`. The public Developer
Guide remains part of the website. A content-only move was rejected because it
would leave the website's tooling and theme scattered across the repository.

## Directory and command contract

| Location | Responsibility |
| --- | --- |
| `website/docs/` | Public handbooks, API pages, examples and brand assets |
| `website/theme/` | Theme overrides |
| `website/tools/` | Build/publication tools and colocated tests |
| `website/mkdocs.yml` | Zensical configuration |
| `website/.build/site/` | Ignored single-version output |
| `website/.build/publication/` | Ignored version aggregation and deployment artifacts |
| `docs/` | Internal design and development records |

After the migration PR, run these commands from the repository root:

```bash
uv run --group docs python website/tools/site.py serve
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
uv run --group docs python website/tools/publication.py --repository TsumiNa/sciloom
```

Preview serves at `http://127.0.0.1:8000/`; build emits HTML under
`website/.build/site/`. Publication retains its clean-checkout, exact-commit CI,
locked dependencies and fetched-ref requirements. It prepares a generated-only
history bundle and site tree; Actions performs the actual deployment.

Zensical runs with `website/` as its working directory. The config uses `docs`,
`theme`, `.build/site`, Python sources in `../src` and snippet base path `..`.
Dependencies remain in the root pyproject and lock file. The website must build
without the internal `docs/` tree. No old-path wrapper or alternate config remains.

## Sequence and boundaries

One PR implements [the migration](01-move-website.md), including all invalidated
references, then follows review, fixes, latest green checks and squash merge.
Verify the automatic main deployment afterward. This plan and implementation
ship together as requested; there is no separate plan PR.

Python APIs, runtime semantics, public URLs, navigation and version metadata do
not change. Preserve generated `gh-pages` history and immutable published releases.
There are no formal tags at migration time, so no old-layout build adapter is
needed. Raw AutoSuite evidence and example companion files remain unchanged.

## Version decision

No package version bump: this migration changes documentation organization and
tool paths, without changing the public Python API or runtime behavior.
