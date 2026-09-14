# Remove the corpus from history

Status: the rewrite ran on 2026-09-14. `main` is rewritten and force-pushed; two
remote cleanup steps remain, listed under [What remains](#what-remains).

## Goal

Make the repository publishable by removing vendor and instrument material from
every commit, not just from the current tree.

Untracking alone was not enough: the corpus was reachable from every commit, so
`git checkout <old-sha>` on a public clone would still have produced it.

## Scope

This is a repository operation, not a pull request. It ran after
[the migration](01-move-corpus.md) merged, at a moment with no other branch or
agent session in flight.

The stripped historical paths, where the corpus lived before the migration
untracked it:

```
autosuite/app  autosuite/asfp  autosuite/archives  autosuite/extracted
autosuite/catalogs  autosuite/MANIFEST.csv
autosuite/schema/type_templates  autosuite/schema/golden_diffs
```

`autosuite/manual/` was never tracked and needed no entry.

## What it cost

`git filter-repo 2.47.0 --invert-paths`, run on a single-branch clone of `main`:

| Item | Before | After |
| --- | --- | --- |
| Commits on main | 68 | 67 |
| `docs/refactor/` files | 54 | 54 |
| Commits touching `docs/refactor/` | 43 | 43 |
| Packed `.git` in that clone | 15 MB | 1.9 MB |
| Tree hash at `main` | `e55477a` | `e55477a` |

The corpus entered in the initial commit and was never modified again apart from
`MANIFEST.csv`. Exactly one commit became empty and was pruned:
`chore: refresh the corpus manifest after the tool reformat (#57)`, which touched
that file alone. Every other commit kept its message, author, date and all of its
non-corpus content; the corpus paths were removed from each of their trees, which
is the point. The tree at `main` is byte-identical because the migration had
already removed those paths from the current tree.

Five `.asfp` files remain in history and are correct: `examples/*.asfp` and
`examples/developer/portable_agitation.autosuite.asfp` are SciLoom's own compiler
output, written by the example scripts and already published as example
downloads.

Every commit SHA changed. `main` went from `54bd4de` to `b231075`.

## What remains

1. **Delete the 34 stale remote branches listed below.** Every one belongs to a
   merged pull request, and each still holds the pre-rewrite history, so the
   corpus stays reachable on the remote and in any clone that fetches them.

   Delete these names explicitly. Do not derive the list with a filter such as
   "every branch except `main` and `gh-pages`": that would also delete any branch
   opened after this list was taken.

   ```bash
   git push origin --delete \
     codex/sciloom-brand-integration docs/api-reference \
     docs/device-abstraction-contract docs/documentation-site-plan \
     docs/package-layout-contract docs/reader-handbooks \
     docs/reference-api-compat-rules docs/sciloom-repository-url \
     docs/site-foundation docs/typeid-suffix-assumption \
     docs/versioned-publication feat/agitation-domain-semantics \
     feat/asfp-compiler feat/autosuite-agitation-backend feat/autosuite-arrays \
     feat/declarative-device-bindings feat/device-configuration-lifecycle \
     feat/device-specialization feat/independent-device-contribution \
     feat/ir-reference-execution feat/list-ir-semantics \
     feat/native-runtime-declarations feat/python-frontend \
     feat/python-list-lowering feat/semantic-ir-json fix/mypy-test-annotations \
     refactor/autosuite-codegen refactor/compiler-module-boundaries \
     refactor/compiler-responsibilities refactor/core-layout \
     refactor/device-module refactor/dsl-contrib-layout \
     refactor/explicit-compilation-targets refactor/standalone-website
   git remote prune origin && git reflog expire --expire=now --all && git gc --prune=now
   ```

   Confirm each name still belongs to a merged pull request before running this,
   in case one was reused since.

2. **Reconcile `gh-pages`.** `website/tools/publication.py` refuses with
   `Refusing stale or divergent dev history`, exactly as designed, because the
   published `dev/build-info.json` names `54bd4de`, which no longer exists. There
   are no release snapshots yet, only the rolling `dev`, so deleting the branch
   loses nothing immutable and lets the publisher rebuild it from the rewritten
   `main`.

   ```bash
   git push origin --delete gh-pages
   gh workflow run "Publish documentation" --ref main
   ```

   A local backup exists at `~/sciloom-pre-rewrite.bundle`; restore with
   `git fetch ~/sciloom-pre-rewrite.bundle 'refs/*:refs/*'` if needed.

## Outcome so far

CI passes on the rewritten `main` (`b231075`, push event). The working checkout
was reset onto it with the corpus untouched, since the corpus is no longer
tracked. Documentation publication stays blocked until step 2 runs.

## Version

No bump: history only; the package version is unchanged.
