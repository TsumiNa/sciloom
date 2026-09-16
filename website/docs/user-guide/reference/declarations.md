# Declarations

Use these declarations in the class body. Import the authoring names from
`sciloom`; import `AutoSuiteTarget` and its hardware profiles from
`sciloom_autosuite`.

## Fields

| Declaration | Meaning | Initial value |
| --- | --- | --- |
| `volume: Input[float]` | Caller supplies a value on every call | Not allowed |
| `speed: Output[RotationalSpeed]` | Result returned to the caller; assign on every path | Not allowed |
| `index: Var[int] = 0` | Working value or persistent state; reset explicitly when needed | Required |
| `batch_size: int = 8` | Ordinary Python configuration; a supported scalar becomes a fixed value in the generated procedure | Ordinary Python rules |
| `shaker: Agitator` | Logical device dependency, bound to hardware through the target | No class-level value |
| `timer: Timer` | Elapsed-time reference owned by this Function | No class-level value; call `start()` during execution |

[Lesson 2](../tutorial/inputs-and-units.md) introduces inputs;
[lesson 3](../tutorial/agitator.md) introduces outputs and working values;
[lesson 5](../tutorial/compile.md) explains persistent state.

Each runtime field has exactly one role: `Input[T]`, `Output[T]` or
`Var[T]`. Supply a supported [value type](runtime-language.md#values).
Bare `Var`, nested roles and untyped lists are invalid.

A `Var` initial value is evaluated when Python creates the class, then checked
against the declared type. For example, `speed: Var[RotationalSpeed] = 300 * rpm`
is valid. A list initial value must be a Python list; SciLoom copies it so later
changes to the original cannot change the declaration. Each instance starts
with independent state. Initial values do not reset fields on later calls.

Inherited declarations remain available. Do not change an inherited field's
role, type or initial value, or replace an inherited device slot with another
attribute. Timer slots also retain their role on inheritance. Use public names that do not conflict with Function methods such as
`compile`.

## The runtime method

| Rule | Detail |
| --- | --- |
| Exactly one method marked `@runtime` | It may be inherited |
| Signature such as `def run(self) -> None` | Only `self`; declare inputs as fields |
| Source in an ordinary `.py` file | No notebook, REPL, `exec()` or asynchronous runtime method |
| Compiled from source | The method body is not executed during compilation |
| Runtime values used inside the method | Host Python cannot read or assign `Input`, `Output` or `Var` values |

Calling `instance.run()` or `instance()` in your Python script raises
`TypeError`. Generate a program with `instance.compile(target=...)`.
Child Function calls belong inside the runtime method.

## The constructor

Python calls `__init__` when an instance is created. Use it to store fixed
settings, create child Functions and share existing logical device references:

`self.stage.shaker = self.shaker` lets the child use the parent's shaker.
Do not assign hardware profiles or runtime field values there.
Timers cannot be assigned or shared between Functions; elapsed time is common
to the procedure, but each timer belongs to its declaring Function.
See [shared devices](../advanced/composition.md) and
[constructor settings](../advanced/specialization.md).

## Docstrings

Describe the procedure in an English class docstring. Use `Attributes:` to
explain its fields and `Args:` for constructor parameters. These descriptions
help readers and tools; they do not determine execution.
