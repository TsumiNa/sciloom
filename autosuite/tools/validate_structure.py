#!/usr/bin/env python3
import json
import sys

from autosuite_io import load

PROFILE = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
r = load(sys.argv[1])
errs = []
warns = []
if r.tag not in ("application", "functions"):
    errs.append(f"unexpected root: {r.tag}")
if r.tag == "application":
    if r.attrib.get("productversion") is None:
        warns.append("application lacks productversion")
    for tag in ("configuration", "tasks", "functions", "zones"):
        if r.find(tag) is None:
            errs.append(f"application missing {tag}")
if r.tag == "functions":
    for f in r.findall("./function"):
        if f.attrib.get("typeid") not in ("Chemspeed.SATaskFunctionDefinition.1", "Chemspeed.SATaskEventFunction.1"):
            warns.append("unseen function type " + str(f.attrib.get("typeid")))
        if f.find("id") is None and f.find("functionid") is None:
            warns.append("function lacks id/functionid: " + (f.findtext("name") or "?"))
print("ERRORS", len(errs))
[print("ERROR:", x) for x in errs]
print("WARNINGS", len(warns))
[print("WARN:", x) for x in warns]
raise SystemExit(1 if errs else 0)
