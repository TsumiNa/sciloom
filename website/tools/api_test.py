"""Verify the curated reference against static exports and rendered object anchors."""

from pathlib import Path
import re
import subprocess
import sys

from griffe import GriffeLoader

ROOT = Path(__file__).resolve().parents[2]


def test_catalogue_covers_exports_with_static_docstrings():
    loader = GriffeLoader(search_paths=[ROOT / "src"], allow_inspection=False)
    package = loader.load("sciloom")
    loader.resolve_aliases(implicit=True, external=False)
    pages = list((ROOT / "website/docs/api").glob("*.md"))
    paths = {p for page in pages for p in re.findall(r"^::: (\S+)", page.read_text(), re.M)}
    for module in ("sciloom", "sciloom.core.ir", "sciloom.devices", "sciloom.core.interpreter", "sciloom.contrib.autosuite"):
        obj = package if module == "sciloom" else package[module.removeprefix("sciloom.")]
        for name in obj.exports:
            exported = obj[name]
            if name == "comptime":
                assert all(f"sciloom.comptime.{query}" in paths for query in ("can_write", "supports", "is_device"))
            else:
                # Re-exported diagnostics and Agitator use their recommended public page.
                candidates = {module + "." + name, exported.canonical_path, "sciloom." + name}
                assert candidates & paths, (module, name)
    for path in paths:
        obj = package[path.removeprefix("sciloom.")]
        assert obj.docstring and obj.docstring.value.strip(), path
        assert not any(part.startswith("_") or part.endswith("_test") for part in path.split("."))


def test_catalogue_objects_have_html_anchors():
    subprocess.run([sys.executable, str(ROOT / "website/tools/site.py"), "build", "--strict"], check=True)
    for page in (ROOT / "website/docs/api").glob("*.md"):
        html = (ROOT / "website/.build/site/api" / page.stem / "index.html") if page.stem != "index" else ROOT / "website/.build/site/api/index.html"
        rendered = html.read_text()
        for path in re.findall(r"^::: (\S+)", page.read_text(), re.M):
            assert f'id="{path}"' in rendered, path
    author = (ROOT / "website/.build/site/api/author/index.html").read_text()
    assert 'id="sciloom.Agitator.speed"' in author
    assert 'id="sciloom.Function.compile"' in author
    compiler = (ROOT / "website/.build/site/api/compiler/index.html").read_text()
    assert 'id="sciloom.core.compiler.Target.resolve_devices"' in compiler
    assert "DeviceBindings" in compiler
    assert "DeviceBinding.__post_init__" not in compiler
