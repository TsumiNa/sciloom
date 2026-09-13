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
"""
