---
description: 'Use when creating or updating runnable examples and their learning documentation, especially examples that compile programs, execute an interpreter, or generate artifacts.'
name: 'Example Output Documentation'
applyTo: 'examples/**,docs/**,website/**'
---

# Example Output Documentation

Keep example code and its observable results together so readers can understand
the outcome without first running the example or studying compiler internals.

- State the intended audience, run command and expected result in the code file's
  module-level docstring (or an equivalent top-of-file comment).
- Put short output directly in that docstring. Include terminal output or a small
  generated fragment where it helps explain the result. Mark excerpts and omitted
  fields explicitly; do not present abbreviated output as a complete artifact.
- Generate long output as a complete companion file beside the code that produces
  it. Use the same base name and the appropriate extension: `agitation.py` produces
  `agitation.asfp`; `agitation_ir.py` produces `agitation_ir.json`. For multiple
  formats, use suffixes such as `example.asfp`, `example.ir.json` and
  `example.stdout.txt`.
- Treat output as long when embedding it would obscure the example's code or
  explanation. Keep a short summary and the companion file's relative path in the
  module docstring; the full output belongs in the companion file.
- Commit companion files with their generating examples. A learning reference
  must not exist only in `dist/`, an ignored directory or a temporary location.
- Obtain documented results and companion files by actually running the example.
  When behavior changes, regenerate them and verify that they match the current
  code. Identify any abbreviated or environment-dependent parts explicitly.
- Preserve the audience boundary: experiment-author examples explain source code
  and target results; IR, JSON interchange and interpreter internals belong in
  developer examples. Distinguish compilation, reference execution and hardware
  execution when describing results.
- Write generated learning artifacts under the example directory, never over raw
  reference evidence in `autosuite/`.
