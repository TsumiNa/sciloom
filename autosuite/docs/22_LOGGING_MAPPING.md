# Typed runtime logging

## Source evidence

The primary `corpus/app/config20260909_polymerization.app` contains five
`Chemspeed.SATaskLogData.1` tasks: three `realnumber` records and two `text`
records. `corpus/extracted/latest_app/functions/24_Sample and Run GPC.asfp`
contains the text record `'Start Sampling'` under category/stream `'log'`.
`corpus/type_templates/49_Chemspeed.SATaskLogData.1_representative.xml`
preserves the same envelope. A read-only scan of the 68 APP snapshots found
432 pressure, 358 realnumber, 120 text, 30 weight and 15 temperature log tasks.
These counts describe this received corpus, not a required canonical dataset.

The empirical type catalog records the ordered fields
`categorynameexpression`, `streamnameexpression`, `expressiontext`, `resulttype`,
`description`, `name`, `edittime`, `id`. SciLoom preserves this envelope and the
complete observed type identifier; the `.1` suffix is not calculated.

Manual 2.47.1.1 section 3.7.11, printed pp. 100–101, describes logging expression
results, runtime category/stream text and a chosen property type. It requires a
Macro context with at least one variable. The description mentions both computed
expressions and an expression referring to a variable in that Macro. The
implementation satisfies both readings by first capturing operands in locals.

## Mapping and evaluation order

The Semantic IR LogValue stores a value expression, category expression and
stream expression. Expression typing determines the scalar result type; no
AutoSuite field or formatting instruction enters public IR.

The backend captures value, category, then stream into three private typed
variables. Each capture follows its expression prerequisites. It then emits
LogData referring to those variables. This provides a Macro with local storage
even for a literal-only Function, preserves one evaluation per argument, and
keeps changes after the operation from changing its captured values. Private
variables remain absent from semantic_ir and specialized_ir.

| Semantic type | `resulttype` | Evidence level |
| --- | --- | --- |
| float | `realnumber` | Directly observed latest APP |
| str | `text` | Directly observed latest APP and F24 |
| int | `integer` | Documented property-type choice combined with existing variable/parameter encoding |
| bool | `bool` | Same derived combination |
| RotationalSpeed | `angularspeed` | Same derived combination; canonical 1/s |
| Volume | `volume` | Same derived combination; canonical m³ |
| Duration | `time` | Same derived combination; canonical seconds |

No list/Zone/object formatting or device telemetry is introduced. Text literal
encoding uses the existing quoted-run/Char logic; XML escaping remains separate.
Argument expressions retain existing target restrictions: putting an unsupported
guard or operation inside a log does not bypass target validation. Application
logging configuration is outside this Function compiler.

## Verification status

| XML evidence | Manual semantics | Reference execution | Executor |
| --- | --- | --- | --- |
| Task child fields/order compared with F24; static scheduling and all current type encodings checked | Macro context, expression result, property type and runtime labels documented | Python/direct IR/JSON, captured quantities, loops/calls, device/log ordering, failure retention and snapshots tested | Pending for all generated profiles, persisted values/units, text encoding and exact type acceptance |

The test wire evaluator checks scheduling under assumed expression/task semantics;
it is not AutoSuite execution. Static success does not prove that records reach a
configured log store. Verify the derived scalar/quantity combinations and exact
stored values on Executor; see [RC-QA-009](../../docs/refactor/runtime-capabilities/21-qa.md).
