# Static typing for SciLoom development

Run `uv sync --locked` and `uv run mypy` from the repository root. Mypy is a locked
development dependency; CI runs the same command on Python 3.12, 3.13 and 3.14.
The default scope is production `src/sciloom` and the six runnable author/developer
examples. Colocated runtime tests and conftest files are excluded because many
intentionally create invalid schemas and IR. Positive/negative static tests run
mypy on separate source fixtures as part of pytest.

Core/contrib functions have complete annotations, with `disallow_untyped_defs`,
`disallow_incomplete_defs` and `check_untyped_defs` enabled. DSL bodies are also
checked, without whole-repository strict mode or a custom plugin. The wheel
contains `sciloom/py.typed`, so downstream consumers can inspect the annotations.

## Author declarations and command signatures

`Input[T]`, `Output[T]` and `Var[T]` are Annotated aliases. Mypy sees `T`; SciLoom
separately reads role metadata during schema construction. The following is a
static-check illustration, not a program to execute as host Python:

```python
from typing import assert_type
from sciloom import Function, Input, Output, Var, runtime

class Scale(Function):
    factor: Input[float]
    values: Input[list[float]]
    result: Output[list[float]]
    index: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.result = self.values
        self.result[self.index] *= self.factor

assert_type(Scale().factor, float)  # Static type; host access raises at runtime.
```

`Var[int] = "text"`, a string element in `list[float]`, or assignment of text to
`Input[float]` produces a mypy error. ParamSpec/TypeVar preserve the decorated
method's parameters and return type. Agitator commands have DSL return type None,
so statements after them are checked; direct host execution still raises.

Mypy does not enforce role nesting, mandatory initial values, descriptor access
protection, the full restricted source subset, Function call binding, physical
limits or vendor constraints. In particular Python typing treats bool as an int
subtype, while SciLoom's semantic validator excludes bool indices. Runtime/IR
validation remains necessary. No Any-based compatibility API is introduced.

## Contributor interfaces

The [authoritative device contract](refactor/device-abstraction/00-overview.md#compiler-and-binding-interface)
shows the exact Target/Artifact/CompileResult interfaces and an independent target.
Targets now implement `resolve_devices(program) -> DeviceBindings`, including
device-free targets, which return `DeviceBindings()`.
Mypy rejects a Target whose emit returns str, incorrect Artifact content types,
and incorrect IR constructor arguments. A valid target's compilation result is
CompileResult, its artifact is Artifact, and write returns pathlib.Path.

Interpreter list inputs accept typed Python lists and tuples; invariant list
typing is accounted for explicitly. Scalar/list conversion overloads retain the
correct return shape. Immutable snapshots continue to expose tuples.

Regression checks are in `core/compiler_typing_test.py` and
`dsl/schema_typing_test.py`. They verify both successful checks and the expected
error counts/codes, so accidentally erasing a public type to Any fails the tests.
