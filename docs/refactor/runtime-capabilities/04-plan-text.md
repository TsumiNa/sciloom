# Stage 2: Runtime text

## Goal

Implement A01 without weakening existing scalar/list semantics.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Native str and list[str] declarations, defaults, IR literals/types, codec, reference values, scalar/list binding and target encoding. Concatenation, equality, len, trim and split_part with exactly the contract's boundaries. Resolve trusted intrinsic identities in DSL. Document and demonstrate the supported AutoSuite text profile.

## Non-goals

No implicit conversions, string truthiness, regex, slicing or arbitrary string methods. No preemptive addition of other twelve-feature nodes.

## Acceptance

Test empty text/list, copying, parameters, bad declarations, Unicode, quotes, backslashes, CR/LF, split empty tokens/missing parts and invalid selectors. Distinguish proven target subsets from operations requiring the later failure gate. Preserve old v4/ASFP fixtures and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and verification

The lazy author namespace `sciloom.text`, TEXT scalar/list types and three typed
expression nodes now cover this stage. Python and direct-IR tests exercise JSON
round trips, Unicode code-point length, the explicit trim set, split boundaries,
argument validation, copy isolation and state retention. Existing v4 golden
JSON and ASFP hashes remain unchanged.

AutoSuite emits text storage, parameters, whole-list copies and documented text
expressions. It refuses runtime split guards, guarded text-list indexing and
unverified Unicode length cases. See the [mapping record](../../../autosuite/docs/19_TEXT_MAPPING.md)
and RC-QA-004/008; no Executor validation is claimed.

`examples/prepare_labels.py` and its ASFP companion are runnable and included in
the explicit website download list. The public reference and API pages describe
the new vocabulary and target limitations.

Review added explicit scalar-text child-call coverage through Python/JSON
reference execution and AutoSuite scalar input/output bindings, alongside text
intrinsic calls in the same parent method.

Local acceptance: 411 code/example tests, 79 website tests, mypy (71 files), Ruff,
strict website build, all 14 current example commands, proposed-example syntax,
AutoSuite smoke, recipe validation and corpus audit. Existing example companions
remain byte-identical. Remote review and latest-head CI are the merge gate.

## Version

Version: PATCH 0.3.0 → 0.3.1 for both workspace packages, by the user's explicit series-level version decision. JSON stays v4.
