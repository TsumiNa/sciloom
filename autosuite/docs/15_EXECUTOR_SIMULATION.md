# AutoSuite Executor simulation reference

AutoSuite Software Manual 2.47.1.1, section 4.5.1 (manual page 185) documents:

```text
AutoSuiteExecutor.exe [file] [/?] [/r] [/sim [xx]] [/s] [/m xx]
```

Relevant options:

- `[file]`: application path
- `/?`: help
- `/r`: automatically run after loading
- `/sim xx`: simulation mode, factor 1-100
- `/real`: real mode
- `/c`: close automatically after application finishes
- `/s`: silent mode (fewer dialogs)
- `/m xx`: ArkSuite module mode; also enables `/s`
- `/var "<var>=<expr>;..."`: initialize global variables

For compiler smoke testing, the intended command is:

```bat
AutoSuiteExecutor.exe generated.app /r /sim 100 /s /c
```

This package cannot execute that command because `AutoSuiteExecutor.exe` is not present here. Static validation is therefore not equivalent to an Executor acceptance test.

Project testing also found that command-line array injection should not be relied on as a general array input mechanism; use files/CSV for nontrivial vector inputs.
