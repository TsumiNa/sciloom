#!/usr/bin/env python3
import csv
import sys


def validate(path, expected_total_ml=3.0, tol=1e-6):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    if not rows:
        return ["CSV has no data rows"]
    headers = list(rows[0].keys())
    errors = []
    if not headers or headers[0] != "EXP_ID":
        errors.append("first column must be EXP_ID")
    if len(headers) < 2:
        errors.append("at least one reagent column is required")
    for i, r in enumerate(rows, start=2):
        vals = [(r.get(h) or "").strip() for h in headers]
        if not any(vals):
            continue
        if not vals[0]:
            errors.append(f"line {i}: active row has empty EXP_ID")
        total = 0.0
        for h in headers[1:]:
            s = (r.get(h) or "").strip()
            if not s:
                s = "0"
            try:
                v = float(s)
            except ValueError:
                errors.append(f"line {i}: {h} is not numeric: {s!r}")
                continue
            if v < 0:
                errors.append(f"line {i}: {h} is negative")
            total += v
        if abs(total - expected_total_ml) > tol:
            errors.append(f"line {i}: reagent total {total:g} mL != {expected_total_ml:g} mL")
    return errors


if __name__ == "__main__":
    p = sys.argv[1]
    errs = validate(p)
    if errs:
        print("\n".join("ERROR: " + x for x in errs))
        raise SystemExit(1)
    print("OK")
