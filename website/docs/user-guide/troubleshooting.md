# Troubleshooting

Find the problem below, then use the diagnostic code to identify its cause.
Fix the Python source and compile again; do not repair the generated XML by hand.

Source and compilation errors print a message with a code in square brackets,
such as `[type_mismatch]`. Some errors while constructing a program are
ordinary Python `TypeError` or `ValueError` exceptions instead.
[Developer diagnostics](../developer/troubleshooting.md#read-diagnostic-fields)
explains how to inspect their structured fields when available.

## A speed assignment is rejected

A plain number has no rotational-speed unit. With
`speed: Output[RotationalSpeed]`, this assignment produces `type_mismatch`:

<!-- correction: speed wrong -->
```python
self.speed = 600
```

Import `rpm` and supply the unit:

<!-- correction: speed fixed -->
```python
self.speed = 600 * rpm
```

For a speed chosen by the caller, declare `Input[RotationalSpeed]`. Runtime
number-times-unit construction is supported by the language; AutoSuite currently
refuses speed construction that needs an unverified runtime sign check.

| Code | Cause | Fix |
| --- | --- | --- |
| `quantity_literal` | a constant unit value is nonfinite or invalid for its quantity | use a finite value; speed must be nonnegative |
| `unsupported_runtime_guard` | runtime speed construction or a variable quantity divisor | supply a typed speed input or a literal nonzero divisor; see [quantity rules](reference/runtime-language.md#physical-quantities) |
| `type_mismatch` | `integer` to `rotational_speed`, `real` to `integer` | use the declared type ([tutorial 2](tutorial/inputs-and-units.md)) |

## A counter does not reset, or cannot be read in Python

`count: Var[int] = 0` supplies the initial state, not a reset at each call.
Add `self.count = 0` at the beginning of `run` when that is what the
procedure needs. For a cumulative counter, leave it out.
See [lesson 5](tutorial/compile.md).

Writing `print(program.count)` in the Python script cannot inspect that
runtime value. To return a result to the generated function's caller, declare
an `Output` and assign the count to it inside `run`.

| Code | Cause | Fix |
| --- | --- | --- |
| `runtime_field_read` | `instance.field` in host code | read it only inside the runtime method ([lesson 5](tutorial/compile.md)) |
| `runtime_field_write` | assigning a runtime field in `__init__` | store host configuration under another name ([specialization](advanced/specialization.md)) |

## A field declaration is rejected

Runtime values need a role and a supported type. For working storage,
`count: Var[int] = 0` is complete. Inputs and outputs have no defaults.
A plain declaration such as `count: int = 0` is host configuration.

| Code | Cause | Fix |
| --- | --- | --- |
| `class_schema` | a bare alias, or a nested role | declare exactly one role ([declarations](reference/declarations.md)) |
| `class_schema` | an unsupported value type | use a supported scalar type or a list of one ([runtime language](reference/runtime-language.md)) |
| `class_schema` | `list`, `list[Any]`, `list[list[...]]` | a one-dimensional typed list |
| `class_schema` | a Var without an initial value | add a value, such as `= 0` or `= 0 * rpm` |
| `class_schema` | a list Var without a list initial value | supply a Python list, such as `= []` |
| `class_schema` | a literal of the wrong type, `Var[int] = 1.5` | match the declared type |
| `class_schema` | `Input` or `Output` with `= value` | remove the default; pass the value or embed host configuration ([specialization](advanced/specialization.md)) |
| `class_schema` | changing an inherited field's role, type or initial value | keep the inherited definition; vary host settings instead |
| `class_schema` | a field named like a Function method | rename the field |
| `class_schema` | `shaker: Agitator = ...` | bind hardware through the target ([lesson 1](tutorial/first-function.md)) |
| `class_schema` | a private or reserved slot name | a public identifier |
| `class_schema` | replacing an inherited slot with another value, type or field role | keep the base slot |

## A runtime method or statement is rejected

Keep the Function in an ordinary `.py` file, with one `@runtime` method
that takes only `self`. Its body supports a
[subset of Python](reference/runtime-language.md); constructors still use
ordinary Python.

For example, with `values: Input[list[float]]` and `total: Output[float]`,
a `for` loop is not supported:

<!-- correction: loop wrong -->
```python
self.total = 0.0
for value in self.values:
    self.total += value
```

Declare `index: Var[int] = 0` and use `while`. Reset the index on each call:

<!-- correction: loop fixed -->
```python
self.total = 0.0
self.index = 0
while self.index < len(self.values):
    self.total += self.values[self.index]
    self.index += 1
```

| Code | Cause | Fix |
| --- | --- | --- |
| `runtime_method` | none or two `@runtime` methods | keep one |
| `source_unavailable` | a notebook cell, `exec()`, `async def` | move the class to a `.py` file |
| `python_subset` | `For`, `Return`, `Try`, `Break`, ... | see the [runtime language](reference/runtime-language.md); loops use `while` ([lesson 4](tutorial/lists-and-loops.md)) |
| `python_subset` | a chained comparison, an unsupported call or attribute chain | split comparisons; use declared fields and the supported calls in [runtime syntax](reference/runtime-language.md) |
| `python_subset` | parameters on the runtime method | declare `Input` fields ([tutorial 2](tutorial/inputs-and-units.md)) |
| `python_subset` | calling a helper or a function that is not an attribute | create the child in `__init__` ([composition](advanced/composition.md)) |
| `python_subset` | the attribute is not a Function instance | assign a Function instance in `__init__` |
| `python_subset` | `self.items[1:]` | copy the whole list or access existing elements in a loop; slicing is unsupported |
| `python_subset` | `len()` of a number or with keywords | `len(self.items)` or `len(self.label)`; see the AutoSuite text limits below |
| `python_subset` | a module-level name `len` | remove the shadowing name |
| `runtime_field` | a local variable or an undeclared field | declare a `Var` |
| `host_value` | a host list or arbitrary object read through `self` | embed scalars only, including text ([specialization](advanced/specialization.md)) |

## A condition or list calculation is rejected

A number cannot stand in for a Boolean. With `count: Input[int]` and
`selected: Output[bool]`, this condition raises `condition_type`:

<!-- correction: condition wrong -->
```python
if self.count:
    self.selected = True
else:
    self.selected = False
```

Write the comparison explicitly:

<!-- correction: condition fixed -->
```python
if self.count > 0:
    self.selected = True
else:
    self.selected = False
```

For lists, check the declared element type and index. Indexed writes update
existing elements; they cannot grow a list.

| Code | Cause | Fix |
| --- | --- | --- |
| `list_type` | `[]` assigned to something untyped | assign to a declared list field |
| `list_type` | mixed or nested literal | one element type |
| `list_type` | `self.x[0] = ...` on a scalar | declare a list field |
| `operator_type` | arithmetic on a Boolean, a comparison of a speed with a number | use numeric operands for arithmetic and ordering; compare speeds only for equality or inequality |
| `operator_type` | `self.a == self.b` on lists | compare elements in a loop |
| `condition_type` | `if self.count:` | `if self.count > 0:` |
| `index_type` | a float or Boolean index | use an integer literal or integer field |
| `list_element_type` | a literal with the wrong element type | match the list's element type |

## AutoSuite rejects Boolean combinations

The AutoSuite target rejects `and` and `or` with
`unsupported_short_circuit`. For Boolean inputs `a`, `b` and output
`both`, replace:

<!-- correction: boolean wrong -->
```python
self.both = self.a and self.b
```

with nested conditions:

<!-- correction: boolean fixed -->
```python
self.both = False
if self.a:
    if self.b:
        self.both = True
```

Python source analysis accepts `and` / `or`; this restriction belongs
to the AutoSuite target.

| Code | Cause | Fix |
| --- | --- | --- |
| `unsupported_short_circuit` | `and` / `or` | nested `if` ([AutoSuite rules](advanced/autosuite.md)) |

## AutoSuite rejects a text operation

The reference interpreter supports the full [text vocabulary](reference/runtime-language.md#text).
Some AutoSuite mappings still need platform verification. These diagnostics
identify the restricted operation before generating a function package:

| Code | Cause | Current option |
| --- | --- | --- |
| `unsupported_rounding` | `round()` of a float in an AutoSuite program | use reference execution until the target's ties-to-even mapping is verified; `floor()` has different semantics and should only be used when rounding down is intended |
| `unsupported_text_length` | runtime text or non-BMP text passed to `len()` | use reference execution; target length currently accepts BMP literals only |
| `unsupported_runtime_guard` | a dynamic split selector, empty delimiter, negative split index or guarded text-list indexing | use a literal nonempty delimiter and nonnegative index; pass whole text lists |
| `unsupported_text_literal` | NUL, surrogate code points or U+FFFE/U+FFFF | remove characters that cannot be represented in the XML expression |

Use `text.trim` and `text.split_part` inside `@runtime`. Calling these markers
directly from ordinary Python raises `TypeError`.

## AutoSuite rejects an output list

With `values: Input[list[float]]`, `result: Output[list[float]]` and
`index: Var[int] = 0`, the output below has no elements to update:

<!-- correction: list-output wrong -->
```python
self.index = 0
while self.index < len(self.values):
    self.result[self.index] = self.values[self.index] * 2.0
    self.index += 1
```

Copy the input first. The result then has the required length, including zero
for an empty input:

<!-- correction: list-output fixed -->
```python
self.result = self.values
self.index = 0
while self.index < len(self.values):
    self.result[self.index] = self.values[self.index] * 2.0
    self.index += 1
```

| Code | Cause | Fix |
| --- | --- | --- |
| `list_output_initialization` | a list output first written inside a loop or a branch | assign the whole list first |

## A call to another step is rejected

Create the child in `__init__`. In `run`, supply every input and receive
every output. Store returned values in whole fields before using them in an
expression or list element. See [composition](advanced/composition.md).

| Code | Cause | Fix |
| --- | --- | --- |
| `call_binding` | wrong number of arguments or destinations | match the child's inputs and outputs |
| `call_binding` | a misspelled or repeated keyword, `*args` | name each input once |
| `call_binding` | a missing input | supply it |
| `call_binding` | `self.items[0] = self.child()` | bind to a field, then write the element |
| `device_reference` | sharing a slot from an unrelated instance | share the parent's reference with its child; do not borrow a slot from an unrelated instance |
| `call_binding` | an unbound input or output | bind every declared input and output |
| `recursive_call` | a Function calling itself, directly or indirectly | a loop |

## The shaker binding is rejected

The dictionary key must match the declared field, such as `"shaker"`, or a
child's path, such as `"stage.shaker"`. Every declared device needs a binding.
See [AutoSuite compilation](advanced/autosuite.md#supply-the-binding).

| Code | Cause | Fix |
| --- | --- | --- |
| `missing_resource_binding` | no entry in `devices` for this slot | bind every declared slot ([lesson 1](tutorial/first-function.md)) |
| `device_type` | the entry's profile is not a subtype of the slot's family | bind a profile of the declared family |
| `unknown_resource_binding` | a key that matches no slot | use the field name or component path ([composition](advanced/composition.md)) |

## The shaker cannot start or use a property

Save the speed before `start()` on every path that reaches it. A previous
entry call does not satisfy this compilation check.

For `enabled: Input[bool]`, `speed: Input[RotationalSpeed]` and
`shaker: Agitator`, the following can reach `start()` without a speed:

<!-- correction: configuration wrong -->
```python
if self.enabled:
    self.shaker.speed = self.speed
self.shaker.start()
```

Put the start in the configured branch and explicitly stop in the other branch:

<!-- correction: configuration fixed -->
```python
if self.enabled:
    self.shaker.speed = self.speed
    self.shaker.start()
else:
    self.shaker.stop()
```

A property assignment saves a setting; it does not apply that setting to a
running device until `start()`. Readback and `+=` are not supported.
For differences between device profiles, use
[device-dependent branches](advanced/device-branches.md).

| Code | Cause | Fix |
| --- | --- | --- |
| `device_property_read` | reading `self.shaker.speed` | keep the configured value in a `Var` |
| `device_property_read` | `self.shaker.speed += ...` | assign the new value |
| `device_property` | a misspelled property, or one only a subclass declares | check the family; guard with `comptime.is_device` ([device branches](advanced/device-branches.md)) |
| `unsupported_operation` | a misspelled or foreign command | check the family |
| `operation_binding` | `self.shaker.start(*args)` | list arguments explicitly |
| `operation_binding` | the same argument twice | supply each once |
| `device_condition` | a query with keywords or a different arity | `comptime.is_device(self.shaker, Cls)` |
| `device_condition` | the first argument is not a slot | pass the slot |
| `device_condition` | the second argument is not a class | pass a device class |
| `device_condition` | an unrelated or sibling class | query a subclass of the slot's type |
| `device_condition` | `supports(self.shaker, Agitator.speed)` | pass a command such as `Agitator.start` |
| `device_condition` | a variable or a non-literal | a string literal |
| `device_condition` | a property no compatible type declares | name a declared property |
| `device_capability` | the selected branch writes a property the profile does not list as writable | guard it with `comptime.can_write` ([device branches](advanced/device-branches.md)) |
| `device_capability` | the selected branch calls a command the profile does not support | guard it with `comptime.supports` |
| `device_capability` | `start()` or `stop()` on a profile that does not support it | guard it with `comptime.supports` |
| `device_configuration` | a path reaches `start()` without assigning `speed` | configure the required properties on every path before starting |
| `unsupported_operation` | a statement the package format has no form for | use an operation supported by the selected target, or choose a target that implements it |

## A wait or timer is rejected

Declare `timer: Timer` on the Function and import `Timer` and `s` from `sciloom`.
For `enabled: Input[bool]`, this code waits even when the timer was never started:

<!-- correction: timer wrong -->
```python
if self.enabled:
    self.timer.start()
self.timer.wait_until(5 * s)
```

If the wait should happen only when enabled, put it in the same branch:

<!-- correction: timer fixed -->
```python
if self.enabled:
    self.timer.start()
    self.timer.wait_until(5 * s)
```

If both paths need the wait, start the timer before the condition instead.
Choose the start location to match when elapsed time should begin; moving it
earlier changes the procedure's timing. A start in a previous entry call does
not satisfy the compilation check.

| Code | Cause | Fix |
| --- | --- | --- |
| `timer_not_started` | a path reaches `wait_until` without a start in this entry invocation | start on every path that reaches the wait, or put the wait inside the started branch |
| `wait_type` | a wait receives a plain number or a different physical quantity | supply a Duration, such as `5 * s` |
| `wait_duration` | a negative reference wait, or an AutoSuite literal outside 0–79,999 hours | use a nonnegative duration within the selected target's range |
| `unsupported_runtime_guard` | AutoSuite receives a runtime duration expression | use a fixed duration for the current target, or reference-execute the dynamic procedure until target range checks are verified |
| `unsupported_timer_scope` | starts/resets occupy different native scopes, or a wait is outside its start scope | keep starts/resets together, with waits in the same branch/loop scope or its descendants; preserve the intended start time |
| `timer_operation` | an unsupported Timer command, such as `stop()` | timers support `start()` and `wait_until()`; stop equipment through its own device slot |

For a reference run, `missing_environment_service` means no virtual clock was
supplied; `clock_error` means advancing it would produce an invalid value, such
as overflow. See the [developer execution diagnostics](../developer/troubleshooting.md#executionerror)
and the [timing example](../examples/timing-ir.md) for explicit clock setup.

## A CSV read fails or will not compile

`unsupported_csv_semantics` means AutoSuite's parsing and failure behavior have
not yet been verified against SciLoom's read contract. Changing the file path
does not remove that target limitation. The same procedure can be checked with
an explicit reference file service; see [CSV reads](reference/csv.md).

| Code | Correction |
|---|---|
| `csv_binding` | Unpack every result into distinct, correctly typed fields; include the status for try-forms and a trailing comma for one result |
| `csv_columns`, `csv_metadata` | Use a nonempty fixed tuple of inline Column declarations, scalar types and host Boolean header selection |
| `csv_unit`, `csv_default` | Give quantities a matching unit and typed defaults; every try_read_row column needs a default |
| `csv_index`, `csv_row` | Use nonnegative integer selectors; only row reads have a row argument |
| `csv_path` | Supply nonempty text without NUL; local adapter paths must stay within its root |
| `csv_eof` | Choose an existing data row, remembering that header=True skips the first record |
| `csv_invalid_data` | Correct the file/cell format or declare a cell fallback where the experiment permits it |
| `csv_io_error` | Supply a readable file; column defaults do not recover a file error |

For reference execution, missing files services and invalid service implementations
are described in the [developer diagnostics](../developer/troubleshooting.md#csv-file-services).

## Python raises TypeError or ValueError before compilation

These exceptions report invalid host calls or configuration rather than a
runtime step failing. The message identifies what to change.

| Symptom | Cause and correction |
| --- | --- |
| Calling `program.run()` or `program()` raises `TypeError` | Use `program.compile(target=...)`; the runtime method is source to compile |
| Calling `program.shaker.start()` raises `TypeError` | Put the operation inside `@runtime` |
| Constructing `Timer()` or reading/assigning `program.timer` raises `TypeError` | Declare `timer: Timer` with no value in the class; use its commands only inside `@runtime` |
| Assigning a hardware profile to `program.shaker` raises `TypeError` | Put the profile in `AutoSuiteTarget(devices={...})`; only compatible logical references can be shared between slots |
| Calling a `comptime` query raises `TypeError` | Use it as a complete `if/elif` condition inside `@runtime` |
| A private child name is rejected | Store the child under a public name such as `self.stage` |
| `devices must contain AutoSuiteIndividualShaker records` | Replace another object in the target dictionary with the required profile |
| A binding name is rejected | Use a field name or dotted child path, not an arbitrary label |
| Two devices have the same ID or zone | Bind separate logical devices to separate hardware, or share one logical reference between steps |
| `device_id` is rejected | Supply a positive decimal individual shaker ID; `"0"` is invalid |
| The zone string is rejected | Supply a nonempty single-line name from the installed configuration |
| A speed literal is rejected | Use a finite nonnegative number times `rpm` or `rps`; strings and Booleans are invalid |

The [developer troubleshooting page](../developer/troubleshooting.md) covers
hand-built IR, reference execution and a runnable collection of these failures.
