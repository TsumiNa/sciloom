# Stage parameters until explicit start

## Goal

Stage parameters until explicit start, following the [authoritative interface contract](00-overview.md).

## Scope

Implement property declarations, runtime ConfigureProperty and explicit StartAgitation/StopAgitation across DSL, IR, interpreter and AutoSuite. Define the complete v4 catalog/static/extension wire vocabulary; unsupported execution paths fail explicitly. Implement definite configuration across calls and backend private context threading. Remove set_speed/SetAgitation and migrate docs, tests and learning outputs together.

## Non-goals

No real getters/duration, public globals or recovery, arbitrary plugin execution, or condition-query execution before stage 6.

## Acceptance

Run shared acceptance; test capture timing, configured/applied separation, persistent/shared state, independent sessions, empty-loop and branch initialization, parent/child state flow, JSON v4 strictness and native typing. Inspect ASFP hidden state and unchanged public entry inputs. Regenerate v4 companions.

Use the exact imports, signatures and semantics in the contract. Update the
contract and affected stage examples in the same PR if an implementation detail
changes its interfaces. Collect domain uncertainties in [Q&A](qa.md); use the
recorded provisional decisions without asking the user individually.

Complete review, address feedback, verify latest-head checks and confirm remote
squash merge before starting the next stage.

