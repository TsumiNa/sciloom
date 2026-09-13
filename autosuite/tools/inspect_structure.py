#!/usr/bin/env python3
# Lightweight structural inspector for .app (gzip XML) and .asfp.
import sys

from autosuite_io import load


def text(e, tag, default=""):
    c = e.find(tag)
    return c.text if c is not None and c.text is not None else default


def walk(e, depth=0):
    tid = e.attrib.get("typeid", "")
    if tid:
        print("  " * depth + f"{e.tag}: {text(e, 'name')!r} [{tid}]")
        depth += 1
    # Untyped container elements (components, tasks, functions, elements) must
    # also be traversed so their typed descendants appear in the outline.
    for c in e:
        walk(c, depth)


if __name__ == "__main__":
    walk(load(sys.argv[1]))
