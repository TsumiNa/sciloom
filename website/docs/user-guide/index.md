# User Guide overview

This guide is for experiment authors: people who write a procedure in Python and
compile it for equipment. It does not require knowledge of SciLoom's internals.

**[Tutorial](tutorial/index.md).** Five pages build one stirring experiment from
a three-line counter to a compiled AutoSuite package. Start here; every rule
the rest of the guide states is first met there in a program you can run.

**Advanced.** One page per technique, each opening with a complete program that
the documentation tests execute: [composition and shared devices](advanced/composition.md),
[host-time specialization](advanced/specialization.md),
[device-dependent branches](advanced/device-branches.md) and the
[AutoSuite rules](advanced/autosuite.md).

**[FAQ](faq.md) and [Troubleshooting](troubleshooting.md).** Short answers to
the questions authors ask, and every diagnostic code with its cause and fix.

**Reference.** The rules as tables, each row linking to the page that explains
it: [declarations](reference/declarations.md), the
[runtime language](reference/runtime-language.md) and
[devices and targets](reference/devices-and-targets.md).

The [glossary](../glossary.md) defines the terms used across the site. The
[example walkthroughs](../examples/index.md) show complete source files with
their generated packages, and the [API reference](../api/index.md) documents the
author API extracted from the source.
