# Write a stirring procedure

Begin with a shaker running at a fixed speed. Then let the caller choose the
speed, extract a reusable calculation, handle a rack of samples and count start
requests.

| Lesson | What you will change |
| --- | --- |
| [1. Start a shaker](first-function.md) | Write and compile two experimental steps |
| [2. Supply a speed and switch](inputs-and-units.md) | Replace a fixed value with inputs and add a stop branch |
| [3. Reuse a calculation](agitator.md) | Choose a speed from sample volume in a separate Function |
| [4. Work with a list of samples](lists-and-loops.md) | Find the largest supplied volume |
| [5. Keep a count across calls](compile.md) | Add a persistent counter and complete the procedure |

Follow [Getting started](../../introduction/getting-started.md) to install the
checkout. Each lesson supplies a complete Python file and its generated package.
Use that lesson's file as your working copy; you do not need to paste all five
files into one script.

The examples use supplied volume data. They do not measure samples. The speeds
and thresholds illustrate the language, rather than a validated experimental
method. Running the Python files compiles them; equipment execution requires
AutoSuite and validation on the deployment computer.
