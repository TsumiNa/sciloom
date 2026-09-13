"""Build checked source snapshots and package a generated-only mike history.

Run in the read-only publication job, after fetching all source refs. This tool
never pushes or deploys; the separate write-enabled job publishes its artifacts.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import tarfile
import tomllib
from contextlib import chdir
from dataclasses import asdict, dataclass
from pathlib import Path

from mike import commands, git_utils

ROOT = Path(__file__).resolve().parents[2]
RELEASE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
CHECKS = {"docs", "check (3.12)", "check (3.13)", "check (3.14)"}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@dataclass(frozen=True)
class Snapshot:
    version: str
    ref: str
    commit: str
    package_version: str


def release_key(version: str) -> tuple[int, ...]:
    if not RELEASE.fullmatch(version):
        raise ValueError(f"Not a canonical release version: {version}")
    return tuple(map(int, version.split(".")))


def select_snapshots(candidates: list[Snapshot], published: dict[str, dict], passed: set[str]) -> list[Snapshot]:
    """Reconcile every eligible tag, refusing moved releases even before CI passes."""
    selected = []
    for item in candidates:
        if item.version != "dev":
            release_key(item.version)
            if item.ref != "v" + item.version or item.package_version != item.version:
                raise ValueError(f"Tag/package mismatch: {item.ref}")
        elif item.ref != "main":
            raise ValueError("dev must come from main")
        previous = published.get(item.version)
        if previous:
            if item.version != "dev" and previous != asdict(item):
                raise ValueError(f"Refusing to overwrite published release {item.version}")
            if previous == asdict(item):
                continue
        if item.commit in passed:
            selected.append(item)
    return sorted(
        selected, key=lambda item: (item.version == "dev", release_key(item.version) if item.version != "dev" else ())
    )


def checked(repository: str, commit: str) -> bool:
    """Require successful push CI and all expected jobs for this exact source SHA."""

    def pages(endpoint: str) -> list[dict]:
        return json.loads(subprocess.check_output(["gh", "api", "--paginate", "--slurp", endpoint], text=True))

    runs = pages(
        f"repos/{repository}/actions/workflows/ci.yml/runs?event=push&status=success&head_sha={commit}&per_page=100"
    )
    for page in runs:
        for run in page["workflow_runs"]:
            if run["head_sha"] != commit or run["event"] != "push" or run["head_repository"]["full_name"] != repository:
                continue
            jobs = pages(f"repos/{repository}/actions/runs/{run['id']}/jobs?per_page=100")
            successful = {job["name"] for group in jobs for job in group["jobs"] if job["conclusion"] == "success"}
            if CHECKS <= successful:
                return True
    return False


def audit_site(site: Path, expected_examples: tuple[str, ...]) -> None:
    """Reject non-site roots, links and unselected source/evidence downloads."""
    allowed = {
        "404.html",
        "index.html",
        "build-info.json",
        "objects.inv",
        "sitemap.xml",
        "search.json",
        "api",
        "assets",
        "developer",
        "examples",
        "introduction",
        "user-guide",
        "_generated",
    }
    if {p.name for p in site.iterdir()} - allowed:
        raise ValueError("Unexpected content at the public site root")
    downloads = site / "_generated/examples"
    actual = {str(p.relative_to(downloads)) for p in downloads.rglob("*") if p.is_file()}
    if actual != set(expected_examples):
        raise ValueError("Public downloads differ from the source commit's explicit allowlist")
    for path in site.rglob("*"):
        if path.is_symlink():
            raise ValueError("Published sites must not contain symlinks")
        if path.is_file() and path.suffix in {".py", ".asfp", ".app", ".zip"}:
            if path.relative_to(site).parts[:2] != ("_generated", "examples"):
                raise ValueError(f"Unselected source/evidence file: {path}")


def record(storage: Path, site: Path, snapshot: Snapshot, *, expected_examples: tuple[str, ...] = ()) -> None:
    """Store an already-built exact snapshot; only mike's generated branch is used."""
    info = json.loads((site / "build-info.json").read_text())
    if info != asdict(snapshot):
        raise ValueError("Built metadata differs from the selected source snapshot")
    audit_site(site, expected_examples)
    with chdir(storage):
        with commands.deploy(
            {"site_dir": str(site), "use_directory_urls": True},
            snapshot.version,
            alias_type=commands.AliasType.redirect,
            message=f"Documentation {snapshot.version} from {snapshot.commit}",
        ):
            pass  # The source checkout's locked environment already built the site.


def aliases(storage: Path) -> None:
    """Keep stable on the highest release, regardless of event or build order."""
    with chdir(storage):
        versions = json.loads(git(storage, "show", "gh-pages:versions.json"))
        releases = [item["version"] for item in versions if RELEASE.fullmatch(item["version"])]
        if releases:
            latest = max(releases, key=release_key)
            current = next(item for item in versions if item["version"] == latest)
            if "stable" not in current["aliases"]:
                commands.alias(
                    {"use_directory_urls": True},
                    latest,
                    ["stable"],
                    update_aliases=True,
                    alias_type=commands.AliasType.redirect,
                )
        default = "stable" if releases else "dev"
        try:
            commands.set_default(default)
        except git_utils.GitEmptyCommit:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    if git(ROOT, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Publication preparation requires a clean source checkout")
    build = ROOT / "website/.build/publication"
    build.mkdir(parents=True, exist_ok=False)
    storage = build / "history"
    storage.mkdir()
    git(storage, "init", "-q")
    git(storage, "config", "user.name", "SciLoom documentation")
    git(storage, "config", "user.email", "docs@users.noreply.github.com")
    prior = (
        subprocess.run(
            ["git", "-C", str(ROOT), "show-ref", "--verify", "--quiet", "refs/remotes/origin/gh-pages"]
        ).returncode
        == 0
    )
    if prior:
        git(storage, "fetch", str(ROOT), "refs/remotes/origin/gh-pages:refs/heads/gh-pages")
    published = {}
    if prior:
        for item in json.loads(git(storage, "show", "gh-pages:versions.json")):
            name = item["version"]
            if name != "dev":
                release_key(name)
            published[name] = json.loads(git(storage, "show", f"gh-pages:{name}/build-info.json"))

    refs = [
        "main",
        *[ref for ref in git(ROOT, "tag", "--list").splitlines() if ref.startswith("v") and RELEASE.fullmatch(ref[1:])],
    ]
    candidates = []
    for ref in refs:
        revision = "refs/remotes/origin/main" if ref == "main" else f"refs/tags/{ref}"
        commit = git(ROOT, "rev-parse", revision + "^{commit}")
        package = tomllib.loads(git(ROOT, "show", f"{commit}:pyproject.toml"))["project"]["version"]
        candidates.append(Snapshot("dev" if ref == "main" else ref[1:], ref, commit, package))
    passed = {item.commit for item in candidates if checked(args.repository, item.commit)}
    selected = select_snapshots(candidates, published, passed)
    for item in selected:
        if item.version == "dev" and "dev" in published:
            previous = published["dev"]["commit"]
            if subprocess.run(
                ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", previous, item.commit]
            ).returncode:
                raise ValueError("Refusing stale or divergent dev history")
        checkout = build / item.version
        git(ROOT, "worktree", "add", "--detach", str(checkout), item.commit)
        try:
            env = dict(os.environ)
            for key in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "GH_TOKEN", "GITHUB_TOKEN", "SCILOOM_DOCS_PR_NUMBER"):
                env.pop(key, None)
            subprocess.run(
                ["uv", "sync", "--locked", "--group", "docs", "--python", "3.14"], cwd=checkout, env=env, check=True
            )
            subprocess.run(
                [
                    "uv",
                    "run",
                    "--no-sync",
                    "--group",
                    "docs",
                    "python",
                    "website/tools/site.py",
                    "build",
                    "--strict",
                    "--publish-ref",
                    item.ref,
                ],
                cwd=checkout,
                env=env,
                check=True,
            )
            if git(checkout, "status", "--porcelain", "--untracked-files=no"):
                raise ValueError("A version build modified tracked source files")
            source = ast.parse((checkout / "website/tools/site.py").read_text())
            expected_examples = next(
                ast.literal_eval(node.value)
                for node in source.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "EXAMPLES" for t in node.targets)
            )
            record(storage, checkout / "website/.build/site", item, expected_examples=expected_examples)
        finally:
            git(ROOT, "worktree", "remove", "--force", str(checkout))
    if not selected and not prior:
        raise ValueError("No checked source snapshots are eligible for publication")
    aliases(storage)
    git(storage, "bundle", "create", str(build / "history.bundle"), "gh-pages")
    archive = build / "site.tar"
    git(storage, "archive", "--format=tar", f"--output={archive}", "gh-pages")
    with tarfile.open(archive) as tar:
        tar.extractall(build / "site", filter="data")
    print("Prepared checked documentation history and Pages artifact")


if __name__ == "__main__":
    main()
