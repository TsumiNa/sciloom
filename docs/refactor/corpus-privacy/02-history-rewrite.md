# Remove the corpus from history

## Goal

Make the repository publishable by removing vendor and instrument material from
every commit, not just from the current tree.

Untracking alone is not enough: the corpus is reachable from all 66 commits, so
`git checkout <old-sha>` on a public clone would still produce it.

## Scope

This is a repository operation, not a pull request. It runs after
[the migration](01-move-corpus.md) has merged, at a moment when no other branch
or agent session is in flight.

Strip these historical paths, which are where the corpus lived before the
migration untracked it:

```
autosuite/app  autosuite/asfp  autosuite/archives  autosuite/extracted
autosuite/catalogs  autosuite/MANIFEST.csv
autosuite/schema/type_templates  autosuite/schema/golden_diffs
```

`autosuite/manual/` was never tracked and needs no entry.

## What it costs

Measured on `origin/main` at `63db7a6`:

| Item | Count |
| --- | --- |
| Commits on main | 66 |
| Commits that become empty and are pruned | 1 |
| Commits retained with messages and non-corpus content intact | 65 |
| `docs/refactor/` records lost | 0 |

The corpus entered in the initial commit and was never modified again apart from
`MANIFEST.csv`. The single pruned commit is the manifest refresh, which touched
that file alone. Every commit SHA changes, which has four consequences:

1. `docs/refactor/uv-workspace/00-overview.md` and `02-lockstep-version.md` cite
   a merge commit; replace those with pull request links.
2. Version identifiers of the form `0.1.0+<merge commit>` recorded in merged pull
   request descriptions point at commits that no longer exist. Those live on
   GitHub, not in the repository.
3. `website/tools/publication.py` checks that the published `dev` commit is an
   ancestor of the new `main` and will refuse to publish. Reconcile `gh-pages`
   once, deliberately, as its guidance intends.
4. Every clone must be re-cloned or hard reset.

## Acceptance

A fresh clone of the rewritten history contains no `.app`, `.asfp`, `.zip` or
manual under any commit; `docs/refactor/` is complete; the packed repository is
single-digit megabytes; CI passes on the rewritten `main`; documentation
publication succeeds after the one-time `gh-pages` reconciliation.

## Version

No bump: history only; the package version is unchanged.
