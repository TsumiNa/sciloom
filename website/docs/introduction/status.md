# Current capabilities

With Python 3.12–3.14, you can write a procedure in a `.py` file and generate an
AutoSuite function package (`.asfp`). The current author API lets you:

- Declare inputs, outputs and working values, including typed lists.
- Calculate values, use `if` and `while`, and call reusable child Functions.
- Save shaker settings and explicitly start or stop agitation.
- Share a logical device between steps and bind it to an AutoSuite shaker.
- Choose device-specific branches when compiling for a target.

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
