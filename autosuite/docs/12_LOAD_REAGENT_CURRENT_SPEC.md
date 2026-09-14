# CSV reagent loading - current AutoSuite-side implementation

Canonical current source: `config20260909_polymerization.app`, especially `Load Reagent Table` and the `Polymerization` Macro Task. `LoadReagentVolume3.asfp` is a historical predecessor of the same function object and is retained to show evolution.

## Current CSV shape

The supplied current file has:

```text
EXP_ID,SOLV_Toluene,MONO_MMA,INIT_AIBN
...
```

There are 48 destination rows. In the supplied example twelve rows are active and each active row totals 3.00 mL; unused rows are blank.

## `Load Reagent Table` interface

Inputs:

```text
integer column_idx
text    fullpath_txt
```

Outputs:

```text
bool     is_end
text[]   expid_array_txt
volume[] reagent_array_vol
text     reagent_name_txt
```

## How a logical reagent index becomes a CSV column

The function increments the caller's logical `column_idx` by 2. Column 1 is reserved for `EXP_ID`; therefore logical reagent index 0 maps to CSV column 2.

It performs two Import CSV operations:

1. Read row 1 without treating it as a header to obtain the current reagent label into `reagent_name_txt`.
2. Read all data rows with header handling enabled:
   - CSV column 1 -> `expid_array_txt`, default `__SKIP__`;
   - current reagent column -> `reagent_array_vol`, default 0 mL.

The exact imported column/task fields can be inspected in `autosuite/corpus/extracted/latest_app/functions/28_Load Reagent Table.asfp`.

## Main polymerization dispatch

The current main polymerization logic iterates reagent columns, resolves `reagent_name_txt` to an AutoSuite zone using `FindZone`, computes `Non Zero Array Min` and chooses a 4NH policy:

```text
if nonzero_min > 0.2 mL and ArrayMax(volumes) > 2.00 mL:
    use ch3/ch4, max_chunk_size 16
else:
    use ch1/ch2, max_chunk_size 8
```

It then calls `Dynamic Transfer Volumectrically` with the selected source zone, reactor destination zone and full per-well volume array.

After reagent loading, the application sequentially scans reactor wells and calls `Label sample ID`, binding each well to the corresponding experiment ID. Downstream reaction and GPC sampling functions can then recover sample identity from the physical well context.

## External versus AutoSuite responsibility

The CSV **producer/validator** is external-tooling territory. Importing the CSV and dynamically dispatching liquid handling are AutoSuite-program territory.

The current AutoSuite implementation does not itself prove the project invariant that every active row totals 3.0 mL. `autosuite/recipe/validate_recipe.py` implements that external validation for the supplied format.
