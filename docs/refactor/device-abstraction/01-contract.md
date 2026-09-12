# Record the device contract

## Goal

Record the device contract, following the [authoritative interface contract](00-overview.md).

## Scope

Record the complete interface examples, evidence, architecture diagrams, ordered stages and centralized Q&A.

## Non-goals

No production API or behavior changes.

## Acceptance

Validate local Markdown links and Python snippet syntax; inspect stage labels, collected Q&A and git diff --check.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.

