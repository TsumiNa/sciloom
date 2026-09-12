# Schema golden fixture matrix

| Feature | Candidate XML | AutoSuite-fixed / re-export evidence | Main conclusion |
|---|---|---|---|
| Empty function | Test01 | real exports | function envelope + components |
| Local variable | Test02_LocalVariable | Test02_FIXED_LocalVariable | variables belong to Macro Task and use modern `<variable>` form |
| Assignment | Test03_SetVariable | Test03_FIXED*, | `SATaskSetVariable.1` + modern metadata/default fields |
| Function call | Test04_ExecuteFunction | Test04_FIXED | call by function ID; modern functiondata envelope |
| IF | Test05_If | Test05_FIXED / TEST05IF_export | conditional Macro Task |
| IF/ELSE | Test06_IfElse | Test06_FIXED / export | multi-condition Macro + branch markers |
| WHILE | Test07_While | Test07_FIXED | while Macro Task |
| direct IF/WHILE | - | Test08 / Test09 | no outer Macro required when no scope feature requires it |
| exact branch nesting | - | Test10_FIXED3 / export | branch body lives in `SATaskCondition/components` |
| typed function I/O | - | Test11_FIXED | item IDs/types/array flags |
| call argument binding | - | Test12_FIXED | call bindings reuse callee parameter IDs |
| sequential zone | - | aaa_sequential_zone | `executionmode=1`, `sequentialzones`, fragment variable |
| agitation intent and angularspeed | - | latest APP / Sample and Run GPC; functionsPackage_3 / 1st_vial | uniform-speed Stir envelope, canonical speed and explicit fixed-zone addressing; see [mapping evidence](16_AGITATION_MAPPING.md) |
| array declarations, bindings and indexing | - | latest APP / Non Zero Array Min / Set ISynth Drawer State; config20260902_2; Suzuki-Miyaura | observed array wire forms plus explicitly derived copy/guard combinations; see [array mapping](17_ARRAY_MAPPING.md) |
