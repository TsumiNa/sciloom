"""Publication boundary and exact-checkout metadata regressions."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location("docs_site", Path(__file__).with_name("site.py"))
assert SPEC and SPEC.loader
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


@pytest.fixture
def checkout(tmp_path):
    (tmp_path / "docs/site").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n')
    for name in site.EXAMPLES:
        p = tmp_path / "examples" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("learning asset\n")
    for args in (("init", "-b", "main"), ("add", "."),
                 ("-c", "user.name=Docs Test", "-c", "user.email=docs@example.invalid", "commit", "-m", "initial")):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    return tmp_path


def test_metadata_identifies_checkout_and_dirty_changes(checkout):
    info = site.source_info(checkout)
    assert info == {"version": "local", "ref": "main", "package_version": "0.1.0",
                    "commit": site.git(checkout, "rev-parse", "HEAD")}
    preview = site.source_info(checkout, preview="29")
    assert (preview["version"], preview["ref"]) == ("preview", "refs/pull/29/head")
    (checkout / "pyproject.toml").write_text('[project]\nversion = "0.2.0"\n')
    assert site.source_info(checkout)["version"] == "local-dirty"
    with pytest.raises(ValueError, match="clean"):
        site.source_info(checkout, preview="29")


def test_prepare_only_copies_explicit_examples(checkout):
    (checkout / "examples/private.txt").write_text("not public")
    (checkout / "autosuite").mkdir()
    (checkout / "autosuite/raw.app").write_text("not public")
    info = site.source_info(checkout)
    site.prepare(checkout, info)
    public = checkout / "docs/site"
    copied = public / "_generated/examples"
    assert {str(p.relative_to(copied)) for p in copied.rglob("*") if p.is_file()} == set(site.EXAMPLES)
    assert json.loads((public / "build-info.json").read_text()) == info
    for name in site.EXAMPLES:
        assert (copied / name).read_bytes() == (checkout / "examples" / name).read_bytes()
    (copied / "stale.txt").write_text("stale")
    site.prepare(checkout, info)
    assert not (copied / "stale.txt").exists()


def test_symlink_cannot_copy_unselected_evidence(checkout):
    secret = checkout / "private.txt"
    secret.write_text("not selected")
    example = checkout / "examples" / site.EXAMPLES[0]
    example.unlink()
    example.symlink_to(secret)
    with pytest.raises(ValueError, match="allowlist"):
        site.prepare(checkout, site.source_info(checkout))


def test_metadata_symlink_does_not_overwrite_source(checkout):
    source = checkout / "pyproject.toml"
    before = source.read_bytes()
    (checkout / "docs/site/build-info.json").symlink_to(source)
    with pytest.raises(ValueError, match="metadata"):
        site.prepare(checkout, site.source_info(checkout))
    assert source.read_bytes() == before


def test_public_directory_symlink_is_rejected(checkout):
    public = checkout / "docs/site"
    public.rmdir()
    public.symlink_to(checkout / "examples", target_is_directory=True)
    with pytest.raises(ValueError, match="documentation"):
        site.prepare(checkout, site.source_info(checkout))
