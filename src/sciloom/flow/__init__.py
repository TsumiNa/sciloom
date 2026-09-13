"""Procedure and control vocabulary: what an experiment author writes.

`function` declares a Function and its runtime method, `fields` declares runtime
state, `device_slots` declares which logical devices a Function uses, and
`comptime` holds the compile-time device queries allowed in branch conditions.
Composing Functions, globals and application packaging belong here too.

Nothing here reads Python source. `sciloom.dsl` does that, and this package must
not import it except through the recorded seam in `Function.to_ir`.
"""
