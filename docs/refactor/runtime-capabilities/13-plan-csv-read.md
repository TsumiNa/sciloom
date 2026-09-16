# Stage 11: Typed CSV reads

## Goal

Implement A05 row and column reads with explicit results and failure policy.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Implement Column metadata, runtime selectors/default capture, read/try-read forms, fixed tuple bindings and named statuses. Add typed read IR, in-memory files and opt-in local adapter, parsing/type/unit checks, atomic result-field commit and bounded AutoSuite generation. Record parser profiles and gate needed failure checks.

## Non-goals

No header-to-variable lookup, implicit field creation, DataFrame, arbitrary slicing, implicit array growth, filesystem transaction or Python evaluation of cells.

## Implementation decisions

The [concrete stage-11 contract](01-contract.md#stage-11-concrete-records-and-parsing-profile)
defines ReadCsv/CsvColumn, fixed tuple destinations, the reference CSV dialect,
strict decimal/Boolean conversion, byte adapters and outcome events before code
is added. The manual's expression evaluation and integer truncation differ from
these semantics. Native envelope/probe generation and explicit Target rejection
must remain distinct from verified compilation; no result-code aggregation or
unchecked parser equivalence is assumed. The fatal-error gate also remains open.

## Acceptance

Test headers/zero-based selectors, single/multiple columns, empty data, missing rows/cells/files, invalid types/defaults, volume units, output isolation and snapshot copies. Check mixed column policies rather than trusting aggregate vendor codes. Reproduce F28's bounded recipe path; validate evidence matrix and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation status

The stage implements the four read forms, fixed typed columns/results, native
status names, byte services, literal parsing and complete result commit. Python,
direct IR and JSON paths execute through the same immutable v4 records. New
consumers explicitly preserve or handle ReadCsv; existing canonical fixtures
and AutoSuite outputs remain unchanged.

The F28-shaped author example selects a heading and aligned ID/volume columns;
the developer companion exercises direct IR and JSON with MemoryFiles. Public
downloads are explicitly listed. Reference execution, schema errors, type-checking,
UTF-8/quoted text, conversion/defaults, unit scaling, IO/EOF, selector capture,
provider failures, normalization failure and list isolation have regression tests.

Fourteen native probe artifacts verify observed task structure and prepare host
measurement; they do not establish parser equivalence or fatal propagation.
The manual's cell-expression and integer-truncation behavior conflicts with
strict literal reads. AutoSuite therefore gives `unsupported_csv_semantics` for
every ReadCsv rather than generating misleading ASFP. The
[mapping record](../../../autosuite/docs/27_CSV_READ_MAPPING.md) lists the remaining
Editor/Executor acceptance work and source evidence. No raw corpus was rewritten.

Validation includes the full code/example/tool suite, mypy, ruff, 28 example and
syntax commands, the strict website build and 86 documentation tests, smoke,
recipe checks, corpus audit and diff whitespace checks. Review/latest-head CI
and squash merge remain the gate before stage 12 begins.

## Version

Version: PATCH 0.3.9 → 0.3.10 for typed CSV reads and explicit file services,
following the user's 0.3.x sequence decision. Both workspace packages move in
lockstep. Review corrections distinguish adapter path validation from provider
failures and fix the reference index count; they retain this scope and version.
JSON remains v4; no release tag or PyPI publication.
