# AutoSuite reference material

This directory holds two different kinds of thing, and the difference decides
whether it enters git.

| Path | Origin | In git |
| --- | --- | --- |
| `corpus/` | The vendor and the instruments: `.app`, `.asfp`, extracted XML, type templates, golden diffs, catalogs, the manual | No |
| `docs/` | Analysis written by this project | Yes |
| `schema/` | Conclusions distilled from the corpus: the empirical type catalog, path profiles, variable-storage observations | Yes |
| `tools/`, `recipe/` | Code written by this project | Yes |

`.gitignore` denies `autosuite/*` and re-allows only the four tracked
directories, so material added later is excluded by default. `.githooks/pre-commit`
refuses a commit that stages anything else here, including after `git add -f`,
and `.claude/settings.json` denies agent writes under `corpus/`.

## Obtaining the corpus

The corpus is shared inside the team, not through this repository. Place the
files you receive under `autosuite/corpus/`, keeping the sub-directory names in
the table above. Nothing in this directory is required to build SciLoom, run the
website, or run the test suite; the tests that compare generated XML against the
corpus skip themselves when it is absent.

It is normal for two developers to hold different corpora. Each person adds the
files that their own work needs, so there is no canonical set and no version to
pin. As `sciloom-autosuite` grows, the fragments a test actually asserts on move
into the test as committed fixtures; when that migration finishes, only the
manual retains reference value.

## Migrating a checkout that predates this layout

Two things happened at once. The commit that introduced `corpus/` untracked the
vendor directories, so updating a checkout that still has them at the old paths
**deletes them from your working tree**. Then history was rewritten to remove
those paths from every commit, so your old history no longer connects to the new
one and an ordinary pull cannot fast-forward.

Move the directories first, then reset onto the new history. Every step is joined
with `&&`, so a move that fails stops the sequence before anything is fetched: a
partial move followed by an update is the very data loss this avoids. Omit a line
for anything your checkout does not have; `manual/` in particular has never been
in git, so it is there only if you already had it locally.

```bash
mkdir -p autosuite/corpus && \
mv autosuite/app autosuite/corpus/app && \
mv autosuite/asfp autosuite/corpus/asfp && \
mv autosuite/archives autosuite/corpus/archives && \
mv autosuite/extracted autosuite/corpus/extracted && \
mv autosuite/catalogs autosuite/corpus/catalogs && \
mv autosuite/manual autosuite/corpus/manual && \
mv autosuite/schema/type_templates autosuite/corpus/type_templates && \
mv autosuite/schema/golden_diffs autosuite/corpus/golden_diffs && \
mv autosuite/MANIFEST.csv autosuite/corpus/MANIFEST.csv && \
git fetch origin && \
git reset --hard origin/main && \
uv run python autosuite/tools/audit_corpus.py --write-manifest
```

`git reset --hard` leaves untracked files alone, and the corpus is untracked by
the time it runs, so it survives. Commit or stash your own work first: the reset
discards tracked changes.

If the chain stops early, nothing has been fetched yet: finish the remaining
moves by hand, confirm that `autosuite/` holds only `corpus/`, `docs/`,
`recipe/`, `schema/` and `tools/`, then run the last three commands.

The final step rewrites `MANIFEST.csv`, whose paths are now relative to `corpus/`.
If you have already updated and lost the files, restore them from your own copy
into `autosuite/corpus/` and run that same command.

Prefer `git fetch` plus `git reset --hard` over `git pull` here. A pull refuses
to run with unstaged changes when `pull.rebase` is set, and after the history
rewrite there is nothing to fast-forward.

## Rules

Raw vendor material is evidence. Do not rewrite a file here to make a test pass.
Write generated output somewhere else and compare the two. Agents must not write
into `corpus/` without a human asking for it; temporary files belong in a scratch
directory, never here.

`tools/audit_corpus.py` checks a corpus you have received: archive members match
their expanded files, extracted function XML matches the application it came
from, and recorded hashes still hold. A file whose content changed is an error;
files you added or have not received are reported, not rejected. It is a local
aid, not a required check, and it needs `corpus/` to be present.

`MANIFEST.csv` lives with the corpus rather than in git, and its paths are
relative to `corpus/`. After moving an existing corpus into this layout, or after
adding files, run `python autosuite/tools/audit_corpus.py --write-manifest` once
to record the current state.
