# Extending the analysis

`sciloom.dsl` is the only layer that reads Python source. It is a chain of
recognizers, each owning one shape of statement or expression, and adding a
shape means adding one link to that chain.

## The conventions

Shared state, source discovery, expression conversion and statement conversion
have separate responsibilities, and every statement recursion lives in one
module. A function that needs lowering state takes the context first, and the
parameter is named `context`.

A recognizer returns `None` for a shape it does not own. Once it has matched, it
reports every problem through `context.fail` rather than returning `None`,
because the statement pass reads `None` as "try the next recognizer". Recognizer
order is therefore meaningful: the device-property write is tried before the
plain assignment, and a compile-time query before an ordinary `if`.

Names used only inside their module are underscore-prefixed. The one
function-local import in the frontend, `Function.to_ir` importing the analysis
driver, carries a comment naming the cycle it breaks; do not add another. IR
structure checking, expression typing, program validation and JSON conversion
stay distinct, and the interpreter separates values, expression evaluation and
session state.

## Adding a shape

1. Add the recognizer and its lowering in the module that owns the shape.
2. Insert it in the chain at the position its precedence requires.
3. Add the colocated `<module>_test.py` case that exercises the shape and the
   diagnostic for its nearest wrong form.
4. Add the new test module to the mypy override list in `pyproject.toml`; the
   list exists for excluded test modules, and production modules are already
   covered, as [typing and tests](../typing-and-tests.md) describes.
5. Run the [verification](../reference/verification.md) list.

A shape that needs a new IR node is a change to the semantic contract and starts
in `docs/` as a design document with concrete examples before any recognizer is
written.

Give a new serializable record its own stable `__ir_kind__: ClassVar[str]` and
keep its field names part of the [wire contract](../reference/ir.md). Structural
conversion follows those typed fields; do not add a second JSON schema. Reuse
device property and command contracts when they already express the behavior.

For a new expression or statement, update type checking, scope and flow validation,
specialization, configuration analysis, reference execution and target handling
together. An unsupported target must report a diagnostic. Closed-union dispatchers
end in `assert_never`, so mypy identifies missing handlers. A test also removes
supported handlers in a temporary copy to verify that these checks detect omissions.
Keep the frozen v4 compatibility fixtures unchanged; they establish that old
documents still execute and produce the same bytes, independently of current examples.
