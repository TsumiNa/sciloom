# Volume and duration mapping

Runtime-capabilities stage 3 adds typed Volume and Duration values. Values in IR
and generated expressions use cubic metres and seconds, independently of display
units. The original corpus remains unchanged.

| Semantic type | Parameter keyword | Storage type | SI unit | Emitted display unit | Evidence |
| --- | --- | --- | --- | --- | --- |
| Volume | `volume` | `5` | `m^3` | `ml` | Latest F28/F31 interfaces; F24 and F31 local variables |
| Duration | `time` | `5` | `s` | `s` | `config20260820.app`, `GPC Analysis Prep and No Delay`, `analysis_time` input; latest F13 local variables |

The current APP's extracted functions do not contain a time parameter; the
historical APP supplies that serialization evidence. F13 `next_prep_time` stores
294 with SI `s` and display unit `min`. F31 `fp_eplison_vol` stores 1e-12 with SI
`m^3` and display unit `ul`. These values distinguish canonical storage from a
display-unit count. Manual 3.8.5 p. 112 defines the quantities, and 3.10.1
pp. 141–142 states that arithmetic expressions use SI values.

The compiler therefore emits `number * 1e-06` for `number * mL`, and divides a
volume by `1e-06` for its magnitude in mL. Typed IR checks dimensional compatibility
before AutoSuite receives the numeric expression. Volume/duration arithmetic,
parameters and whole-list copies reuse the existing task/array encoding.

| Verification boundary | Status |
| --- | --- |
| XML/manual | Parameter keywords and storage fields checked against the files above |
| Reference execution | Signed values, finite-number checks, unit construction, arithmetic, copies, intermediate speed validity and JSON round trips tested |
| Static output | Quantity declarations/parameters and SI arithmetic checked with the existing modeled task evaluator; no vendor execution implied |
| Executor | Pending: numerical limits/rounding, duration arrays and failure propagation |

New quantity divisions needing a runtime zero check and speed scaling needing a
runtime sign check receive `unsupported_runtime_guard`. New volume/duration-list
indexing also awaits verified bounds-failure propagation; whole-list operations
are available. Existing numeric division and previously accepted list programs
retain their output. Reference execution implements the full declared semantics.

No transfer, wait, timer or other equipment operation is introduced by these value
types. Floating conversions are not a promise of exact decimal arithmetic or
platform numerical equivalence.
