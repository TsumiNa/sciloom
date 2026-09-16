# Runtime text mapping

Runtime-capabilities stage 2 implements A01. These are static/manual mappings;
Executor and instrument acceptance remain separate.

| Intent | AutoSuite encoding | Evidence |
| --- | --- | --- |
| Text parameters | `variabletype=text`; array flag matches scalar/list | F25 `Import Csv Header`, F28 `Load Reagent Table`, F33 `Get Parent Element Name` |
| Text state | storage `8`, SI unit `text`, observed display-unit field `K/s` | F25/F33 local variables |
| Literal/concatenation | single-quoted expression, `+` | F25 Windows path, F33 defaults; manual 3.10.4 pp. 144–145 |
| Equality | `=` / `<>` | F33 empty-name check; F41 `Set ISynth Drawer Valve` mode checks |
| Length/trim | `TextLength`, `TrimText` | F28/F33/F48; manual 3.11.3 p. 156 |
| Split part | `SplitTextAndGet` | F33; manual 3.11.3 p. 157 |
| Quote/backslash/control characters | quoted runs plus `Char(code)` | derived composition of documented ASCII codes 1–255, manual p. 157 |

Fxx names follow the [audit](18_CAPABILITY_GAPS_AND_ZONE_PARAMETERS.md). The
observed `K/s` field is serialization metadata, not a dimension assigned to text.
Whole-array copy and private call bindings reuse the [array adapter](17_ARRAY_MAPPING.md).

The manual's split example preserves empty tokens and documents empty text for
an unavailable token. SciLoom additionally rejects negative indices and empty
delimiters. Until failure propagation is verified, this target therefore requires
literal nonempty delimiters and literal nonnegative indices; it also rejects new
text-list accesses requiring runtime bounds guards. Reference execution supports
the complete declared text/list semantics.

Native Unicode code-point counting is not established. Length currently accepts
literal BMP text only; runtime text and non-BMP length receive
`unsupported_text_length`. Trim follows the manual's space/newline/tab description;
its precise Unicode whitespace set remains an Executor question.

Literal encoding uses Char expressions rather than assuming undocumented quote
escaping. XML escaping is applied separately. NUL, surrogate code points and
U+FFFE/U+FFFF literals are rejected. Static tests reconstruct only documented
Char/concatenation operations and round-trip XML; they do not execute the vendor parser.

| Verification boundary | Status |
| --- | --- |
| Original XML / manual | Read-only checks for the fields above |
| Reference semantics | Empty text/lists, copying, persistence, Unicode, trimming, split boundaries and failures tested |
| Generated XML | Declarations, parameters, private array copies and escaping tested; `prepare_labels` compiles |
| Executor | Pending: Unicode count, whitespace, Char expressions in initial values/tasks, encoding and failure propagation |
| Instrument | Not performed; no hardware action added |
