# Semantic construct -> AutoSuite XML mapping reference

This is a compact map of what the supplied golden fixtures actually establish. For exact bytes, inspect `autosuite/corpus/asfp/` and the normalized diffs in `autosuite/corpus/golden_diffs/`.

## Function definition

A named function owns an executable component list and typed input/output bindings.

Observed envelope:

```xml
<functions>
  <function typeid="Chemspeed.SATaskFunctionDefinition.1">
    <description />
    <name>...</name>
    <edittime>...</edittime>
    <expanded>1</expanded>
    <functiondata>...</functiondata>
    <id>{FUNCTION-GUID}</id>
    <components>...</components>
  </function>
</functions>
```

A function's executable body is `components/component`. A direct component can be an assignment or function call; an outer Macro Task is not intrinsically mandatory.

## Typed function input/output

`Test11_FIXED_RealInOut_DirectSet.asfp` establishes:

```xml
<inputs>
  <count>1</count>
  <item0>
    <id>{PARAMETER-GUID}</id>
    <name>x</name>
    <variablename>x</variablename>
    <variabletype>realnumber</variabletype>
    <isarray>0</isarray>
    <expression />
  </item0>
  <sortType>0</sortType>
</inputs>
```

The same form is used for outputs.

## Local variable declaration

For a local real variable named `x`, the fixed fixture puts the variable on a Macro Task:

```xml
<component typeid="Chemspeed.SAMacroTask.1">
  ...
  <variables sortingType="1">
    <variable>
      <name>x</name>
      <value><type>5</type><value>0</value></value>
      <siunit>1</siunit>
      <unit>1</unit>
      <array>0</array>
      <creationtime>...</creationtime>
      <constant>0</constant>
    </variable>
  </variables>
  ...
</component>
```

Observed storage codes are corpus-derived, not a complete vendor enum: `3` integer, `5` numeric/physical, `8` text-or-zone distinguished by SI unit, `11` boolean.

## Assignment

Assigning the expression `1` to `x` maps to `Chemspeed.SATaskSetVariable.1`
with at minimum the semantic fields:

```xml
<variablename>x</variablename>
<expressiontext>1</expressiontext>
```

Modern real exports also carry default fields such as element selection mode, start index, clear-variable flag, sorting/enumeration fields and an object ID. `Test11_FIXED...` is a useful complete direct-component example.

## Function call

A call is `Chemspeed.SATaskExecuteFunction.1` plus `<functionid>`.

The important non-obvious rule from `Test12_FIXED_CallBinding_RealInOut.asfp` is that each call binding uses the **same parameter ID as the callee definition**. For an input literal, the binding value is stored in `<expression>`; for an output, the destination variable is stored in `<variablename>`.

This means a compiler needs symbol resolution before final serialization.

## IF

A single IF is a `SAMacroTask` with:

```xml
<conditionif>...</conditionif>
<conditiontype>1</conditiontype>
<multicondition>0</multicondition>
```

The body is the Macro Task's `<tasks>`.

The direct-IF fixture proves such a conditional Macro Task can itself be a function component; no artificial wrapper macro is required unless scope/structure requires one.

## WHILE

A WHILE is a `SAMacroTask` with:

```xml
<conditionwhile>...</conditionwhile>
<conditiontype>2</conditiontype>
```

Again the body is `<tasks>`.

## IF / ELSE

The exact current evidence is `Test10_FIXED3_IfElse_ExactStructure.asfp` plus the re-export.

Outer block:

```xml
<component typeid="Chemspeed.SAMacroTask.1">
  <multicondition>1</multicondition>
  <tasks>
    <task typeid="Chemspeed.SATaskCondition.1"> ... </task>
    <task typeid="Chemspeed.SATaskCondition.1"> ... </task>
  </tasks>
</component>
```

Each branch has a condition type and owns its body under **`components`**:

```xml
<task typeid="Chemspeed.SATaskCondition.1">
  <name>If</name>
  <conditiontype>0</conditiontype>
  <condition>1 = 1</condition>
  <components>
    <component typeid="...">...</component>
  </components>
</task>
```

The Else branch observed in the fixture uses `conditiontype=2` and an empty condition. The critical schema fact is branch nesting, not merely the numeric enum.

## Repetition

A normal Macro Task carries `<conditionloop>`. The AutoSuite Manual defines repeat execution and a zero-based loop variable. Real applications show values including literal counts and expressions such as `ArraySize(...)`. The compiler should model repeat count as an expression, not only an integer literal.

## Sequential-zone execution

`aaa_sequential_zone.asfp` isolates the core form:

```xml
<executionmode>1</executionmode>
<fragmentvariable>fragment</fragmentvariable>
<sequentialzones>
  <count>1</count>
  <sequentialzone0>
    <fragmentsize>1</fragmentsize>
    <variablename>z_frag</variablename>
    <zonename>z</zonename>
  </sequentialzone0>
</sequentialzones>
```

Real code may combine sequential execution with conditional mode. Treat these as orthogonal fields in the IR rather than forcing everything into a Python `for` abstraction.

## Built-in / ordinary tasks

Device-independent and device-specific task nodes are distinguished primarily by `typeid` and a set of task-specific child fields. The supplied corpus contains 67 observed `typeid`s. See:

- `autosuite/schema/empirical_type_catalog.json`
- `autosuite/corpus/type_templates/INDEX.csv`
- `autosuite/corpus/type_templates/*_representative.xml`

This is the recommended starting point for backend task adapters.

## Execute Operation

Production files contain many `Chemspeed.SATaskExecuteOperation.1` nodes. The user-facing representation should expose device, operation and typed in/out parameters, while the backend should serialize the exact task envelope learned from a matching real export. This is preferable to hard-coding undocumented numeric/ID details in frontend syntax.

## Main application

A `.app` has an application root with machine configuration, task manager, function manager, zone manager and application parameters. The main task tree lives under the task manager, while reusable functions live under the function manager. The supplied `.app` files are gzip-compressed XML.

For a first compiler, do not synthesize machine configuration from zero. Load a known-good application/template, modify program-level sections in a controlled way, serialize, gzip, then require Executor `/sim` acceptance.

## Native event functions versus project error latch

Event functions use `Chemspeed.SATaskEventFunction.1`. The corpus proves event-function serialization exists, but this package does not assign meanings to numeric `eventtype` values unless separately established.

The current `Throw Error` / `g_error_latched` mechanism is ordinary application logic and must not be confused with native AutoSuite event function semantics.
