# Numeric expressions and rounding boundaries

## Source evidence

Manual 3.11.7, printed page 162, defines `abs(x)` as magnitude and `floor(x)` as
the greatest integral value not greater than x. It says the mathematical
functions return real numbers. It lists `round(number, precision)` without
specifying half-value ties or native integer/real limits. Storage type IDs are
not evidence of those limits.

The latest-app function `30_Dynamic Transfer Volumectrically.asfp` contains
`floor(current_idx / max_chunk_size) * max_chunk_size + max_chunk_size - 1`
and `abs(current_residual_vol - ch1_start_vol)` inside a condition.
`35_Get ISynth Drawer Index.asfp` uses `floor((well_id_int - 1) / 8)`.
The older `functionsPackage_3.asfp` contains one-argument native round in
measurement expressions; it does not establish ties-to-even.

## Mapping

| SciLoom operation | AutoSuite expression | Boundary |
| --- | --- | --- |
| `abs(int/float/Volume/Duration)` | `abs(operand)` | Retain the semantic type; quantities use SI numbers |
| `floor(float)` | `floor(operand)` | Result is integral; SciLoom assigns it to its typed integer result |
| `floor(int)`, `round(int)` | Original operand | Identity; no new real conversion or native round |
| `round(float)` | No emission | `unsupported_rounding` until tie and expansion-range evidence exists |

Each operand's prerequisite tasks run once, before the expression uses the
captured result. Source syntax and IR retain the high-level Unary operation;
neither contains vendor expression text. No unchecked arithmetic expansion of
round, inferred machine width or runtime numeric guard is added.

## Verification status

| XML evidence | Manual semantics | Reference execution | Executor |
| --- | --- | --- | --- |
| Read-only checks match floor/abs spellings in F30; generated task expressions and operand scheduling checked | abs/floor definitions above; round ties unspecified | Negative/positive values, half ties, large integers, quantity magnitudes, type/nonfinite failures, Python/IR/JSON paths | Pending; test wire evaluator assumes documented math and is not vendor execution |

Reference tests of huge integers do not certify native storage or conversion
limits. The new stage refuses floating round at every input range; no claim of
round equivalence is derived from the spelling alone. Existing numeric v4
programs and serialized baselines are unchanged. Track remaining numerical
questions in [RC-QA-004](../../docs/refactor/runtime-capabilities/21-qa.md).

## Combined volume calculation

The project-authored `examples/aspiration_chunk.py` adapts F31 `Get Aspirate
Chunk` and F30's aligned group boundary. F31 computes usable volume as
`syringe_vol - airgap_vol - extra_vol - safe_vol`, packs whole or partial
requests, and adds extra only for nonempty packed work. The retained tolerance
is 1e-12 m³. F30 supplies the `floor` boundary shown above.

The adaptation prevalidates all volume entries and rejects a residual exceeding
the original request by more than the retained tolerance. It returns an explicit `valid`
Boolean instead of the vendor global error latch, and defines zero outputs for
empty/no-work input. It does not port the liquid-transfer tasks or the original
error handler. Source/JSON reference tests cover partial fills, resume, exact and
tolerance boundaries, aligned groups, invalid input and repeated calls. A
read-only corpus test checks both formulas. Native volume-list access remains
rejected by the runtime-guard gate; no ASFP or hardware-equivalence claim is made.
