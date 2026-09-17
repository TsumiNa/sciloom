# Reassessment, acceptance and sequential execution

## Mandatory preflight

Before each refactor, each PR, and after any contradictory discovery:

1. Read applicable repository instructions and this stage's authoritative
   contract, scope, non-goals, dependencies and acceptance.
2. Inspect current main SHA, branch/PR state, package versions, actual interfaces,
   callers and tests. Inspect newly received original/re-export/Executor evidence.
3. Confirm predecessors' remote merge and latest-head checks. A status sentence
   in an old plan is not proof of implementation or native acceptance.
4. Check that the planned author and contributor examples express the intended
   workflow with today's types, ownership, evaluation order and fault behavior.
5. Record baseline, evidence, discrepancy classification, affected plans and
   decision in [decisions](05-decisions.md). Update the contract and stage plans
   before changing an interface. Link unresolved questions in [Q&A](06-qa.md).

A preflight is a real comparison, not a checkbox copied from the last PR.
Do not start coding against an obsolete plan simply because it was accepted.

## Difference handling

| Class | Examples | Action |
| --- | --- | --- |
| A: implementation detail | Moved files, renamed internal functions, an existing reusable tool | Update paths/scope and continue; avoid duplicate work. |
| B: intent-preserving design | Private storage layout, smaller abstraction, independently green PR regrouping | Update contract, affected plans and acceptance first; document why observable behavior is unchanged, then continue. |
| C: insufficient evidence | Missing valid export, uncertain enum/temperature mapping, no Executor result | Keep the affected native rejection; merge only honest implemented/gated scope and continue independent work after its PR merges. |
| D: material deviation | Changed variable lifetime, implicit device action, continuing after cancel, lost results, changed old JSON, hidden globals, expanded Application compiler, incompatible public API | Stop affected implementation and obtain an explicit developer decision before proceeding. |

A class D report must state the original intent, concrete contradictory code or
experiment, affected callers/plan stages, feasible alternatives and their behavior,
and a recommendation. Keep unaffected work reviewable, but do not begin a later
implementation PR while the current one is open. Silence or elapsed time is not
approval. Do not implement a compromise and retroactively update the plan.

Strings encoding typed values, arbitrary payload dicts, hidden parameters,
temporary compatibility APIs and unverified error recovery are not acceptable
workarounds. If one seems necessary, reassess the contract.

## State and evidence

Code status: pending, in-progress, implemented/gated, implemented.
Native status: not-applicable, pending, verified, contradicted.
Record statuses per capability, not just per PR. "Verified" names the exact
version/profile, input/APP/artifact hashes and receipt; reference/static tests
cannot set it. "Compatible" in a deployment report means only the checked
deployment preconditions, never Executor or physical validation.

An unavailable host is not itself a class D discrepancy. Preserve the public
compiler gate, document unfinished native acceptance and finish independently
valid reference/static work. Close a merged implementation PR normally; open a
separate unlock PR only after the receipt meets its acceptance.

## Common acceptance

Each code PR runs the required repository commands:

```console
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest src/sciloom packages/sciloom-autosuite/src examples
uv run pytest autosuite/tools
uv run python autosuite/tools/smoke_test.py
uv run python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
uv run python -m compileall -q examples/proposed_frontend
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
git diff --check
```

Run current CI examples and each added example, verifying same-base-name
companions and absence of unintended tracked changes. After reference changes,
run `uv run python autosuite/tools/audit_corpus.py` read-only. Corpus-free tests
must still pass/skip correctly. Colocate meaningful tests with their behavior.

Every new node/type/contract is covered by structural validation, type/symbol
validation, specialization, reference execution and target handling or explicit
rejection. Preserve existing v4 round trips, class-name-independent wire kinds
and baseline bytes. Test argument capture, immutable snapshots, shared/distinct
resources, branches/calls/loops and absence of later effects after failure.

Document-only R0 runs strict docs build, website tests, local plan links/sections/
Python-snippet syntax checks and diff checks. It does not regenerate examples
or add implementation-mirroring tests.

## Review and version gate

Follow [repository workflow](../../../.github/instructions/branch-and-pr-workflow.instructions.md):
review → address feedback → latest-head checks → squash merge → confirm remote
MERGED → fetch main → next PR. Audit reviews, inline threads, suppressed findings
and general comments. Green CI alone does not pass review.

Last before review, decide the version from actual shipped changes: PATCH fixes,
MINOR capabilities/public interfaces, MAJOR only after explicit approval, none
for plans/docs/tests/tools alone. Update all workspace packages together.
Accepted scope here supersedes only the previous sequence's 0.3.x restriction;
it does not authorize a breaking migration or publication.

## Version

Version: none, execution policy and acceptance documentation only.
