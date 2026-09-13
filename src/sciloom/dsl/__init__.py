"""DSL source analysis: one Python Function instance to validated IR.

The author's vocabulary lives in `sciloom.flow` and `sciloom.devices`. This
package is the only layer that reads Python source, and it runs only inside
`Function.to_ir()`. Read it in dependency order: `context` holds the shared state
and answers what a `self` attribute means; `source` finds and parses the one
runtime method; `expressions` and `statements` convert the subset, with every
statement recursion living in `statements`; `device_conditions` and
`device_operations` are recognizers the statement pass consults; `driver`
discovers composition and assembles the program.

This module deliberately re-exports nothing: importing `sciloom.Function` must
not load the analysis. `layering_test.py` enforces that, together with the single
deferred import that reaches this package from the vocabulary.

Conventions for adding to the analysis:

1. A function that needs lowering state takes `LoweringContext` as its first
   parameter, named `context`.
2. A recognizer returns `None` for a shape it does not own. Once it has matched,
   it reports through `context.fail` and never returns `None`, because the
   statement pass treats `None` as "try the next recognizer".
3. A name used only inside its own module carries a leading underscore.
4. A function-local import carries a comment naming the cycle it breaks. There is
   one in the whole frontend, and the layering test keeps it that way.
5. Adding a module means: the recognizer and its lowerer, wiring into the
   statement chain at the right position because recognizer order is meaningful,
   a colocated `<module>_test.py`, and the matching entry in the mypy override
   list in `pyproject.toml`.
"""
