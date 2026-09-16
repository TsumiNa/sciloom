"""Prepare public documentation assets, stamp their source, and invoke Zensical."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# No recursive repository copy: additions to the public downloads are deliberate.
EXAMPLES = (
    "tutorial/start_shaker.py",
    "tutorial/start_shaker.asfp",
    "tutorial/control_shaker.py",
    "tutorial/control_shaker.asfp",
    "tutorial/choose_stirring_speed.py",
    "tutorial/choose_stirring_speed.asfp",
    "tutorial/stir_sample_rack.py",
    "tutorial/stir_sample_rack.asfp",
    "function_call.py",
    "function_call.asfp",
    "agitation.py",
    "agitation.asfp",
    "scale_values.py",
    "scale_values.asfp",
    "prepare_labels.py",
    "prepare_labels.asfp",
    "quantity_conversion.py",
    "quantity_conversion.asfp",
    "numeric_operations.py",
    "numeric_operations.asfp",
    "confirm_samples.py",
    "confirm_samples.asfp",
    "timestamp_path.py",
    "timestamp_path.asfp",
    "timed_agitation.py",
    "timed_agitation.asfp",
    "read_reagent_table.py",
    "read_reagent_table.csv",
    "developer/csv_read_ir.py",
    "developer/csv_read_ir.json",
    "append_sample_log.py",
    "developer/csv_append_ir.py",
    "developer/csv_append_ir.json",
    "resolve_locations.py",
    "resolve_locations.asfp",
    "developer/zone_ir.py",
    "developer/zone_ir.json",
    "visit_locations.py",
    "visit_locations.asfp",
    "developer/zone_traversal_ir.py",
    "developer/zone_traversal_ir.json",
    "record_values.py",
    "record_values.asfp",
    "non_zero_array_min.py",
    "non_zero_array_min.asfp",
    "stir_rack.py",
    "stir_rack.asfp",
    "developer/agitation_ir.py",
    "developer/agitation_ir.json",
    "developer/list_ir.py",
    "developer/list_ir.json",
    "developer/reference_environment.py",
    "developer/confirmation_ir.py",
    "developer/confirmation_ir.json",
    "developer/wall_time_ir.py",
    "developer/wall_time_ir.json",
    "developer/timing_ir.py",
    "developer/timing_ir.json",
    "developer/logging_ir.py",
    "developer/logging_ir.json",
    "developer/demo_device.py",
    "developer/demo_device.json",
    "developer/demo_contribution/__init__.py",
    "developer/source_paths.py",
    "developer/portable_agitation.py",
    "developer/portable_agitation.json",
    "developer/portable_agitation.autosuite.asfp",
    "developer/portable_agitation.demo.json",
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def package_version(root: Path) -> str:
    """Return the version shared by the root project and every uv workspace member."""
    config = tomllib.loads((root / "pyproject.toml").read_text())
    version = config["project"]["version"]
    for pattern in config.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", ()):
        for member in sorted(root.glob(pattern)):
            project = tomllib.loads((member / "pyproject.toml").read_text())["project"]
            if project["version"] != version:
                raise ValueError(
                    "Workspace members must share the root version: "
                    f"{project['name']} is {project['version']}, root is {version}"
                )
    return version


def source_info(root: Path, *, preview: str | None = None, publish_ref: str | None = None) -> dict[str, str]:
    """Identify this checkout, never a separately installed SciLoom distribution."""
    package = package_version(root)
    commit = git(root, "rev-parse", "HEAD")
    dirty = bool(git(root, "status", "--porcelain", "--untracked-files=no"))
    if publish_ref:
        if preview or dirty:
            raise ValueError("Published documentation requires a clean, non-PR checkout")
        ref = publish_ref
        if ref == "main":
            version = "dev"
            expected = git(root, "rev-parse", "refs/remotes/origin/main")
        elif re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", ref):
            version = ref[1:]
            if package != version:
                raise ValueError("Release tag must match the source package version")
            expected = git(root, "rev-parse", f"refs/tags/{ref}^{{commit}}")
        else:
            raise ValueError("Publish only main or vMAJOR.MINOR.PATCH")
        if expected != commit:
            raise ValueError("Published ref does not identify this source commit")
    elif preview:
        if not preview.isdecimal():
            raise ValueError("preview must be a pull request number")
        version, ref = "preview", f"refs/pull/{preview}/head"
        if dirty:
            raise ValueError("PR previews require a clean checkout")
    else:
        version = "local-dirty" if dirty else "local"
        ref = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return {"version": version, "ref": ref, "commit": commit, "package_version": package}


def prepare(root: Path, info: dict[str, str]) -> None:
    """Copy only selected learning assets; leave all source files unchanged."""
    public = root / "website/docs"
    generated = public / "_generated"
    metadata = public / "build-info.json"
    if public.resolve() != root.resolve() / "website/docs" or metadata.is_symlink():
        raise ValueError("public documentation and metadata must not be symlinks")
    if generated.is_symlink():
        raise ValueError("generated documentation directory must not be a symlink")
    if generated.exists():
        shutil.rmtree(generated)
    for name in EXAMPLES:
        source = root / "examples" / name
        if source.resolve() != root.resolve() / "examples" / name:
            raise ValueError(f"example escapes the publication allowlist: {name}")
        destination = generated / "examples" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    metadata.write_text(json.dumps(info, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("serve", "build"))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--preview",
        default=os.environ.get("SCILOOM_DOCS_PR_NUMBER"),
        help="Stamp a clean PR head checkout with its PR number",
    )
    parser.add_argument("--publish-ref", help="Stamp an exact main/release checkout for publication")
    args = parser.parse_args()
    if args.publish_ref and args.command != "build":
        parser.error("--publish-ref is only valid for build")
    info = source_info(ROOT, preview=args.preview, publish_ref=args.publish_ref)
    prepare(ROOT, info)
    env = dict(os.environ)
    for key, value in info.items():
        env[f"SCILOOM_DOCS_{key.upper()}"] = value
    if args.publish_ref:
        env["MIKE_DOCS_VERSION"] = info["version"]
    else:
        env.pop("MIKE_DOCS_VERSION", None)
    command = [sys.executable, "-m", "zensical", args.command, "-f", "mkdocs.yml"]
    if args.strict:
        command.append("--strict")
    subprocess.run(command, cwd=ROOT / "website", env=env, check=True)


if __name__ == "__main__":
    main()
