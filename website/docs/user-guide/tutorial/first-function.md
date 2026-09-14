# 1. Your first Function

A SciLoom program is a Python class. Its class body declares what the program
remembers and exchanges, and one method holds what it does. Nothing in the class
runs on your computer: SciLoom reads the method's source and compiles it.

Start the file with the smallest useful Function, a counter that remembers how
many times stirring has been requested.

<!-- tutorial: step -->
```python
from sciloom import Function, Var, runtime
from sciloom_autosuite import AutoSuiteTarget


class CountStirs(Function):
    """Count how many times stirring has been requested in this session.

    Attributes:
        stirs: Number of requests so far; persists across calls.
    """

    stirs: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.stirs += 1
```

Three things happen here.

`stirs: Var[int] = 0` declares **persistent state**. A `Var` needs a literal
initial value on the class, and that value is the state when the session starts,
not an assignment on every call: the second call sees the count the first call
left behind. If a value should start at zero on every call, reset it inside the
runtime method, as page 3 does. State belongs to an instance; two `CountStirs()`
instances count separately.

`@runtime` marks the **one method SciLoom compiles**. It takes only `self`. It
must live in an ordinary `.py` file, because SciLoom reads its source text;
notebook cells, `exec()` and `async def` are refused.

The **class docstring** describes the procedure, and its `Attributes:` section
names the declared fields. Docstrings help readers and tools; they never change
what compiles.

Compile the counter. `AutoSuiteTarget` is the equipment target every page of
this tutorial compiles for; it needs no device mapping for a program that
declares no device:

<!-- tutorial: checkpoint -->
```python
print(CountStirs().compile(target=AutoSuiteTarget()).write("count_stirs.asfp").name)
```
```text
count_stirs.asfp
```

The package is written to the directory you ran the command from, because the
name is relative; page 5 writes it beside the script instead. Nothing was executed: the target was
chosen explicitly, the program was checked, and the file was produced.

Host Python never touches runtime state. Reading a `Var` from outside the
runtime method is refused, and the message tells you where the rule lives:

<!-- tutorial: checkpoint -->
```python
try:
    CountStirs().stirs
except Exception as error:
    print(error)
```
```text
$.schema.stirs: Runtime fields cannot be read by host Python. [runtime_field_read]
```

Every SciLoom error reads this way: a path into the program, a message, and a
code in brackets.

Next: [2. Inputs, outputs and speeds](inputs-and-units.md).
