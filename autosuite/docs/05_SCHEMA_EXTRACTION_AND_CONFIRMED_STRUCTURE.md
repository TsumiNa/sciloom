# AutoSuite XML serialization: evidence-based schema notes

## Evidence classes

- **AutoSuite-produced / project-verified**: `*_FIXED_*`, `*_export.asfp`, real application files and exported function packages.
- **Historical generator candidate**: the small non-FIXED `Test01..Test07.asfp` files. These are useful because the delta to the fixed/re-exported files reveals what the old generator was missing.
- **Manual-confirmed semantics**: behavior described by AutoSuite Software Manual 2.47.1.1.

No official XSD was supplied. `empirical_type_catalog.json`, `asfp_path_profile.json` and `app_path_profile.json` are corpus-derived schemas, not vendor XSDs.
## Manual boundary

The supplied AutoSuite Software Manual 2.47.1.1 does **not** provide an official `.asfp` or `.app` XSD/schema, XML tag catalog, `typeid` catalog or UUID/reference specification. It documents the semantic programming model and import/export behavior. Therefore the serialization schema below is empirical and is derived from AutoSuite-produced files in this corpus.


## `.app` container

Every one of the 68 supplied `.app` files begins with the gzip magic bytes `1f 8b`. Decompression yields XML. The newest application root is:

```xml
<application productversion="2.47.1.1" configuration="Swing XL Isynth" baseapplication="" time="...">
  <configuration typeid="Chemspeed.SAElementManager.1">...</configuration>
  <tasks typeid="Chemspeed.SATaskManager.1">...</tasks>
  <functions typeid="Chemspeed.SAFunctionManager.1">...</functions>
  <zones typeid="Chemspeed.SAZoneManager.1">...</zones>
  <parameters>...</parameters>
  <resetvariables>...</resetvariables>
  <passwordhashed>...</passwordhashed>
</application>
```

## `.asfp` container

Observed exported packages use:

```xml
<functions>
  <function typeid="Chemspeed.SATaskFunctionDefinition.1">...</function>
  ...
</functions>
```

A modern normal function has `description`, `name`, `edittime`, `expanded`, `functiondata`, `id`, and `components`. Event functions use `Chemspeed.SATaskEventFunction.1` and an `eventtype` field.

## Function body

`<components>` is a heterogeneous executable list. Child elements are named `<component>` regardless of their specific task `typeid`. Inside a Macro Task the list is `<tasks>` and children are `<task>`.

A direct assignment with no local Macro scope is valid and is seen in `Test11_FIXED_RealInOut_DirectSet.asfp`.

## Local variables

Variables live on a Macro Task, not directly on the function definition. Modern storage is:

```xml
<variables sortingType="1">
  <variable>
    <name>x</name>
    <value><type>5</type><value>0</value></value>
    <siunit>1</siunit><unit>1</unit><array>0</array>
    <creationtime>...</creationtime><constant>0</constant>
  </variable>
</variables>
```

Observed storage codes in this corpus: `3` integer, `5` real/physical numeric, `8` text or zone (distinguished by `siunit`), `11` boolean. This is empirical and not claimed exhaustive.

## Function input/output and call binding

Function parameters are stored under `functiondata/inputs|outputs/itemN`, each with a stable parameter `id`. `Test12_FIXED_CallBinding_RealInOut.asfp` proves that an Execute Function call copies those parameter IDs into its own binding data. Therefore IDs are semantic references, not decoration.

## IF

Single IF is a `Chemspeed.SAMacroTask.1` with `conditiontype=1` and the expression in `conditionif`.

## WHILE

WHILE is a Macro Task with `conditiontype=2` and expression in `conditionwhile`.

## IF / ELSE exact structure

The strongest fixture is `Test10_FIXED3_IfElse_ExactStructure.asfp` and its re-export. The outer Macro Task has `multicondition=1`. Its `<tasks>` contains `Chemspeed.SATaskCondition.1` branch markers. Each branch marker contains `<components>` holding branch body components. This is materially different from putting branch statements as flat sibling tasks.

## Sequential macro

`aaa_sequential_zone.asfp` shows `executionmode=1` plus:

```xml
<sequentialzones>
  <count>1</count>
  <sequentialzone0>
    <fragmentsize>1</fragmentsize>
    <variablename>z_frag</variablename>
    <zonename>z</zonename>
  </sequentialzone0>
</sequentialzones>
```

The current application confirms the same encoding at scale.

## Why the original Test01-07 generator was insufficient

The older generated candidates used `functionid`, `<variables><count><item0>...`, and `<tasks><count>...`, and omitted modern fields such as `edittime`, `expanded`, object IDs, `sortType`, `fragmentvariable`, `executionmode`, `sequentialzones`, and `multiloop`. The FIXED/re-export fixtures are the correct baseline for a new backend.
