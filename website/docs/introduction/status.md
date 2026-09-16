# Current capabilities

With Python 3.12–3.14, you can write a procedure in a `.py` file and generate an
AutoSuite function package (`.asfp`). The current author API lets you:

- Declare inputs, outputs and working values, including typed lists.
- Process text and calculate volumes, time intervals and rotational speeds with explicit units.
- Calculate values, use `if` and `while`, and call reusable child Functions.
- Calculate magnitudes and round down; nearest-integer rounding of floats is available in reference execution, pending AutoSuite equivalence checks.
- Save shaker settings and explicitly start or stop agitation.
- Share a logical device between steps and bind it to an AutoSuite shaker.
- Choose device-specific branches when compiling for a target.
- Record supplied values and request an explicit OK acknowledgement before continuing.

The runtime method accepts a [restricted Python subset](../user-guide/reference/runtime-language.md).
Constructors and the surrounding script remain ordinary Python.

Contributors can define devices and targets. The developer examples include a
demonstration target, JSON v4 interchange and a reference interpreter for checking
calculations and state changes. That interpreter does not simulate laboratory hardware.

A visual editor, server, public Application/global API, measured property reads,
and notebook or interactive source support are not yet available.

## What compilation establishes

Compilation checks the source, value types, declared device bindings and required
configuration before generating XML. It does not connect to the instrument or
prove that the procedure will run correctly on your deployment.

Generated packages still need AutoSuite Executor validation and equipment
acceptance. Array bounds checks, device mappings and fault/recovery behaviour
require platform verification; SciLoom's reference execution cannot establish
the instrument's numerical or physical behaviour.

The generated OK dialog is available for inspection and simulation; platform
execution remains unverified. Before equipment use, check on the AutoSuite host
that it blocks later steps until OK and resumes exactly once. The
[confirmation example](../examples/confirm-samples.md) describes that acceptance
gate. Supplying a response to the reference interpreter does not pass it.
