# Compiler foundation

Accepted 2026-09-11. The purpose is to validate engineering boundaries with a small,
independently executable IR and a real agitation operation. Examples probe the
architecture; fixture details must not define its public language.

## Decisions

- Python source lowering belongs to the Python frontend; typed SciLoom semantics
  are shared by JSON, future GUI/AI authoring, reference execution and targets.
- Generic compilation validates IR and delegates through an explicit target
  contract. XML structure, serialization IDs and AutoSuite constraints stay inside
  its backend. No implicit AutoSuite target or old internal-module aliases remain.
- Program replaces Package; JSON v2 describes the new contract. No v1 compatibility
  layer is required. Preserve Function, Input/Output, scalar types and runtime DSL.
- A reference interpreter executes IR, never source Python or generated XML.
  Function internal state persists within a session; input/output frames are per
  call. Errors stop execution, budgets bound loops and recursion.
- Logical agitation resources, rotational-speed quantities and set/stop intent
  remain visible in IR. Target bindings choose AutoSuite zones. Reference execution
  records commanded state, not mixing quality or physical setpoint attainment.
- Learn progressive lowering and target legality from MLIR without introducing its
  dependency, SSA, an optimizer, plugin registry or speculative generic operations.

## Scope and evidence

The production Sample and Run GPC function establishes agitation task structure;
the manual section 3.6.19 establishes control semantics. Only rpm and revolutions
per second are required initially. Existing FIXED fixtures continue to validate
scalar/control-flow ASFP. Original evidence remains unchanged. Executor acceptance
is a separate integration gate; reference execution does not prove vendor runtime
compatibility or numerical edge-case equivalence.

Application/globals, temperature, transfer, general unit algebra, GUI, AI services,
Notebook/interactive/exec source and real-device execution remain outside scope.

## Ordered PRs

1. [Organize compiler module boundaries](01-module-boundaries.md).
2. [Isolate target compilation](02-target-contract.md).
3. [Specify independently executable IR](03-reference-interpreter.md).
4. [Preserve agitation intent in domain IR](04-agitation-semantics.md).
5. [Validate agitation on the AutoSuite backend](05-autosuite-agitation.md).

Record this plan with PR1. Complete checks, inspect all review surfaces, address
feedback, squash merge and verify remote MERGED before beginning the next stage.
Every stage must pass independently; unsupported constructs fail explicitly.

## Baseline checks for every PR

Run pytest on src/sciloom, AutoSuite smoke and recipe checks, proposed-example
syntax checks, and executable examples. Audit corpus after reference-document
updates. Only run examples and feature tests implemented by the current stage.

## End-state acceptance

The following capabilities are introduced incrementally by PR2–PR5, not required
of the behavior-preserving PR1. Their owning stage adds the corresponding tests.
By the end of PR5, tests establish IR execution without backend imports,
non-XML target compilation, Python/JSON/direct-IR equivalence, state isolation,
errors/budgets, retained domain intent and production XML field relationships.

## References

- [MLIR rationale](https://mlir.llvm.org/docs/Rationale/Rationale/)
- [Target legality and conversion](https://mlir.llvm.org/docs/DialectConversion/)
- [Side effects](https://mlir.llvm.org/docs/Rationale/SideEffectsAndSpeculation/)

## Completed gates

PR1: #5 merged as `70a88f0d58b62e9bda2747e80b4bd5d5ffd342f9`; 79 tests and
Python 3.12–3.14 CI passed. Copilot acceptance-scope feedback was addressed.
