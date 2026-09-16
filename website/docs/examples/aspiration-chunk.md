# Calculate a bounded volume chunk

Given requested volumes and a capacity, calculate how much fits and where to
resume. This example performs arithmetic only. It does not aspirate, dispense or
validate an experimental recipe.

The usable capacity subtracts the air gap, extra volume and safety reserve from
the syringe volume. With requests `[1, 2, 4]` mL and a 5 mL capacity, reserving
0.5, 0.25 and 0.25 mL leaves 4 mL. The first calculation fits `1 + 2 + 1` mL.

| Call | Next index | Unfinished volume | Total aspiration amount |
|---|---:|---:|---:|
| Start at index 0 | 2 | 3 mL | 4.25 mL |
| Resume index 2 with 3 mL remaining | 3 | 0 mL | 3.25 mL |

The extra 0.25 mL is included only when some volume was packed. The caller
supplies the returned index and residual on the next call; the procedure does
not silently resume from stored state.

`chunk_size=4` restricts each calculation to one aligned group of four positions.
Starting at index 3, for example, cannot advance into index 4 in that call.
`max_idx` adds an inclusive caller limit. Indices start at zero.

This adapts a vendor program's packing formula and its caller's group boundary.
It retains their 1e-12 m³ tolerance, but uses an explicit `valid` output instead
of a vendor global error latch. It checks all requested volumes before packing.
Invalid numeric preconditions return `valid=False` with zero volume outputs.
Empty input returns no work; it does not invent a transfer. All runtime values
must still satisfy SciLoom's declared types and finite-number rules.

```console
uv run python examples/aspiration_chunk.py
```

```text
AutoSuite volume-list indexing awaits verified runtime guards.
```

The current AutoSuite target refuses this program's volume-list indexing, so no
ASFP is written. Run the [developer example](aspiration-chunk-ir.md) to inspect
the reference calculation and its JSON document.

??? example "Complete source"

    ```python
    --8<-- "examples/aspiration_chunk.py"
    ```

[Download Python](../_generated/examples/aspiration_chunk.py)
