# Stir a rack of samples

This tutorial builds one experiment from nothing to a compiled AutoSuite
package. A rack of vials sits on an individual shaker. The program measures the
largest sample volume in the rack, chooses a stirring speed for it, and either
configures the shaker and starts it or stops it. Each page adds one class to the
program; the last page shows the complete file, which is also the runnable
[stir-rack example](../../examples/stir-rack.md).

| Page | You add | You learn |
|---|---|---|
| [1. Your first Function](first-function.md) | `CountStirs` | a Function class, persistent state, the one runtime method |
| [2. Inputs, outputs and speeds](inputs-and-units.md) | `ChooseSpeed` | values exchanged per call, rotational speed, `if`/`else` |
| [3. Lists and loops](lists-and-loops.md) | `LargestVolume` | list inputs, `while` with an index, `len` |
| [4. Stirring with an Agitator](agitator.md) | `StirRack` | a logical device, child Functions, configure then start, stop |
| [5. Bind and compile](compile.md) | the `__main__` block | binding a real shaker and writing the `.asfp` |

Before you start, follow [getting started](../../introduction/getting-started.md)
so that `uv run python` finds `sciloom` and `sciloom_autosuite`. Keep one file,
for example `stir_rack.py`, and paste each page's step into it in order; the
checkpoints on each page are short extra lines you can run and then delete.
Every checkpoint output shown here was produced by running that code.

--8<-- "website/snippets/hardware-boundary.md"
