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
