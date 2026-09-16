# Wait and timer mapping

This document records stage 10's A08 mapping. It separates the supplied XML,
manual semantics, reference execution and pending platform verification. The
authoritative interface is [the runtime contract](../../docs/refactor/runtime-capabilities/01-contract.md#9-wait-and-timer-a08-stage-10).
All corpus paths below are relative to `autosuite/corpus/`; no corpus file is
changed by this implementation.

## Primary evidence

`app/config20260909_polymerization.app` contains ten `SATaskSetTimer.1` tasks
and 36 `SATaskWait.1` tasks: 25 use `waitmode=0`, eleven use `waitmode=2`.
The supplied tasks all enable `cancelwait=1`. The extracted
`extracted/latest_app/functions/13_Run GPC Analysis.asfp` (F13) declares
`break_timer` and `acq_start_timer` in its outer variable Macro and uses them in
nested waits. F11 invokes other functions; it is not the direct timer payload
fixture for this mapping.

The names `timer1` through `timer4` occur in both the current and old Polymerization
macros. This is evidence of separate lexical placements, not proof that setting
the same timer twice in one scope resets it.

| Task | Ordered fields after the component type |
| --- | --- |
| `Chemspeed.SATaskSetTimer.1` | description, name, edittime, timername, id |
| `Chemspeed.SATaskWait.1` | description, name, edittime, time, timeunit, msgtodisplay, waitmode, contacts, timername, cancelwait, id |

Manual 3.6.24, printed pp. 76–77, describes interval waits and waits from a
previously set timer. Peripheral equipment keeps its state while waiting. It
documents an optional Cancel Wait button and a range of 0–79,999 hours.
Manual 3.7.12, pp. 101–102, requires unique timer names and assigns timers the
same limited scope as variables: an outer Macro's timer is visible inside
submacros, while a timer defined inside a Macro is not visible outside it.
Entering execution after a required Set Timer can produce a timer-not-set error.

## Implemented mapping

| SciLoom operation | Native task | Status |
| --- | --- | --- |
| `timer.start()` | Set Timer with deterministic private timername | Observed envelope; reset behavior still needs Executor |
| `wait(duration)` | Wait with waitmode 0 and empty timername | Observed mode and documented interval semantics |
| `timer.wait_until(duration)` | Wait with waitmode 2 and the timername | Observed mode and documented elapsed-time semantics |
| Duration literal | SI seconds in time, timeunit `s` | Existing duration encoding and native seconds evidence |
| Non-cancellable elapsed wait | cancelwait `0` | Manual-derived option; supplied APP uses `1` |

Generated names include the semantic resource identity, avoid variable/name
collisions, and distinguish separate Function instances. A Function with timers
receives an owning Macro even when it has no runtime variables. A timer needs no
device binding. Source inputs and outputs do not gain timer parameters.

The initial profile conservatively requires all starts/resets of a timer to be
in one lexical scope, with waits in that scope or descendants. Core allows a
start in both runtime branches followed by a joined wait; AutoSuite currently
rejects that form with `unsupported_timer_scope`. Moving a start before the
branch would change the clock origin and is not a valid fix. Repeated starts
within one scope are generated as repeated Set Timer tasks, awaiting reset
verification on the actual platform.

Only literal durations within the documented range compile. Dynamic inputs and
expressions require reliable runtime failure propagation, which remains
[unverified](24_RUNTIME_FAILURE_GATE.md); the target returns
`unsupported_runtime_guard` rather than accepting an unchecked negative wait.
Out-of-range constants produce `wait_duration`. The public reference semantics
accept finite nonnegative durations independently of this target limit.

## Verification and remaining gate

| Layer | Result |
| --- | --- |
| Supplied XML | Task field order and fixed empty/default fields compared to the primary APP; cancellation is an explicitly tested override |
| Manual semantics | Interval/elapsed waits, unchanged equipment state, scope, range and cancellation option documented |
| Reference execution | Five-second composed schedule, reached threshold, reset, child time, instance/session isolation, missing service, negative duration and clock overflow tested |
| Generated schedule model | Native payload sequencing compared with the reference interpreter under the stated timer assumptions; does not execute AutoSuite |
| Executor simulation | Pending: native reset/repeated call behavior, names/scope, cancelwait=0, elapsed threshold and unchanged equipment state |

On the AutoSuite host, test a two-second wait followed by a five-second timer
threshold, an already elapsed threshold, repeated starts, repeated Function
calls, two distinct Function instances and an outer-timer/nested-wait case.
Verify Cancel Wait is disabled and no following step runs early. Retain generated
and re-exported XML, simulation output, source commit, application/profile and
Executor version. Do not infer physical timing accuracy from reference or XML
tests. These tests do not authorize operating instruments.
