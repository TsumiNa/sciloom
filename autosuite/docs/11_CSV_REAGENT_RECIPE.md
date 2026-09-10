# CSV reagent recipe - current observed contract

The current example is `input_0908.csv`:

```csv
EXP_ID,SOLV_Toluene,MONO_MMA,INIT_AIBN
ID260909_1,2.42,0.3,0.28
,,,
...
```

## Data-plane meaning

- one row corresponds to one destination reactor well;
- column 1 is experiment/sample identity (`EXP_ID`);
- each remaining header is expected to resolve to an AutoSuite zone using `FindZone(header)`;
- numeric cells are reagent volumes in mL;
- blank reagent cells are converted by the current Import CSV task to 0 mL;
- blank rows represent unused wells in the supplied production example.

The current application reads the reagent header independently from the all-row numeric array. This is why reagent columns can be iterated dynamically without hard-coding each reagent name in the AutoSuite program.

## Producer-side invariants used by this project

The project design assumes an active polymerization row has a non-empty `EXP_ID` and reagent total of 3.0 mL, while an unused row is blank/zero. This total-volume invariant is a producer/validation responsibility rather than something the current AutoSuite `Load Reagent Table` proves on its own.

Use `validate_recipe.py` for a lightweight external check.
