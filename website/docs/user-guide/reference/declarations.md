# Declarations

Rules for the class body of a Function. Each row links to the page that explains
it.

## Fields

| Declaration | Meaning | Default | Explained on |
|---|---|---|---|
| `volume: Input[float]` | value supplied by the caller at each call | not allowed | [lesson 3](../tutorial/agitator.md) |
| `speed: Output[RotationalSpeed]` | value written back when the call returns; assigned on every path | not allowed | [lesson 3](../tutorial/agitator.md) |
| `index: Var[int] = 0` | persistent state of the instance; the literal is the initial state, not a per-call reset | required literal | [lesson 5](../tutorial/compile.md) |
| `batch_size: int = 8` | host-time configuration, embedded as a literal when read in the runtime method | ordinary Python | [host-time specialization](../advanced/specialization.md) |
| `shaker: Agitator` | logical device slot; the target binds the hardware | none; no class-level value | [lesson 1](../tutorial/first-function.md) |

Import `Function`, `Input`, `Output`, `Var`, `runtime`, `Agitator`,
`RotationalSpeed`, `rpm`, `rps` and `comptime` from `sciloom`. A field has
exactly one role; a bare `Annotated` alias or a nested role is refused. A list
`Var` needs a list literal, which is copied and frozen when the class is built.
Inherited runtime fields and methods work; redeclaring an inherited field, or
shadowing an inherited device slot, is refused. A field name must not collide
with the Function API.

## The runtime method

| Rule | Detail |
|---|---|
| exactly one `@runtime` method | a class with none or two is refused |
| signature `def run(self) -> None` | no other parameters; inputs are fields |
| source on disk | an ordinary `.py` file; notebook cells, `exec()` and `async def` are refused |
| never executed by host Python | calling it, or an instance, raises `TypeError` |
| runtime fields are sealed | host reads and writes are refused (`runtime_field_read`, `runtime_field_write`) |

## The constructor

`__init__` is ordinary Python. It stores host configuration and child Function
instances as attributes, and may share a device slot with a child
(`self.stage.shaker = self.shaker`). It must not assign a runtime field. See
[composition](../advanced/composition.md).

## Docstrings

Write an English class docstring describing the procedure, with an `Attributes:`
section naming the declared fields and an `Args:` section for constructor
parameters. Docstrings inform readers and tools; they never change what compiles.
