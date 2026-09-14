# Runtime language

What a `@runtime` method may contain. SciLoom reads the source and accepts a
restricted subset of Python; the first construct outside it is named in a
diagnostic.

## Values

| Type | Notes |
|---|---|
| `int`, `float` | an integer widens to a float where needed; a float never narrows |
| `bool` | its own type; not an integer, not an index, the only valid condition |
| `RotationalSpeed` | written `600 * rpm` or `10 * rps` from a host number; canonical unit is revolutions per second; the only physical quantity in this release |
| `list[T]` | one-dimensional, homogeneous, `T` one of the four above |

There is no implicit truthiness: a condition is a Boolean expression, not a
number or a list. Lists have no arithmetic, comparison or truthiness of their own.

## Expressions

| Supported | Not supported |
|---|---|
| literals; `self.<field>`; a host scalar through `self` | local names, module globals, attribute chains |
| `+ - * /` (division yields `float`); unary `+ - not` | `** % //`, bitwise operators |
| one comparison `== != < <= > >=` | chained comparisons, `in`, `is` |
| `and`, `or` (refused by AutoSuite; see [AutoSuite rules](../advanced/autosuite.md)) | conditional expressions |
| `[a, b]`, `self.items[i]`, `len(self.items)` | slicing, comprehensions, list methods, any other call |
| `300 * rpm` with a host number | a unit applied to a runtime value; use `Input[RotationalSpeed]` |

## Statements

| Supported | Not supported |
|---|---|
| `self.x = expr`, `self.x += expr` and the other augmented forms | assignment to anything but a declared field |
| `self.items[i] = expr`, `self.items[i] += expr` | writes that extend a list |
| `if` / `elif` / `else` | conditional expressions |
| `while cond:` | `for`, `break`, `continue`, `while ... else` |
| `self.x = self.child(...)`, `self.a, self.b = self.child(...)`, `self.child()` | calls nested in expressions, helper functions |
| `self.shaker.speed = expr`; `self.shaker.start()` | reading a device property; `+=` on one |
| `if comptime.is_device(...)`, `can_write`, `supports` as the whole condition | queries combined with `and`, or with runtime arguments |
| `pass`, docstrings | `return`, `try`, `with`, `assert`, `del`, nested `def` |

Lists are values: assignment copies, and a call copies inputs in and outputs
out. Indices are non-negative integers; negative or out-of-range access is an
execution error, and a write never grows a list. An empty literal needs a
declared element type. Explained in [tutorial 3](../tutorial/lists-and-loops.md).

## Calls

| Form | Rule |
|---|---|
| inputs | positional or keyword, each exactly once |
| one output | one assignment destination |
| several outputs | a tuple destination in declaration order |
| no outputs | a bare call statement |
| destinations | whole fields only, never list elements |

Explained in [composition](../advanced/composition.md).
