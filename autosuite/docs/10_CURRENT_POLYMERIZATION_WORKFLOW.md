# Current polymerization workflow reconstructed from the newest application

Source: `config20260909_polymerization.app`.

The application contains 52 functions, 75 zones and 15 global variables. The current reagent-loading path in the `Polymerization` Macro Task is substantially newer than the historical standalone `LoadReagentVolume3.asfp`.

## Current CSV-driven loading path

1. Reset/use `reactor_zone`, debug/mock flags and `g_error_latched`.
2. Iterate reagent columns with `Load Reagent Table`.
3. `Load Reagent Table` adds 2 to its zero-based logical reagent index, reads row 1 to obtain the reagent header, then imports all data rows:
   - column 1 -> `expid_array_txt` (text array), default `__SKIP__`
   - current reagent column -> `reagent_array_vol` (volume array), default 0 mL
4. Resolve the header with `FindZone(reagent_txt)`.
5. Compute `Non Zero Array Min`.
6. Channel policy currently encoded in the application:
   - if minimum non-zero volume > 0.2 mL **and** max volume > 2.00 mL: use channels 3/4, `max_chunk_size=16`;
   - otherwise use channels 1/2, `max_chunk_size=8`.
7. Call `Dynamic Transfer Volumectrically` with 10 uL air gap, 5 uL safe volume and 20 uL extra volume.
8. After all reagent columns, export well logs.
9. Sequentially scan each reactor well and call `Label sample ID`, binding `expid_array_txt[counter]` to the well property.
10. Continue reaction and downstream sampling/GPC tasks.

## The actual supplied CSV

`input_0908.csv` contains 48 well rows and 4 columns: `EXP_ID`, `SOLV_Toluene`, `MONO_MMA`, `INIT_AIBN`. Twelve wells are active. Every active row sums to exactly 3.00 mL (2.42 + 0.30 + 0.28 mL); the other rows are completely blank.

This corrects an older naming assumption in the chat history: the current real file uses the prefix `MONO_`, not `MONR_`.

## Dynamic Transfer current role

`Dynamic Transfer Volumectrically` is an AutoSuite-side function, not external Python. It validates destination/array size and enabled channels, calculates a max index boundary per chunk, opens only the selected reactor destination range, packs aspiration across enabled 4NH channels, dispenses chunks, then closes the corresponding valve region. It uses helper functions including `Syringe Capasity`, `Get Aspirate Chunk`, `Aspirate From Source`, `Dispense Chunk`, `Get Well Zone With Index` and `Set ISynth Drawer Valve`.

The current application is the source of truth over older standalone copies when they differ.
