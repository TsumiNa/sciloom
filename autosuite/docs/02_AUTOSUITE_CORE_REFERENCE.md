# AutoSuite 2.47.1.1 - compiler-oriented core reference

This is a deliberately small reference for compiler work. It summarizes only the manual areas that affect representation, validation and testing. Consult the included PDF for complete hardware/task details.

## Product split

AutoSuite is a software suite. Relevant components include:

- **AutoSuite Editor** - configuration, zones and application/task authoring.
- **AutoSuite Executor** - runtime GUI that executes applications; also exposes command-line arguments.
- **AutoSuite Driver Manager** - hardware/driver configuration.
- Other tools such as Extractor and Configuration Manager.

The Editor can launch run/simulation for the currently loaded application. This user experience does not make Editor and Executor the same executable.

## Application model

The Editor has three central authoring domains:

1. **Configuration** - model of the physical Chemspeed platform and devices/elements.
2. **Zones** - named virtual groups of wells/reactors/vials with an enumeration order.
3. **Tasks / application** - executable workflow logic.

A working application is tied to a Machine Configuration; a wrong configuration can prevent correct opening/execution. Base Applications can share machine-specific parameters/zones/calibration information between normal applications.

### Compiler consequence

Do not treat an `.app` as portable program text independent of the machine. A first external compiler should target a known configuration/base/template and preserve machine-specific sections unless intentionally editing them.

## Variables

Global variables are available to Main Application and functions. Macro Tasks can define local variables. Important documented behavior:

- variable types include integer, real number, boolean, text, zone and physical types (volume, length, time, temperature, pressure, etc.);
- variables can be arrays (except zone arrays in the documented model);
- arrays are zero-based;
- macro variables are scoped to the macro and nested tasks/macros;
- a same-name inner variable hides an outer variable;
- unless Reset Variables behavior is enabled, re-entering the same Macro Task does **not** necessarily reset variables to initial values;
- writable zone variables start empty and must be filled before use.

These semantics are not ordinary Python local-variable semantics.

## Macro Task control flow

Documented execution modes include:

- execute N times (loop variable is zero-based; zero skips the macro);
- execute if condition;
- execute while condition;
- IF / ELSE IF / ELSE extension;
- sequential execution over zone fragments;
- batch execution.

Sequential mode introduces sequential zone variables, fragment sizes and a fragment loop/counter. Multiple sequential zones must imply the same number of sequential cycles.

## Functions

Functions are reusable sequences of tasks with typed inputs and outputs. Execute Function calls bind caller expressions/variables to those interfaces. Recursive function calls are not allowed.

AutoSuite additionally supports event functions such as Start, Error and Stop. These are runtime hooks, not normal user-called functions.

## Expressions and units

AutoSuite evaluates expressions at runtime. Supported categories include mathematical, boolean, device, text, array, zone and element expressions.

Critical rule: numeric expression results are interpreted in the context's SI unit unless an explicit unit literal/typed variable provides units. Naked physical constants are therefore dangerous. The compiler should preserve type/unit intent explicitly.

Unit literals such as `34.5mg`, `2h + 30min` are documented.

## Arrays

Useful documented functions include `ArraySize`, `ArrayMin`, `ArrayMax`, `Sum`, search/sort/merge/remove functions, etc. Array autofill in task tables has limitations: arbitrary indexed expressions are not necessarily expanded per row. Ensure arrays contain enough values before a task consumes them.

## Zones

A zone is a named ordered group of wells/reactors/vials. Enumeration order affects processing order. Useful documented functions include `ZoneSize`, `FindZone`, `EnabledWells`, `WellsOfElement`, `WellID`, `WellFullName`, etc.

## Import CSV

Import CSV must be in a Macro Task. It can read a selected row or all rows into arrays. Important result codes:

- `0` success
- `1` column type mismatch; default used
- `2` requested column unavailable; default used
- `3` end of file
- `4` file read/write error

The task supports comma/semicolon/tab delimiter and optional header handling. Expressions can be used for filename and selected-row fields. Values are handled using AutoSuite type/SI-unit rules.

## Set/Get Property

Well/reactor properties provide persistent workflow metadata associated with physical locations. User properties can be written with Set Property and recovered with Get Property. Standard properties include sample name/enabled state plus read-only operational properties. This is the mechanism used by the current program to attach sample/experiment identity to wells.

## File/process integration

AutoSuite provides file-system expression functions and a Run Executable task. These are useful for integration but are distinct from the external compiler itself.

## Executor simulation / CLI

Manual section 4.5.1 documents the relevant command-line capabilities:

```text
AutoSuiteExecutor.exe [file] [/?] [/r] [/sim [xx]] [/s] [/m xx]
```

The same section also documents `/real`, `/c` and `/var` options. Compiler-relevant meanings:

- application file path - load the application;
- `/?` - help;
- `/r` - run after loading;
- `/sim xx` - simulation mode, factor 1-100;
- `/real` - real execution mode;
- `/c` - close after application finishes;
- `/s` - silent mode / fewer user dialogs;
- `/m xx` - ArkSuite module mode (not needed for the compiler's basic smoke test);
- `/var "name=expression;..."` - initialize global variables from command line.

Recommended compiler acceptance command:

```bat
AutoSuiteExecutor.exe generated.app /r /sim 100 /s /c
```

Do not treat local XML parsing as equivalent to this runtime acceptance test.

## Network files

The manual explicitly supports reading/writing network drives after Windows authentication. This supports external generation of CSV/app artifacts without requiring unsupported IPC modifications.

## Sections worth opening in the full manual

- 3.4 Zone Editor
- 3.5 Task Editor / Application Settings
- 3.7 Advanced Tasks (Execute Operation, Run Executable, Get/Set Property, Import/Export CSV)
- 3.8 Macro Tasks
- 3.9 Functions / Start / Error / Stop Functions
- 3.10 Expressions
- 3.11 Expression Functions
- 4 AutoSuite Executor, especially 4.5.1 Command Line Arguments

ArkSuite is deliberately not summarized here beyond what is necessary to avoid conflating it with the compiler; its orchestration role will be reconsidered when vendor documentation is available.

## Error handling primitives relevant to the compiler

Manual section 3.9.4 documents a single application-level **Error Function / OnError**. It runs before the error is shown and the application is stopped. `ErrorMessage` contains the original error text. The manual recommends simple/safe error actions and warns that a second error in the Error Function stops directly. The Error Function is not run when the application is paused/unlocked.

The Stop Function is not equivalent to `finally`: an application error follows the error path rather than relying on normal Stop Function execution.

Several tasks/functions provide nonfatal result-code/fallback modes (Import CSV result, Database Operation Result, selected file operations). A compiler should represent these separately from fatal hardware/runtime faults.

Configuration Manager section 6.5.1 additionally documents system-level **Exception Handling**, which can launch an external executable when an error occurs and pass the error in command-line text (email notification is given as an example). This executable is not run in simulation mode.

## `.asfp/.app` schema note

The supplied manual does not define the XML serialization schema for exported Functions or Applications. It documents Function import/export and program semantics, but no `.asfp/.app` XSD, full XML tag schema, `typeid` table or UUID/reference contract is provided. Use `autosuite/docs/05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md` and the corpus fixtures for serialization details.
