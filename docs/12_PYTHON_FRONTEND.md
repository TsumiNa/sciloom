# Python Function frontend

Device annotations such as `agitator: Agitator` form a separate dependency schema.
`self.agitator.speed = value` lowers to ConfigureProperty; explicit `start()` and
`stop()` lower to lifecycle nodes. Reads and augmented property writes are rejected.
See [device semantics](15_AGITATION_SEMANTICS.md). The DSL never invokes declared
property or command bodies while translating source.

`Function` classes declare runtime schema before instantiation. Calling
`instance.to_ir()` reads registered runtime source and instance configuration,
then returns a validated `sciloom.core.ir.Program`. `instance.compile(target=...)` additionally
emits the selected target's artifact. AutoSuiteTarget emits ASFP; see the
[compiler guide](13_ASFP_COMPILER.md).

Implementation ownership: `dsl/model.py` handles Function lifecycle and logical
components; `dsl/schema.py` handles declarations and descriptors. `lowering.py`
builds the instance graph using `context.py` for symbols/source identity,
`source.py` for file discovery, `expressions.py` for expression conversion and
`statements.py` for calls, domain operations and structured control flow.

See the runnable [function-call example](../examples/function_call.py):

```bash
uv run python examples/function_call.py
```

## Declarations and specialization

Host instance construction and device selection are distinct stages. Runtime
if/elif conditions can use the restricted `comptime` queries imported from
`sciloom`; `.to_ir()` preserves both branches until a target binding is supplied.

```python
from sciloom import comptime
from examples.developer.demo_contribution import DemoAgitator

# Inside a @runtime method with an Agitator slot:
if comptime.is_device(self.agitator, DemoAgitator):
    self.agitator.gain = 0.5
self.agitator.speed = self.speed
self.agitator.start()
```

This sequence is runnable in the [portable example](../examples/developer/portable_agitation.py).
`is_device` narrows the true branch's device interface. `can_write(device, "name")`
and `supports(device, DeviceType.command)` query explicit capabilities without
narrowing. A literal property name must resolve unambiguously in compatible device
declarations in scope. Queries take two positional arguments and appear only as
whole if/elif conditions; combine them using nesting. Getters, arbitrary host
queries, boolean query expressions and runtime-dependent type selection remain
unsupported. All branches must pass source/type validation, including branches
that a particular target will discard.

Import `Function`, `Input`, `Output`, `Var` and `runtime` from `sciloom`. Use native
`int`, `float`, `bool`, `RotationalSpeed`, or one-dimensional `list[T]` of those
types as value types. Real/Integer/Boolean
markers have been removed. Declare inputs and outputs as `Input[T]` and
`Output[T]` without defaults. Declare internal state as `name: Var[T] = literal`;
the initial value persists across calls, with explicit runtime assignment for
resets. Unwrapped annotations such as `limit: int = 3` or a plain physical type
are host-time configuration. `Class.model_fields` exposes immutable RuntimeField
records; these implementation records belong to `dsl.schema`.

Input/Output/Var are Annotated aliases: ordinary type checkers see the native
value type, while SciLoom resolves annotations with `include_extras=True` to keep
the role. Exactly one direct role is required. Bare aliases, nested roles,
missing Var initializers and unsupported types fail during class construction.
List declarations, source conversion and AutoSuite array emission are implemented; see the [implementation contract](refactor/package-layout/00-overview.md).

`__init__` is normal Python. It can assign scalar configuration and compose child
Function instances. Runtime fields cannot be read or written as host Python; they
are used by source lowering. Inherited schema/runtime methods are supported,
but changing inherited runtime field declarations is rejected in this subset.
Specialize ordinary Python configuration instead.

## Function documentation

Describe the purpose in the class docstring, followed by an Attributes section
whose names match runtime fields. Constructor Args explain host configuration;
types already come from annotations. See Identity/Caller in
[function_call.py](../examples/function_call.py) and ConfigureAgitation in
[agitation.py](../examples/agitation.py). These conventions prepare help text for
AI and future Studio; no description extractor or node registry is implemented.
Docstrings never determine execution rules or replace semantic validation.

`uv run mypy` checks the production package and runnable examples. Annotated
field aliases retain native types, and `runtime` retains the method signature.
See [typing scope and limits](16_TYPING.md); schema, source-subset and device
rules remain SciLoom validation responsibilities.

## Runtime lists

Declare inputs/outputs with `Input[list[T]]` / `Output[list[T]]`, or persistent
state with `Var[list[T]] = [...]`. Schema construction copies and freezes list
defaults; subsequent mutation of the original Python initializer cannot change
the class schema. Different composed Function instances and interpreter sessions
have independent state, while repeated calls to one instance retain state.

The source subset supports list literals, whole assignment, Function I/O, builtin
`len`, indexed reads, indexed writes and augmented indexed assignment. `if` and
`while` combine these operations without lowering list intent to vendor tasks.
Empty literals need a declared element context, such as assignment to a list field
or a typed call argument. Nonempty literals can infer a homogeneous type, including
numeric widening; list variables themselves are invariant in their element type.

Assignment and function transfer use value semantics. Indices are nonnegative
integers excluding bool; negative/out-of-range reads and writes are execution
errors, with no automatic growth. Python slicing, comprehensions, iteration,
append/pop/remove/clear and indexed Function output bindings remain unsupported.
Shadowing builtin `len` is rejected rather than silently changing its meaning.
The complete [ScaleValues example](../examples/scale_values.py) compiles to ASFP.
AutoSuite requires whole-list output assignment on every return path and before
reads (`list_output_initialization`); initialize outputs before potentially empty
loops. See [array mapping evidence](../autosuite/docs/17_ARRAY_MAPPING.md).

## Runtime source subset

Each Function has exactly one synchronous `@runtime` instance method taking only
`self`. The compiler reads its ordinary `.py` module with its declared source
encoding, locates the method by name and source line, and lowers Python AST. A
direct call to the decorated method raises an error instead of executing tasks.
Unavailable, dynamic and asynchronous source is rejected. Source files must remain
available and correspond to the loaded class definitions during compilation.

Supported runtime syntax:

- `self.field` reads and writes for statically declared runtime fields;
- scalar Python literals and scalar host configuration via `self.attr`;
- arithmetic `+`, `-`, `*`, `/`, unary signs, individual comparisons, `not`, `and`, `or`;
- assignment, augmented assignment, `if/elif/else` and `while` without loop `else`;
- calls to composed `self.child(...)` Function instances using positional/keyword
  inputs; all inputs must be supplied exactly once;
- a single assignment destination for one output, or tuple destinations in declared
  order for multiple outputs; standalone calls require a function with no outputs;
- `pass` and non-executing string statements such as docstrings.

A call is a statement, not an expression nested inside arithmetic. Python local
temporaries, arbitrary helper calls, attribute chains, properties, module-global
lookups, chained comparisons, loops with `break`/`continue`, `for`, `return`, multidimensional arrays,
units other than the supported rotational-speed quantities, and exception handling are outside this subset. Unsupported forms fail with
source-located diagnostics. Reading a property never executes its getter during lowering.

## Identity and compilation boundaries

One instance maps to one function ID per package, including shared child instances.
Distinct instances of the same class remain separate specializations. Child
functions are discovered in runtime source order; unused components are omitted.
IDs are deterministic for repeated lowering of an unchanged instance graph/source,
but are not promised stable across source edits or component reordering. Cycles in
the function call graph are representable in IR; AutoSuiteTarget rejects recursion.

Global binding, Application and event APIs remain deferred. The first supported
domain operation is [agitation](15_AGITATION_SEMANTICS.md). The proposed
examples directory illustrates that broader design; only the subset documented
here is currently executable. `.compile()` and ASFP writing use the same lowering.

See the [execution contract](14_REFERENCE_EXECUTION.md) for independent IR
semantics. AND/OR lower into short-circuit IR; AutoSuite currently rejects these
operators until an equivalent target lowering is verified. Use explicit If
statements when compiling to that target.
