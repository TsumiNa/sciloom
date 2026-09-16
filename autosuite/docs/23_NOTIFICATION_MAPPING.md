# OK acknowledgement messages

**Platform gate: unverified.** ASFP generation is available for inspection and
host simulation. Physical use of the generated notification is not accepted
until the deployment host passes the checks below. This document records no
Executor result.

## Source evidence

The primary `corpus/app/config20260909_polymerization.app` contains 12
`Chemspeed.SATaskUserDialog.1` tasks: seven `showmessage`/`ok`, four
`showmessage`/`stop`, and one `showmessage`/`okstop`. The first OK task displays
`SplitTextAndGet(WellFullName(z),':',0)`. These are observations of this received
corpus, not a required corpus inventory.

The earlier capability audit cited F21/F47 together with the APP. More precisely,
F21 (`21_Validate Polymerization Zone.asfp`) uses Stop, and F47
(`47_Report Error.asfp`) uses OK/Stop. The representative template
`63_Chemspeed.SATaskUserDialog.1_representative.xml` also uses OK/Stop.
They establish the envelope, not this stage's button policy. The primary APP's
seven OK-only occurrences supply that policy directly.

Manual 2.47.1.1 section 3.6.17, printed pp. 66–71, documents message expressions,
button choices and wait time. A maximum wait time of zero displays the dialog
indefinitely; a nonzero timeout permits automatic continuation. The post-dialog
pause is a separate option. This compiler uses no timeout and no post-dialog
pause, with no input/result variable. Stop buttons are not treated as proof of
fatal propagation; stage 8 owns that separate evidence gate.

## Mapping

Semantic Notify holds one text expression. The target captures it into a private
text variable before emitting the dialog. The variable remains absent from both
public semantic programs. The observed field ordering and full `.1` type ID are
preserved. In particular:

| Field | Value / meaning |
| --- | --- |
| `dialogtype` | `showmessage` |
| `buttonoption` | `ok` |
| `interpretmessageasexpressionflag` | `1`, reading the captured variable |
| `maxwaittimeexpression` / `maxwaittimeunit` | `0` / `s` |
| `defaultpauseafterdialog` | `0` |
| `resultvariablename`, `initialvalue`, answer expressions | Empty |

Display dimensions, font and other envelope defaults match the original OK
task. `softstopping=1` is retained as an observed field, without assigning it a
new recovery or termination guarantee. No source-code parameter exposes these
vendor fields. Existing text escaping and expression restrictions still apply;
wrapping an unverified indexed text read in Notify cannot bypass target guards.

## Verification

| XML evidence | Manual semantics | Reference execution | Executor |
| --- | --- | --- | --- |
| Ordered fields and defaults compared with an OK task from the primary APP; private capture scheduling tested | Message expressions, indefinite zero wait and separate pause documented | Python/direct IR/JSON; explicit copied responses, absent/exhausted service, loops/calls, source retention, immutable events and failure ordering tested | Pending: dialog display, indefinite blocking, exactly one continuation after OK, nested calls and text rendering |

The test wire evaluator assumes an acknowledgement to inspect emitted scheduling;
it cannot prove that AutoSuite's UI blocks. The reference interpreter never opens
a real dialog and never supplies a response implicitly. Verify with a visible
log marker after the dialog in Executor before relying on this task operationally.
See [RC-QA-007](../../docs/refactor/runtime-capabilities/21-qa.md).

## Host acceptance procedure

Use the generated `examples/confirm_samples.asfp` in a disposable, known-good
AutoSuite application with configured logging. Keep instruments in simulation.
The application must call the function with a fixed sample label, so the
subsequent `recipe/confirmed` log can be distinguished from unrelated records.
SciLoom currently generates the function package, not this test application.

Run the prepared APP with the documented simulation options from
[the Executor reference](15_EXECUTOR_SIMULATION.md). For an interactive dialog
probe, omit `/s` (silent mode reduces dialogs):

```bat
AutoSuiteExecutor.exe notification-probe.app /r /sim 100 /c
```

This is a host procedure to perform, not a command executed in this checkout.
Acceptance requires all of the following, independently of reference tests:

1. Before OK, the correct message remains displayed and no matching
   `recipe/confirmed` record or later caller marker appears. Record the observed
   wait interval; the zero-timeout field must also survive Editor re-export.
2. One OK produces exactly one matching record and one subsequent caller marker.
   Neither is duplicated after the dialog closes.
3. A child Function call obeys the same ordering. A two-iteration caller shows
   one dialog per iteration and requires two acknowledgements; the first OK
   must not acknowledge the second dialog.
4. Re-export preserves the OK-only/no-timeout/no-post-dialog-pause settings.
   Record rendering checks separately for any non-ASCII or escaped text used.

Keep source commit, package/target and AutoSuite versions, ASFP/APP hashes,
re-exported task, command, observed event counts and Executor logs with the
result. Do not infer blocking from a successful exit code, simulated wire
evaluator, or the absence of errors alone. Production adoption remains gated
until this evidence is recorded; failure leaves the capability unverified.
