# Stored well text properties

Stage 15 implements A07. Semantic reads/writes are distinct from device
configuration getters and measured, read-only native properties. Raw files are
read-only corpus evidence; generated examples live under `examples/`.

| Layer | Evidence / status |
| --- | --- |
| Existing XML | Primary `app/config20260909_polymerization.app` contains SetProperty user mode 2, value mode 0, property `is_used`, expression `'abc'`, result type `text`. F45/F46 contain GetProperty user mode 2, fallback mode 1, fallback `''`. F45/F50 also show value mode 1 writes. |
| Manual semantics | 3.7.6–7, printed pp. 85–87: reads select one well; missing/incompatible data can stop or use a fallback expression. Single-value writes assign one expression to all selected wells. 3.8.5 p. 115 warns about using empty Zones. |
| SciLoom reference | Explicit directory/store, captured arguments, single-well strict/default reads, whole-selection writes, unknown-well validation, immutable snapshots and events; tests cover Python/direct IR/JSON. |
| Generated XML | Single-value SetProperty, defaulted GetProperty, captured private variables and empty-write guard checked statically against observed fields. |
| Executor | Pending. No re-export, simulation or instrument result is claimed. |

## Write mapping

`WriteWellProperty` captures the text RHS first, then the Zone, into separate
private variables. Its SetProperty task uses these fields in observed order:

| Field | Encoding |
| --- | --- |
| `destzonename` | Captured Zone variable |
| metadata | description, name, edittime |
| `propertytype` | `2`, user property |
| `propname` | Static user-property name, XML-escaped |
| `valuemode` | `0`, single-value expression observed in the primary APP |
| `variablename` | Empty |
| `propvalueexprtext` | Captured text variable as expression |
| `resulttype` | `text` |
| `propertyunit` | Empty |
| `id` | Deterministic task identity |

The task sits inside an If macro with `ZoneSize(captured_zone) > 0`, because an
empty SciLoom selection is a no-op. This wrapper and private-variable capture
are derived combinations, not an assertion that an identical task sequence
already exists in the corpus. Mode 1's array/repetition behavior is not used.

## Read mapping and validation boundary

`ReadWellProperty` captures Zone then default before GetProperty. The task uses
`sourcezonename`, metadata, `propname`, `destvariablename`, `userpropertymode=2`,
`fallbackmode=1`, `fallback=<captured text variable>`, then `id`.

Compilation requires a default and proof of one selected well. A size-one
ForEachZone target establishes that fact at each iteration. Copies retain it;
unknown assignments/call outputs invalidate it. If branches intersect facts.
Loop facts reach a fixed point before checking reads, so a mutation near the end
of one iteration cannot make the next iteration unsafe. Zero iterations cannot
establish a fact. No previous-entry state or interprocedural cardinality promise
is assumed. This is deliberately conservative.

Strict reads and unproven cardinality produce `unsupported_well_property_read`.
Native Stop Application wording alone is not a verified cross-call failure
propagation result. See [the failure gate](24_RUNTIME_FAILURE_GATE.md).

## Remaining platform measurements

Confirm missing and incompatible-property defaults, text escaping/Unicode,
single-value writes over multiple wells, empty-write skipping, and repeated and
nested calls in Editor/Executor. Compare re-exported fields and observed stored
values, not just successful parsing. Record source commit, input/output hashes,
target profile and simulation command. No physical device action is needed.

Corpus checks skip when the relevant material is absent. Updating this note does
not change the evidence manifest or authorize writes into `autosuite/corpus/`.
