# Versioned publication

## Goal

Publish checked main/tag documentation automatically on GitHub Pages.

## Scope

Follow the [authoritative contract](00-overview.md). Lock the Zensical mike fork,
add version selection/stamping and serialized publication with missed-tag
reconciliation. Preserve release snapshots and highest-version stable redirects.
Gate publication on exact-commit checks. Configure Pages on the current repository
or the approved public generated-site fallback. Isolate publication credentials
from PR builds. Deploy the first dev version and document maintenance/recovery.

## Non-goals

No package release, tag creation, custom domain or source visibility change.
No per-commit permanent websites or automatic historical-version rewriting.

## Acceptance

Test two release snapshots and dev updates, stable ordering, missing-tag recovery,
tag/package mismatch, moved tags, stale dev updates and immutable history. Verify
version/base-prefix links and current-version search. Run all existing checks,
strict build and publication exclusion audit. Confirm the deployed homepage,
representative API search/downloads and full source SHA in build-info.json.
Inspect all review surfaces, fix feedback and squash merge the completed stage.

## Implementation and deployment choice

The Pages API successfully enabled a public Actions-backed site on the existing
private `TsumiNa/sciloom` repository. The selected URL is
`https://tsumina.github.io/sciloom/`; the fallback repository is unnecessary.
No source visibility change, release tag or PyPI publication was performed.

The docs group pins squidfunk/mike at
`2d4ad799442f4592db8ad53b179bfb33db8c69ac`. Each source snapshot builds in its own
worktree/environment with its own lock and Python 3.14. The current publisher
packages completed trees with mike; a separate write-enabled job stores the
generated-only branch and deploys Pages. Each run reconciles all eligible tags
and checked current main, using exact-commit CI job verification.

Regression coverage exercises two releases, repeated dev updates, highest stable,
root/nested redirects, preserved release tree hashes, moved tags, version mismatch,
missing tag reconciliation, rejected CI identities/jobs, publication exclusions,
and a real locked-checkout dev build followed by divergent-main rejection.
The first live dev deployment is expected after this stage's reviewed merge and
successful main CI; inspect its build-info.json and representative browser pages.

Local verification passed 354 tests, mypy, strict builds, smoke/recipe validation,
all eight examples and the whitespace check. A real Zensical/mike fixture confirmed
root → stable → 0.2.0 redirects, selection of dev and retained 0.1.0, and search
navigation staying under the selected version's API path.
