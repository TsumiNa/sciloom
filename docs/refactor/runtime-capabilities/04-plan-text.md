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

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

