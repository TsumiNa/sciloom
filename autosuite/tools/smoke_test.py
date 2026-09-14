"""Quick checks for the reference AutoSuite application and the recipe.

The application lives in the shared corpus, which is not in git; its checks are
skipped when the corpus is absent. The recipe is part of this repository and is
always checked.
"""

import gzip
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
app = BASE / "corpus/app/config20260909_polymerization.app"
if app.is_file():
    raw = app.read_bytes()
    assert raw[:2] == b"\x1f\x8b"
    root = ET.fromstring(gzip.decompress(raw))
    assert root.tag == "application"
    assert root.attrib["productversion"] == "2.47.1.1"
    assert len(root.findall("./functions/functions/function")) == 52
    assert len(root.findall("./zones/zones/zone")) == 75
    print("AUTOSUITE SMOKE TEST: application OK")
else:
    print(f"AUTOSUITE SMOKE TEST: no corpus at {app.parent}; see autosuite/README.md")
subprocess.run(
    [sys.executable, str(BASE / "recipe/validate_recipe.py"), str(BASE / "recipe/input_0908.csv")], check=True
)
print("AUTOSUITE SMOKE TEST: OK")
