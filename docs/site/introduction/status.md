# Current capabilities

SciLoom supports Python 3.12–3.14. Runtime methods come from ordinary Python files
and are translated by source analysis; arbitrary Python execution is not part of
the language. The semantic interchange format is Program/JSON v4.

Implemented features include typed Function inputs/outputs/state, scalar and
one-dimensional homogeneous lists, assignments, expressions, if/while, Function
calls, logical device slots and explicit target bindings. Agitator configuration
is captured by property assignment and applied by `start()`; `stop()` is explicit.
Device-dependent branches can be selected at compile time.

The AutoSuite target emits ASFP. An independent demonstration target validates
the extension boundary. A reference interpreter defines SciLoom execution
behavior; it does not simulate laboratory hardware.

GUI/server, public Application/global APIs, measured property reads, Notebook and
interactive source support remain future work. XML checks and reference execution
do not establish acceptance by AutoSuite Executor or real equipment.
