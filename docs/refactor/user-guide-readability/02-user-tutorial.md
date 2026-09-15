# Five independent tutorial snapshots

## Goal

Teach the experiment in the order defined by the [contract](00-overview.md).

## Scope

Replace all five lessons together; retain URLs and update navigation, labels and
links. Add the remaining three tutorial examples and companions, explicit public
downloads and CI/mypy coverage. Validate user pages against complete source files;
remove only the user's append-only series registration. Preserve the developer
series. Correct claims about measurement and runtime execution in touched material.

## Non-goals

No generic tutorial framework, public API changes or hardware execution.

## Acceptance

Run PR1's full checks. Verify both enabled branches, threshold values, empty
lists, loop reset, saved state and distinct instances/sessions. Compare generated
companions, actual rendered code and downloads. Each lesson must run independently;
developer cumulative tests must still pass. Check folded code and navigation.

## Version

Version: none, documentation, examples and tests only.
