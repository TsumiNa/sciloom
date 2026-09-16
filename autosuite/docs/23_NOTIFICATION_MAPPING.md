# OK acknowledgement messages

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
