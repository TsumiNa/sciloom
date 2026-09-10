# How the schema was extracted and verified

The strongest part of the supplied corpus is that it preserves a sequence of deliberately minimal experiments.

## 1. Minimize one semantic feature

The minimal XML fixtures isolate: empty function, local variable, assignment, function call, IF, IF/ELSE and WHILE. The old source-language probes have been removed; their candidate XML and AutoSuite-fixed counterparts remain available for comparison.

## 2. Compare candidate XML to AutoSuite-fixed/re-exported XML

Examples:

- `Test02_LocalVariable.asfp` vs `Test02_FIXED_LocalVariable.asfp`
- `Test03_SetVariable.asfp` vs `Test03_FIXED*_SetVariable.asfp`
- `Test05_If.asfp` vs `Test05_FIXED_If.asfp` / `TEST05IF_export.asfp`
- `Test06_IfElse.asfp` vs `Test06_FIXED_IfElse.asfp` / `TEST06FIXEDIFELSE_export.asfp`

This exposes mandatory envelope/default fields and container conventions.

## 3. Design second-generation probes for ambiguity

The `Test08..Test10` fixtures specifically test whether IF/WHILE/IFELSE can be direct function components without an artificial outer Macro Task. `Test10_FIXED3_IfElse_ExactStructure.asfp` establishes the exact branch nesting.

## 4. Probe typed function interfaces

`Test11*` establishes direct function input/output serialization. `Test12*` establishes call binding and parameter-ID reuse.

## 5. Probe sequential execution separately

`aaa_sequential_zone.asfp` isolates `executionmode=1`, fragment size, sequential variable name and source zone name.

## 6. Validate against production-scale exports

The 59 ASFP files and 68 APP files are then used as a corpus check. `autosuite/schema/empirical_type_catalog.json` contains all observed `typeid`s and child-field sets. This is essential because a minimal probe can accidentally learn a special case.

## 7. Use Executor simulation as final authority

Static XML similarity is not sufficient. On the AutoSuite host, generated `.app` must pass an Executor simulation. The recommended CI gate is `/r /sim 100 /s /c` and log/exit inspection.

## What remains unproven

- There is no vendor XSD in the supplied material.
- Not every possible task/device type is represented.
- XML child ordering may matter in some serializers even when generic XML semantics say it should not.
- Version 2.47.1.1 compatibility should be tracked explicitly; future AutoSuite versions may change fields.
