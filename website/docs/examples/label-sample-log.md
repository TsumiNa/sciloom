# Label wells and append a dated log

This procedure takes a Zone, a label and an output directory. After an explicit
OK acknowledgement, it trims the label, captures the date and time once, and
visits each selected well in order. It stores the label as `sample_ID`, reads
that property back, and appends one text cell containing `well name:label`.

For wells B then A and label `"  batch A\t"`, a reference clock set to
2026-09-17 13:00:00 UTC produces `logs/2026-09-17_130000.csv` with two records:

```text
B:batch A
A:batch A
```

The actual file uses UTF-8 and CRLF record endings. The procedure returns the
path and a count of two, then records that count in the `samples/records` log.
This metadata read is stored text, not an instrument measurement.

| Situation | Result |
|---|---|
| Empty Zone | Confirm and capture time, return count zero, append nothing |
| Another call with the same timestamp | Append to the same file; reset the count for this call |
| No acknowledgement available | Stop before changing labels or files |
| File write fails after an earlier row | Stop; keep completed property writes and any bytes already written |

A timestamp does not guarantee a unique filename. The directory must already
exist when using a local file adapter. Appending does not create directories,
replace a file, or repair an incomplete last record.

```console
uv run python examples/label_sample_log.py
```

```text
AutoSuite workflow awaits CSV and location validation.
```

The author script checks the current compilation diagnostics and writes no ASFP.
AutoSuite append behavior and the `zones.well_name()` mapping are still gated.
The unchanged one-well loop target already supplies the proof needed by the
defaulted property read. The
[reference workflow](runtime-workflows-ir.md) supplies files, time, responses and
well properties explicitly and executes the full sequence in memory.

??? example "Complete source"

    ```python
    --8<-- "examples/label_sample_log.py"
    ```

[Download Python](../_generated/examples/label_sample_log.py) ·
[CSV rules](../user-guide/reference/csv.md) ·
[Well properties](../user-guide/reference/well-properties.md)
