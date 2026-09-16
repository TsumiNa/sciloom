# Wall-time text mapping

Stage 9 implements A12 as an ordered ReadWallTime statement. It writes one text
field, so subsequent use cannot duplicate a clock read. JSON remains v4 and old
canonical programs and generated UUIDs are unchanged.

## Source evidence

The primary application's extracted F15, `util Get Time Stamp`, contains a
direct `Chemspeed.SATaskSetVariable.1` component with:

```xml
<variablename>time_txt</variablename>
<expressiontext>DateTime('%Y-%m-%d_%H%M%S')</expressiontext>
<elementselectmode>0</elementselectmode>
```

Its source is
`autosuite/corpus/extracted/latest_app/functions/15_util Get Time Stamp.asfp`.
The task uses the usual Set Variable envelope/default fields; its function
returns `time_txt` as a scalar text output. A corpus-dependent test compares
the full ordered field list and all defaults except IDs, timestamps and labels.
Raw evidence is not changed.

Manual 2.47.1.1, §3.11.1, printed pp. 146–149, describes DateTime as current
system local time, including daylight saving. It accepts an explicit text
format. `%Y`, `%m`, `%d`, `%H`, `%M`, `%S` and `%%` are documented; SciLoom
accepts only this subset, plus literal text. It always supplies a format rather
than relying on the platform's regional default.

## Generated behavior

Each ReadWallTime becomes one Set Variable task with `DateTime(format)` as the
entire expression and the semantic destination as `variablename`. It creates
no extra semantic variable. Child calls and loop iterations execute the read
at their original position. Empty/literal-only formats still issue DateTime;
later concatenation uses the captured field rather than repeating DateTime.

Format strings use the existing text-expression encoder: quotes, backslashes
and control characters are encoded independently of XML escaping. Unsupported
XML/text characters produce an `unsupported_text_literal` target diagnostic at
the clock operation's source. No runtime guard or assumed failure primitive is
needed for the statically validated format subset.

## Independent verification levels

| Evidence | Completed | Remaining |
| --- | --- | --- |
| Original XML | F15 DateTime expression and complete Set Variable envelope compared | Generated package Editor import/re-export |
| Manual semantics | Explicit format, local system time, directive subset | Runtime/platform-specific formatting details |
| Reference execution | Aware fixed clock, explicit changes, single reads, loops/calls, invalid/missing service, immutable ordered events | Does not establish vendor clock behavior |
| Executor | Not available in this environment | Actual read timing, local/DST transitions, calendar boundaries, supported year range, Unicode and escaped literal formats |

The wire scheduling model injects distinct clock strings; it does not run
DateTime or pretend to validate the vendor's formatter. Reference formatting
uses supplied calendar fields, a four-digit minimum year and two-digit remaining
numeric fields, without locale or host timezone conversion. It samples no real
clock by default. Clock time can repeat or move backwards; filename uniqueness
is not promised.

For host verification, import/re-export a generated timestamp function, record
the platform timezone and manual/system clock, and compare its output for the
native F15 format plus each supported directive and escaped literals. Check
repeated calls and loop/child-call reads without assuming a clock tick occurs
between adjacent tasks. Retain source/artifact hashes, AutoSuite version and
Executor command/logs. Keep wall-clock tests separate from elapsed-time timers.

## Version

Version: none, evidence documentation only. The implementation stage records its
lockstep 0.3.x package decision in the stage plan.
