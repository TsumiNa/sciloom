"""Quick checks for the current AutoSuite application and recipe."""

from pathlib import Path
import gzip
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
app = BASE / "app/config20260909_polymerization.app"
raw = app.read_bytes()
assert raw[:2] == b"\x1f\x8b"
root = ET.fromstring(gzip.decompress(raw))
assert root.tag == "application"
assert root.attrib["productversion"] == "2.47.1.1"
assert len(root.findall("./functions/functions/function")) == 52
assert len(root.findall("./zones/zones/zone")) == 75
subprocess.run([sys.executable, str(BASE / "recipe/validate_recipe.py"),
                str(BASE / "recipe/input_0908.csv")], check=True)
print("AUTOSUITE SMOKE TEST: OK")
