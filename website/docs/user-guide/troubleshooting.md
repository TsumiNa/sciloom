# Troubleshooting

<!-- Error demonstrations formerly embedded in the introductory lessons are
kept executable here. The main tutorial follows successful programs. -->

Every SciLoom error carries structured diagnostics: a machine-readable code, a
message, a path into the program and, when the source is known, the line that
caused it. Printing the error shows `path: message [code]` per diagnostic. To
read the fields, catch the base class every SciLoom error derives from:

```python
from sciloom import Function, Output, RotationalSpeed, runtime
from sciloom.core.diagnostics import DiagnosticError
from sciloom_autosuite import AutoSuiteTarget


class BareNumber(Function):
    """Assign a number where a speed is declared.

    Attributes:
        speed: A rotational speed.
    """

    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.speed = 600


try:
    BareNumber().compile(target=AutoSuiteTarget())
except DiagnosticError as error:
    for diagnostic in error.diagnostics:
        print(diagnostic.code)
        print(diagnostic.message)
        print(diagnostic.path)
        print(diagnostic.source.line if diagnostic.source else "no source position")
```
```text
type_mismatch
Cannot assign integer to rotational_speed.
$.functions[0].body[0]
17
```

Fix the declaration or the statement the diagnostic points at; never edit the
generated package. The tables below are grouped by when the error fires.

## When the class is created

Raised as soon as Python executes the `class` statement.

| Code | Message | Cause | Fix |
|---|---|---|---|
| `class_schema` | Runtime fields require one direct Input[T], Output[T] or Var[T] role. | a bare alias, or a nested role | declare exactly one role ([declarations](reference/declarations.md)) |
| `class_schema` | Input, Output and Var require int, float, bool, RotationalSpeed or a typed list of those values. | an unsupported value type | use one of the four types or a list of one ([runtime language](reference/runtime-language.md)) |
| `class_schema` | Lists require one supported scalar element type; Any and nested lists are unsupported. | `list`, `list[Any]`, `list[list[...]]` | a one-dimensional typed list |
| `class_schema` | Var requires an explicit scalar literal initial value. | a `Var` without `= literal` | add the literal ([lesson 5](tutorial/compile.md)) |
| `class_schema` | Var requires an explicit list initial value. | a list `Var` without a list literal | add `= []` or a literal list |
| `class_schema` | Default must be a finite `<type>` value. | a literal of the wrong type, `Var[int] = 1.5` | match the declared type |
| `class_schema` | Parameter defaults are outside the first frontend subset. | `Input` or `Output` with `= value` | remove the default; pass the value or embed host configuration ([specialization](advanced/specialization.md)) |
| `class_schema` | Overriding runtime schema is unsupported; specialize host-time configuration instead. | redeclaring an inherited field | keep the base declaration |
| `class_schema` | Runtime field name conflicts with the model API. | a field named like a Function method | rename the field |
| `class_schema` | Device slot `<name>` cannot have a class-level value. | `shaker: Agitator = ...` | bind hardware through the target ([lesson 1](tutorial/first-function.md)) |
| `class_schema` | Invalid or conflicting device slot name `<name>`. | a private or reserved slot name | a public identifier |
| `class_schema` | Inherited device slot `<name>` cannot be shadowed. | redeclaring a base class slot | keep the base slot |

## When host Python touches a runtime field

Raised when host code reads or assigns a runtime field on an instance, for
example in `__init__` or in a script.

| Code | Message | Cause | Fix |
|---|---|---|---|
| `runtime_field_read` | Runtime fields cannot be read by host Python. | `instance.field` in host code | read it only inside the runtime method ([lesson 5](tutorial/compile.md)) |
| `runtime_field_write` | Instance configuration shadows runtime field `<name>`. | assigning a runtime field in `__init__` | store host configuration under another name ([specialization](advanced/specialization.md)) |

## When the source is read

Raised by `compile` (or `to_ir`) while the runtime method's source is analysed.
The path names the function, `$.python.fn:0`.

| Code | Message | Cause | Fix |
|---|---|---|---|
| `runtime_method` | A Function requires exactly one @runtime instance method. | none or two `@runtime` methods | keep one |
| `source_unavailable` | Runtime source must come from an ordinary .py file. | a notebook cell, `exec()`, `async def` | move the class to a `.py` file |
| `python_subset` | Unsupported runtime statement: `<Node>`. | `For`, `Return`, `Try`, `Break`, ... | see the [runtime language](reference/runtime-language.md); loops use `while` ([lesson 4](tutorial/lists-and-loops.md)) |
| `python_subset` | Unsupported runtime expression: `<Node>`. | a chained comparison, a string, a call, an attribute chain | one comparison at a time; fields, not helpers |
| `python_subset` | Runtime methods take only self; declare Input fields on the class. | parameters on the runtime method | declare `Input` fields ([tutorial 2](tutorial/inputs-and-units.md)) |
| `python_subset` | Only calls to composed self.<function> instances are supported. | calling a helper or a function that is not an attribute | create the child in `__init__` ([composition](advanced/composition.md)) |
| `python_subset` | Runtime calls require a Function instance composed before compilation. | the attribute is not a Function instance | assign a Function instance in `__init__` |
| `python_subset` | List slicing is unsupported. | `self.items[1:]` | index in a loop |
| `python_subset` | len requires one positional list argument. | `len()` of a scalar or with keywords | `len(self.items)` |
| `python_subset` | len must resolve to the Python builtin; shadowed calls are unsupported. | a module-level name `len` | remove the shadowing name |
| `runtime_field` | Assignment targets must be declared self.<runtime_field> references. | a local variable or an undeclared field | declare a `Var` |
| `call_binding` | Call arity or assigned output count does not match the callee schema. | wrong number of arguments or destinations | match the child's inputs and outputs |
| `call_binding` | Unknown, duplicate or unpacked input argument. | a misspelled or repeated keyword, `*args` | name each input once |
| `call_binding` | Every callee input must be bound exactly once. | a missing input | supply it |
| `call_binding` | Function outputs must bind to whole variables, not indexed elements. | `self.items[0] = self.child()` | bind to a field, then write the element |
| `list_type` | An empty list needs a declared list element type. | `[]` assigned to something untyped | assign to a declared list field |
| `list_type` | Lists must be one-dimensional and homogeneous. | mixed or nested literal | one element type |
| `list_type` | Indexed assignment requires a declared list variable. | `self.x[0] = ...` on a scalar | declare a list field |
| `quantity_literal` | Unit literals require a host numeric value; use Input[RotationalSpeed] for runtime inputs. | `self.value * rpm` | take a speed input, or a host number times a unit |
| `host_value` | Only scalar bool/int/float host values can enter runtime expressions. | a host list, string or object read through `self` | embed scalars only ([specialization](advanced/specialization.md)) |
| `device_property_read` | Device getters are not supported; use a runtime variable for the configured value. | reading `self.shaker.speed` | keep the configured value in a `Var` |
| `device_property_read` | Device properties only support plain assignment. | `self.shaker.speed += ...` | assign the new value |
| `device_property` | Device property `<name>` is not declared. | a misspelled property, or one only a subclass declares | check the family; guard with `comptime.is_device` ([device branches](advanced/device-branches.md)) |
| `unsupported_operation` | Device command `<name>` is not declared. | a misspelled or foreign command | check the family |
| `operation_binding` | Device calls do not support argument unpacking. | `self.shaker.start(*args)` | list arguments explicitly |
| `operation_binding` | Duplicate device command argument. | the same argument twice | supply each once |
| `device_condition` | Device queries require two positional arguments. | a query with keywords or a different arity | `comptime.is_device(self.shaker, Cls)` |
| `device_condition` | Device queries require a declared self.<device> slot. | the first argument is not a slot | pass the slot |
| `device_condition` | is_device requires a declared device class. | the second argument is not a class | pass a device class |
| `device_condition` | is_device requires a type on the current device interface's inheritance chain. | an unrelated or sibling class | query a subclass of the slot's type |
| `device_condition` | supports accepts commands, not properties or getters. | `supports(self.shaker, Agitator.speed)` | pass a command such as `Agitator.start` |
| `device_condition` | can_write requires a declared property name as a string literal. | a variable or a non-literal | a string literal |
| `device_condition` | can_write needs one unambiguous property declared by a compatible device type in scope. | a property no compatible type declares | name a declared property |
| `device_reference` | Shared device owner must belong to this Function composition. | sharing a slot from an unrelated instance | share within the parent's own children |

## When the program is checked

Raised by `compile` after the source is read, on the typed program. The path
names the statement, `$.functions[0].body[2]`.

| Code | Message | Cause | Fix |
|---|---|---|---|
| `type_mismatch` | Cannot assign `<source>` to `<target>`. | `integer` to `rotational_speed`, `real` to `integer` | use the declared type ([tutorial 2](tutorial/inputs-and-units.md)) |
| `operator_type` | Operator `<op>` cannot combine `<left>` and `<right>`. | arithmetic on a Boolean, a comparison of a speed with a number | compare like with like |
| `operator_type` | Lists do not support implicit arithmetic, comparisons or truthiness. | `self.a == self.b` on lists | compare elements in a loop |
| `condition_type` | Control-flow conditions must be boolean. | `if self.count:` | `if self.count > 0:` |
| `index_type` | List indices must be integers, excluding bool. | a float or Boolean index | an integer `Var` |
| `list_element_type` | Expected `<type>` elements. | a literal with the wrong element type | match the list's element type |
| `call_binding` | Missing `<inputs or outputs>`: ... | an unbound input or output | bind every declared input and output |

## When the target compiles it

Raised by `compile` for the selected target; the path names a resource or a
statement.

| Code | Message | Cause | Fix |
|---|---|---|---|
| `missing_resource_binding` | No compatible binding for device `<slot>`. | no entry in `devices` for this slot | bind every declared slot ([lesson 1](tutorial/first-function.md)) |
| `device_type` | No compatible binding for device `<slot>`. | the entry's profile is not a subtype of the slot's family | bind a profile of the declared family |
| `unknown_resource_binding` | Device binding `<name>` has no declared resource. | a key that matches no slot | use the field name or component path ([composition](advanced/composition.md)) |
| `device_capability` | The bound device does not implement this writable property contract. | the selected branch writes a property the profile does not list as writable | guard it with `comptime.can_write` ([device branches](advanced/device-branches.md)) |
| `device_capability` | The bound device does not implement this command contract. | the selected branch calls a command the profile does not support | guard it with `comptime.supports` |
| `device_capability` | The bound device does not support this lifecycle operation. | `start()` or `stop()` on a profile that does not support it | guard it with `comptime.supports` |
| `device_configuration` | start() requires `<property>` to be configured on every reachable path in this invocation. | a path reaches `start()` without assigning `speed` | assign the speed on every path first ([lesson 2](tutorial/inputs-and-units.md)) |
| `unsupported_short_circuit` | AutoSuite short-circuit equivalence is unverified; lower to explicit If statements. | `and` / `or` | nested `if` ([AutoSuite rules](advanced/autosuite.md)) |
| `recursive_call` | AutoSuite does not support recursive calls. | a Function calling itself, directly or indirectly | a loop |
| `list_output_initialization` | AutoSuite requires whole-list output assignment on every return path. | a list output first written inside a loop or a branch | assign the whole list first |
| `unsupported_operation` | AutoSuite cannot emit `<Statement>`. | a statement the package format has no form for | a supported operation |

## Errors raised at host time

These are ordinary Python exceptions, not diagnostics.

| Exception | Message | Cause |
|---|---|---|
| `TypeError` | SciLoom runtime methods must be compiled, not executed as Python. | calling `instance.run()` |
| `TypeError` | Function calls in @runtime methods are compiled, not executed as Python. | calling `instance()` from host code |
| `TypeError` | Device operations belong in compiled @runtime methods. | `instance.shaker.start()` from host code |
| `TypeError` | Device slot `<name>` requires a compatible logical device reference; bind hardware through Target. | assigning a profile or another object to a slot |
| `TypeError` | comptime queries belong in compiled if/elif conditions. | calling a query from host code |
| `TypeError` | Composed Function names must be public Python identifiers. | a child stored under a `_private` attribute |
| `TypeError` | devices must contain AutoSuiteIndividualShaker records. | another object in `devices` |
| `ValueError` | Device binding names must be logical field/component paths. | a key that is not a dotted identifier |
| `ValueError` | Distinct resources cannot alias shaker device `<id>`. | two slots with the same `device_id` |
| `ValueError` | Distinct resources cannot bind the same AutoSuite zone `<zone>`. | two slots with the same `zone` |
| `ValueError` | device_id must be the positive decimal ID of an individual shaker. | `device_id="0"` or a non-numeric id |
| `ValueError` | ... must be a nonempty single-line string. | an empty or multi-line zone |
| `ValueError` | Rotational speed must be finite and nonnegative. | a negative or infinite speed |
| `TypeError` | A speed literal requires a number, not bool or text. | `"600" * rpm` |

Codes that arise only from hand-built programs or reference execution are
covered by the Developer Guide.

## Try common failures

Save this complete example to a `.py` file to reproduce four errors. Use the
codes to find the cause and correction in the tables above.

<!-- example: failures -->
```python
from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Var, runtime
from sciloom.core.diagnostics import DiagnosticError
from sciloom_autosuite import AutoSuiteTarget


class Counter(Function):
    """Count calls with a runtime field."""
    count: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.count += 1


class BareSpeed(Function):
    """Demonstrate a missing speed unit."""
    speed: Output[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.speed = 600


class ForLoop(Function):
    """Demonstrate unsupported iteration syntax."""
    values: Input[list[float]]
    total: Output[float]

    @runtime
    def run(self) -> None:
        self.total = 0.0
        for value in self.values:
            self.total += value


class UnboundShaker(Function):
    """Declare a shaker that still needs a target binding."""
    shaker: Agitator

    @runtime
    def run(self) -> None:
        self.shaker.stop()


for action in (
    lambda: Counter().count,
    lambda: BareSpeed().compile(target=AutoSuiteTarget()),
    lambda: ForLoop().compile(target=AutoSuiteTarget()),
    lambda: UnboundShaker().compile(target=AutoSuiteTarget()),
):
    try:
        action()
    except DiagnosticError as error:
        print(error.diagnostics[0].code)
```
```text
runtime_field_read
type_mismatch
python_subset
missing_resource_binding
```
