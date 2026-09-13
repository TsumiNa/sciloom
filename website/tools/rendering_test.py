"""Check public API HTML and strict-link failures with the real renderer."""

from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


class BrandReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"src", "srcset", "href"} and value and "assets/brand/" in value:
                self.urls.add(value)


def test_rendered_api_and_revision():
    # Always rebuild: a stale local artifact must not mask a broken API change.
    output = ROOT / "website/.build/site"
    subprocess.run([sys.executable, str(ROOT / "website/tools/site.py"), "build", "--strict"], check=True)
    api = (output / "api/author/index.html").read_text()
    for symbol in ("Function", "Input", "Output", "Var", "Agitator"):
        assert f'id="sciloom.{symbol}"' in api
    assert "RotationalSpeed" in api
    assert "CompileResult" in api
    info = json.loads((output / "build-info.json").read_text())
    assert info["commit"][:8] in api
    assert info["version"] in api
    assert not (output / "autosuite").exists()
    assert not (output / "refactor").exists()
    assert not (output / "_generated/examples/proposed_frontend").exists()

    # Branding must survive nested page URLs and publication under /dev/.
    for name in ("index.html", "developer/brand/index.html", "api/author/index.html"):
        page = output / name
        references = BrandReferences()
        references.feed(page.read_text())
        assert any(url.endswith("favicon.svg") for url in references.urls)
        for url in references.urls:
            parsed = urlsplit(url)
            assert not parsed.scheme and not parsed.path.startswith("/")
            asset = (page.parent / parsed.path).resolve()
            assert asset.is_relative_to((output / "assets/brand").resolve())
            relative = asset.relative_to(output.resolve())
            assert asset.read_bytes() == (ROOT / "website/docs" / relative).read_bytes()

    readme = BrandReferences()
    readme.feed((ROOT / "README.md").read_text())
    assert len(readme.urls) == 2
    assert all((ROOT / url).is_file() for url in readme.urls)

    brand = output / "assets/brand"
    manifest = json.loads((brand / "manifest.json").read_text())
    assert set(manifest["files"]) == {
        str(path.relative_to(brand)) for path in brand.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }


def test_strict_renderer_rejects_broken_internal_link(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Broken\n\n[Missing](missing.md)\n")
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Broken link test\ndocs_dir: docs\nsite_dir: output\n")
    result = subprocess.run(
        [sys.executable, "-m", "zensical", "build", "--strict", "-f", str(config)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "page does not exist" in result.stdout + result.stderr
