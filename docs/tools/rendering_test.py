"""Check public API HTML and strict-link failures with the real renderer."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_rendered_api_and_revision():
    # Always rebuild: a stale local artifact must not mask a broken API change.
    output = ROOT / ".build/docs"
    subprocess.run([sys.executable, str(ROOT / "docs/tools/site.py"), "build", "--strict"], check=True)
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
