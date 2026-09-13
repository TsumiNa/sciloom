"""Exercise version history with the real pinned mike fork in isolated Git repos."""

from dataclasses import asdict, replace
import json
import os
import shutil
import subprocess
import sys
import tomllib

import pytest

from docs.tools import publication as pub


def test_reconcile_missing_tags_and_reject_moved_release():
    first = pub.Snapshot("0.1.0", "v0.1.0", "a" * 40, "0.1.0")
    second = pub.Snapshot("0.2.0", "v0.2.0", "b" * 40, "0.2.0")
    dev = pub.Snapshot("dev", "main", "c" * 40, "0.2.0")
    candidates = [dev, second, first]
    assert pub.select_snapshots(candidates, {}, {first.commit, second.commit}) == [first, second]
    assert pub.select_snapshots(candidates, {first.version: asdict(first)}, {item.commit for item in candidates}) == [second, dev]
    with pytest.raises(ValueError, match="overwrite"):
        pub.select_snapshots([replace(first, commit="d" * 40)], {first.version: asdict(first)}, set())
    with pytest.raises(ValueError, match="mismatch"):
        pub.select_snapshots([replace(first, package_version="0.2.0")], {}, {first.commit})
    with pytest.raises(ValueError, match="canonical"):
        pub.release_key("01.2.3")


@pytest.fixture
def history(tmp_path):
    storage = tmp_path / "history"
    storage.mkdir()
    pub.git(storage, "init", "-q")
    pub.git(storage, "config", "user.name", "Docs Test")
    pub.git(storage, "config", "user.email", "docs@example.invalid")
    return storage


def test_two_releases_and_dev_preserve_history_and_highest_stable(history, tmp_path):
    site = tmp_path / "site"
    source = tmp_path / "body"
    (source / "api").mkdir(parents=True)
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Version fixture\nsite_url: https://tsumina.github.io/sciloom/\n"
                      "docs_dir: body\nsite_dir: site\ntheme:\n  font: false\n"
                      "extra:\n  version:\n    provider: mike\n")
    saved = {}
    for version, sha in (("0.2.0", "b"), ("0.1.0", "a"), ("dev", "c"), ("dev", "d")):
        snapshot = pub.Snapshot(version, "main" if version == "dev" else "v" + version, sha * 40,
                                "0.2.0" if version == "dev" else version)
        (source / "index.md").write_text(f"# Version {version}\n\nSource {sha * 40}.\n\n[API](api/index.md)\n")
        (source / "api/index.md").write_text(f"# API {version}\n\nUniqueSearch{sha}Only\n")
        (source / "build-info.json").write_text(json.dumps(asdict(snapshot)))
        subprocess.run([sys.executable, "-m", "zensical", "build", "--strict", "--clean", "-f", str(config)],
                       cwd=tmp_path, env={**os.environ, "MIKE_DOCS_VERSION": version}, check=True)
        assert f'https://tsumina.github.io/sciloom/{version}/' in (site / "index.html").read_text()
        pub.record(history, site, snapshot)
        pub.aliases(history)
        for name, tree in saved.items():
            assert pub.git(history, "rev-parse", f"gh-pages:{name}") == tree
        if version != "dev":
            saved[version] = pub.git(history, "rev-parse", f"gh-pages:{version}")
    versions = json.loads(pub.git(history, "show", "gh-pages:versions.json"))
    assert next(v for v in versions if v["version"] == "0.2.0")["aliases"] == ["stable"]
    assert 'href="stable/"' in pub.git(history, "show", "gh-pages:index.html")
    assert 'href="../../0.2.0/api/"' in pub.git(history, "show", "gh-pages:stable/api/index.html")
    assert json.loads(pub.git(history, "show", "gh-pages:dev/build-info.json"))["commit"] == "d" * 40
    assert not any(line.startswith("120000") for line in pub.git(history, "ls-tree", "-r", "gh-pages").splitlines())
    # No source commit/history was copied into this independently initialized repo.
    assert pub.git(history, "rev-list", "--max-parents=0", "gh-pages")


def test_dev_only_default_and_publication_boundary(history, tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    snapshot = pub.Snapshot("dev", "main", "a" * 40, "0.1.0")
    (site / "index.html").write_text("dev")
    (site / "build-info.json").write_text(json.dumps(asdict(snapshot)))
    pub.record(history, site, snapshot)
    pub.aliases(history)
    assert 'href="dev/"' in pub.git(history, "show", "gh-pages:index.html")
    with pytest.raises(ValueError, match="metadata"):
        pub.record(history, site, replace(snapshot, commit="b" * 40))
    (site / "autosuite").mkdir()
    with pytest.raises(ValueError, match="Unexpected"):
        pub.audit_site(site, ())
    (site / "autosuite").rmdir()
    (site / "api").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        pub.audit_site(site, ())
    (site / "api").unlink()
    (site / "_generated/examples").mkdir(parents=True)
    (site / "_generated/examples/private.py").write_text("not selected")
    with pytest.raises(ValueError, match="allowlist"):
        pub.audit_site(site, ())


@pytest.mark.parametrize("failure", [None, "wrong_commit", "wrong_repository", "missing_job", "pull_request"])
def test_exact_commit_ci_gate(monkeypatch, failure):
    run = {"id": 1, "head_sha": "a" * 40, "event": "push", "head_repository": {"full_name": "owner/repo"}}
    if failure == "wrong_commit":
        run["head_sha"] = "b" * 40
    if failure == "wrong_repository":
        run["head_repository"]["full_name"] = "other/repo"
    if failure == "pull_request":
        run["event"] = "pull_request"
    jobs = [{"name": name, "conclusion": "success"} for name in pub.CHECKS]
    if failure == "missing_job":
        jobs.pop()

    def response(command, **kwargs):
        return json.dumps([{"jobs": jobs}] if "/jobs?" in command[-1] else [{"workflow_runs": [run]}])

    monkeypatch.setattr(subprocess, "check_output", response)
    assert pub.checked("owner/repo", "a" * 40) is (failure is None)


def test_locked_checkout_pipeline_and_stale_dev_rejection(tmp_path, monkeypatch):
    """Build actual docs in a separate source repo; mock only the GitHub CI response."""
    root = tmp_path / "source"
    root.mkdir()
    for name in ("README.md", "pyproject.toml", "uv.lock", ".gitignore", ".python-version", "mkdocs.yml"):
        shutil.copyfile(pub.ROOT / name, root / name)
    for name in ("src", "docs", "examples"):
        shutil.copytree(pub.ROOT / name, root / name,
                        ignore=shutil.ignore_patterns("__pycache__", "_generated", "build-info.json"))
    pub.git(root, "init", "-q", "-b", "main")
    pub.git(root, "config", "user.name", "Docs Test")
    pub.git(root, "config", "user.email", "docs@example.invalid")
    pub.git(root, "add", ".")
    pub.git(root, "commit", "-qm", "source")
    sha = pub.git(root, "rev-parse", "HEAD")
    pub.git(root, "update-ref", "refs/remotes/origin/main", sha)
    monkeypatch.setattr(pub, "ROOT", root)
    monkeypatch.setattr(pub, "checked", lambda repository, commit: True)
    monkeypatch.setattr("sys.argv", ["publication.py", "--repository", "owner/repo"])
    pub.main()
    output = root / ".build/publication"
    info = json.loads((output / "site/dev/build-info.json").read_text())
    package_version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    assert info == {"version": "dev", "ref": "main", "commit": sha, "package_version": package_version}
    html = (output / "site/dev/index.html").read_text()
    assert 'href="https://tsumina.github.io/sciloom/dev/"' in html
    assert '"provider":"mike"' in html
    assert pub.git(root, "status", "--porcelain", "--untracked-files=no") == ""
    # Keep generated history, then simulate a main reset behind its published dev.
    pub.git(root, "fetch", str(output / "history.bundle"), "gh-pages:refs/remotes/origin/gh-pages")
    shutil.rmtree(output)
    pub.git(root, "checkout", "--orphan", "divergent")
    pub.git(root, "commit", "-qm", "unrelated source")
    pub.git(root, "update-ref", "refs/remotes/origin/main", pub.git(root, "rev-parse", "HEAD"))
    with pytest.raises(ValueError, match="stale or divergent"):
        pub.main()
