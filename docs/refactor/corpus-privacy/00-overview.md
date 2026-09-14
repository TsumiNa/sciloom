# Keep the AutoSuite corpus out of git

Status: implemented by [the migration](01-move-corpus.md), which ships with this
plan as requested. The history rewrite that completes it is a separate operation,
recorded in [history](02-history-rewrite.md).

The repository cannot be made public while it carries material from the vendor
and the instruments. That material is also the whole weight of the repository:
the packed history is about 27 MB, and the corpus accounts for nearly all of it.

## Decision

Split `autosuite/` by the origin of its contents, not by file type.

| Path | Origin | In git |
| --- | --- | --- |
| `autosuite/corpus/` | Vendor and instruments: `.app`, `.asfp`, archives, extracted XML, type templates, golden diffs, catalogs, the manual | No |
| `autosuite/docs/` | Analysis written by this project | Yes |
| `autosuite/schema/` | Conclusions distilled from the corpus: empirical type catalog, path profiles, variable-storage observations | Yes |
| `autosuite/tools/`, `autosuite/recipe/` | Code written by this project | Yes |

`.gitignore` denies `autosuite/*` and re-allows only the four tracked
directories. Enumerating what is allowed rather than what is forbidden means
material added later is excluded by default, which matters because the corpus
grows file by file as developers hit new problems.

The corpus is shared inside the team. It is deliberately not pinned: no
submodule, no required version, no canonical set. Two developers holding
different corpora is the expected state, so every check that reads it is
optional and skips when it is absent.

## Agents must not write there

The standing rule is that an agent does not permanently add or change files under
`autosuite/corpus/` unless a human asks for it; temporary output goes to a scratch
directory. Three mechanisms carry it, because prose alone did not:

1. `.gitignore` keeps such a write out of a commit.
2. `.claude/settings.json` denies `Write` and `Edit` under `autosuite/corpus/`, so
   the tool call is refused rather than reviewed after the fact.
3. `.githooks/pre-commit` refuses a commit that stages anything under `autosuite/`
   outside the tracked directories, which covers `git add -f`.

A shell command can still write there. That is a deliberate act by whoever runs
it, and the commit path stays closed.

## Consequences

Once the corpus is ignored, `git status` no longer reveals a file changed in
place, so `autosuite/tools/audit_corpus.py` remains the way to detect that. It is
rewritten to suit a corpus that grows: no fixed counts, each section runs only
when the material it needs is present, a changed file is an error, and added or
missing files are reported as facts. `MANIFEST.csv` travels with the corpus
instead of being committed, where it would have leaked file names such as site
and reaction identifiers.

CI loses the comparisons between generated XML and vendor evidence; those become
developer-local checks. Restoring them would need a private runner or an
authenticated fetch, neither of which is in scope.

## Non-goals

No change to compilation, IR, or generated XML. No submodule and no corpus
version pinning. No decision about publishing the repository itself, which stays
with the maintainer. The two `autosuite/docs/` files that embed vendor XML, and
the recipe input, are confirmed publishable and are left as they are.

## Expected end state

As `sciloom-autosuite` grows, the fragment a test actually asserts on moves into
the test as a committed fixture, and its `@requires_corpus` marker disappears.
When that migration finishes, only the manual retains reference value.

## Version

No bump: repository layout, ignore rules and tooling only. The merged state is
identified as `0.1.0+<merge commit>`.
