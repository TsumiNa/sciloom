# Troubleshooting

Contributor-facing errors, grouped by exception type. The author-facing codes,
those a runtime method or a class body can provoke, are on the User Guide's
[troubleshooting](../user-guide/troubleshooting.md) page and are not repeated
here. A diagnostic's fields are described on
[reject a program](tutorial/reject-a-program.md#reading-a-diagnostic).

## Read diagnostic fields

Source and compilation validation errors derive from `DiagnosticError`. A
diagnostic carries a code, message, program path and optional source position.
Ordinary Python construction errors may instead raise `TypeError` or
`ValueError`; they do not have a `diagnostics` attribute.

Save this complete example to a `.py` file. The reported line is relative to
the code below; adding lines before the class changes it.

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

## TypeError at host time

| Message | What it proves | Fix |
|---|---|---|
| Device property reads are not supported yet. | a getter was executed from host Python | never read a device property; the getter exists only to declare the type |
| Concrete device profiles must explicitly declare `<list>`. | a profile omits `writable_properties`, `required_configuration` or `supported_operations` | declare all three as `ClassVar` tuples on the profile |
| writable_properties must list declared property names. | a name the family never declared | list declared properties only |
| supported_operations must list registered command methods. | a plain method, or a property, in the list | list methods decorated with `@operation` |
| resolve_devices must return DeviceBindings. | the target returned something else | return `DeviceBindings(devices=(...))` |
| DeviceBinding requires a trusted DeviceTypeContract. | a binding built from something other than a contract | build bindings with `bind_device` |
| DeviceBindings requires DeviceBinding records. | the envelope contains other objects | pass `DeviceBinding` records only |
| Composed Function names must be public Python identifiers. | a child stored under a private attribute | a public attribute name |

## ValueError from bindings

Raised while a `DeviceBinding` or `DeviceBindings` is built, before compilation.

| Message | What it proves | Fix |
|---|---|---|
| Device binding identities must be nonempty strings. | an empty `logical_id` or `physical_id` | give both a value |
| Device type identities must be namespaced and versioned. | a `device_type_id` such as `heater` | `example.heater/v1` |
| base_contracts must provide the complete trusted ancestor directory. | an ancestor missing from the binding | let `bind_device` build the binding |
| Invalid trusted device directory: ... | the ancestor contracts do not validate | fix the declaration the message names |
| `<list>` must identify distinct declared device members. | a duplicate or undeclared member in a capability list | list each declared member once |
| Required device configuration must be writable. | a property in `required_configuration` but not in `writable_properties` | make it writable or drop the requirement |
| Duplicate device binding `<field>`. | two bindings share a logical or physical id | one binding per resource and per instrument |
| Conflicting trusted device contracts across bindings. | two bindings describe one type id differently | one contract per type id |

## IRValidationError

Raised by `validate`, by the JSON codec and by `compile_ir` before any target
runs. Codes an author can provoke are on the User Guide page; these arise from
hand-built or edited programs and from device declarations.

| Code | Message | Cause |
|---|---|---|
| `device_contract` | A device type identifier has conflicting declarations. | two classes declare one `device_type_id` differently |
| `device_contract` | Device query must name a declared type. | a hand-built `IsDevice` naming an unknown type |
| `device_property` | Property must have a declared signature for this device category. | a `ConfigureProperty` for a property the directory does not declare |
| `device_command` | Command arguments must match its declared signature. | wrong arity or types on a `DeviceCommand` |
| `device_command` | Built-in agitation commands require their dedicated semantic nodes. | agitation start or stop emitted as a `DeviceCommand` |
| `device_type` | Agitation lifecycle requires an Agitator resource. | `StartAgitation` on a non-agitator resource |
| `unknown_resource` | Operation must reference a declared device. | a resource id with no `DeviceResource` |
| `format_version` | Only semantic format version 4 is supported. | an older or missing version; nothing is upgraded silently |
| `json_shape` | A package must declare format_version. / Document is cyclic or nested too deeply. | a malformed document |
| `json_syntax` | Invalid JSON: ... / Duplicate object key ... / Nonstandard JSON constant ... | syntax, duplicate keys, `NaN` or `Infinity` |
| `empty_id`, `duplicate_id` | Semantic IDs must not be empty. / ID ... already occurs at ... | node ids are required and unique; they are never generated on import |
| `source_span` | Source needs a path, line >= 1 and column >= 0. | an invalid span |
| `resource_identity` | Logical resource IDs must be nonempty and unique. | two resources with one logical id |
| `entry_function`, `unknown_function` | Entry must reference a function in this package. / Unknown function ... | a dangling function id |
| `unknown_symbol`, `symbol_scope` | Unknown variable ... / Variable belongs to a different function; globals are not implicit. | a reference across function ownership |
| `variable_owner`, `variable_name`, `empty_name` | ownership and naming rules for hand-built functions | match owner ids; unique non-empty names |
| `initializer_role`, `initializer_literal`, `missing_initializer` | internal variables need a literal initializer; only internal variables have one | add or remove the initializer |
| `literal_type` | Value does not represent `<type>`. | a literal whose value and declared type disagree |

## CompilationError

Raised by `compile_ir` after validation: by the binding check, the capability
and configuration pass, and `Target.validate`.

| Code | Message | Cause |
|---|---|---|
| `missing_resource_binding` | No compatible binding for device `<slot>`. | the target returned no binding for a declared resource |
| `device_type` | No compatible binding for device `<slot>`. | the binding's profile is not a subtype of the resource's declared type |
| `unknown_resource_binding` | Device binding `<name>` has no declared resource. | a binding the program did not ask for |
| `device_contract` | Serialized device contract differs from the target's trusted contract. | the program's directory disagrees with the binding |
| `device_contract` | Selected property query differs from the trusted signature. / Selected command query differs from the trusted signature. | a `CanWrite` or `SupportsOperation` query whose signature is not the profile's |
| `device_capability` | The bound device does not implement this writable property contract. / ... this command contract. / ... does not support this lifecycle operation. | the selected program uses a member the profile does not list |
| `device_configuration` | start() requires `<property>` to be configured on every reachable path in this invocation. | a `StartAgitation` reachable without its required writes |
| your own code | your own message | whatever your `validate` proves; keep the code stable and the message actionable |

## ValueError from ExecutionConfig

Raised when the interpreter's configuration is constructed, before any run.

| Message | What it proves | Fix |
|---|---|---|
| max_steps must be a positive integer. | a non-positive step budget | a positive integer |
| max_call_depth must be an integer between 1 and 100. | a depth outside the range | stay within 1 to 100 |

## ExecutionError

Raised by the reference interpreter during a run.

| Code | Message | Cause |
|---|---|---|
| `unspecialized_device_condition` | Specialize device conditions before reference execution. | a `DeviceIf` still in the program; use `result.specialized_ir` |
| `unsupported_operation` | Cannot execute DeviceCommand. | a native command; see [native commands](advanced/native-commands.md) |
| `input_binding` | Supply exactly the entry function's named inputs. | a missing or extra input |
| `runtime_type` | Expected `<type>`, received ... / A rotational-speed input requires a quantity such as 600 * rpm. / A quantity cannot be passed to a scalar input. | an input of the wrong Python type |
| `uninitialized_read` | Variable `<name>` has no value in this call. | an input or output read before it was bound |
| `missing_output` | Output `<name>` was not assigned in this call. | a path that skips an output |
| `index_type`, `index_bounds` | List indices must be integers, excluding bool. / Index ... is outside a list of length ... | an invalid index at run time |
| `numeric_error` | Arithmetic produced a nonfinite value. / Nonfinite real value. | overflow, division by zero |
| `invalid_speed` | Rotational speed must be nonnegative. | a negative speed at run time |
| `device_configuration` | start() requires complete saved configuration. | `start` before every required property was saved |
| `step_limit`, `call_depth`, `execution_depth` | Reference execution exhausted its step budget. / ... exceeded its call-depth budget. / Reference evaluation exceeded the host nesting limit. | a budget in `ExecutionConfig` was exhausted |


## Reproduce author-facing failures

This complete script keeps the examples from the author lessons and advanced
guides executable in one place. It prints only each diagnostic code; the
[User Guide](../user-guide/troubleshooting.md) shows corrections by symptom.

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


class Limits(Function):
    """A host list cannot enter a runtime expression.

    Attributes:
        volume: Sample volume in millilitres.
        small: Whether the volume is below the first limit.
    """

    volume: Input[float]
    small: Output[bool]

    def __init__(self) -> None:
        self.limits = [1.0, 5.0]

    @runtime
    def run(self) -> None:
        self.small = self.volume < self.limits


class Both(Function):
    """A condition AutoSuite refuses.

    Attributes:
        a: First flag.
        b: Second flag.
        both: Whether both flags are set.
    """

    a: Input[bool]
    b: Input[bool]
    both: Output[bool]

    @runtime
    def run(self) -> None:
        self.both = self.a and self.b



for action in (
    lambda: Counter().count,
    lambda: BareSpeed().compile(target=AutoSuiteTarget()),
    lambda: ForLoop().compile(target=AutoSuiteTarget()),
    lambda: UnboundShaker().compile(target=AutoSuiteTarget()),
    lambda: Limits().compile(target=AutoSuiteTarget()),
    lambda: Both().compile(target=AutoSuiteTarget()),
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
host_value
unsupported_short_circuit
```
