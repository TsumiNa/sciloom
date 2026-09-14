#!/usr/bin/env python3
"""Check a received AutoSuite corpus; never rewrite XML evidence.

The corpus under ../corpus/ is shared inside the team and is not in git, so two
developers hold different files. Nothing here asserts a fixed count: each section
runs only when the material it needs is present, and the recorded CSVs detect a
file whose content changed, not a corpus that grew.

Use --write-manifest after intentionally adding or updating references.
"""

import argparse
import csv
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE / "corpus"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_rows(path, fields, records):
    with path.open("w", newline="\n", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def tree(element):
    text = element.text
    if len(element) and (text is None or not text.strip()):
        text = None
    tail = element.tail if element.tail and element.tail.strip() else None
    return (element.tag, sorted(element.attrib.items()), text, tail, tuple(tree(child) for child in element))


def check(condition, message):
    if not condition:
        raise ValueError(message)


def compare(recorded, current, key):
    """Fail on a changed file; report growth and removal as facts, not errors."""
    was = {key(record): record for record in recorded}
    now = {key(record): record for record in current}
    changed = sorted(name for name in was.keys() & now.keys() if was[name] != now[name])
    check(not changed, f"Recorded evidence changed: {', '.join(changed[:5])}")
    return sorted(now.keys() - was.keys()), sorted(was.keys() - now.keys())


def archives_and_catalogs():
    members = []
    for kind in ("app", "asfp"):
        files = sorted((CORPUS / kind).glob(f"*.{kind}")) if (CORPUS / kind).is_dir() else []
        by_hash = {}
        for path in files:
            raw = path.read_bytes()
            key = digest(raw)
            check(key not in by_hash, f"Duplicate expanded {kind}: {path}")
            by_hash[key] = path.relative_to(CORPUS).as_posix()
            root = ET.fromstring(gzip.decompress(raw) if kind == "app" else raw)
            check(root.tag == ("application" if kind == "app" else "functions"), f"Unexpected XML root: {path}")
        archive_path = CORPUS / "archives" / f"{kind}_type_files.zip"
        if archive_path.is_file():
            with zipfile.ZipFile(archive_path) as archive:
                for member in sorted(archive.namelist()):
                    if not member.endswith(f".{kind}"):
                        continue
                    raw = archive.read(member)
                    key = digest(raw)
                    check(key in by_hash, f"Archive member is not preserved: {member}")
                    members.append(
                        {
                            "archive": archive_path.relative_to(CORPUS).as_posix(),
                            "member": member,
                            "path": by_hash[key],
                            "bytes": str(len(raw)),
                            "sha256": key,
                        }
                    )
        catalog_path = CORPUS / "catalogs" / f"{kind}_catalog"
        if not catalog_path.with_suffix(".json").is_file():
            continue
        catalog = json.loads(catalog_path.with_suffix(".json").read_text())
        csv_catalog = rows(catalog_path.with_suffix(".csv"))
        check(len(catalog) == len(csv_catalog), f"{kind} catalog count mismatch")
        for entries in (catalog, csv_catalog):
            for record in entries:
                path = CORPUS / kind / record["file"]
                if not path.is_file():
                    continue
                raw = path.read_bytes()
                check(
                    digest(raw) == record["sha256"] and len(raw) == int(record["bytes"]),
                    f"Catalog hash/size differs: {record['file']}",
                )
    return members


def derived_references():
    app = CORPUS / "app/config20260909_polymerization.app"
    extracted = CORPUS / "extracted/latest_app"
    if not (app.is_file() and (extracted / "application.xml").is_file()):
        return []
    raw_app = app.read_bytes()
    xml = gzip.decompress(raw_app)
    check(xml == (extracted / "application.xml").read_bytes(), "Decompressed APP differs")
    functions = ET.fromstring(xml).findall("./functions/functions/function")
    packages = sorted((extracted / "functions").glob("*.asfp"))
    index = rows(extracted / "function_index.csv")
    check(len(functions) == len(packages) == len(index), "Function counts differ")
    sources = []
    for number, (source, path, record) in enumerate(zip(functions, packages, index)):
        root = ET.parse(path).getroot()
        check(root.tag == "functions" and len(root) == 1, f"Not a single-function package: {path}")
        check(int(path.name.split("_", 1)[0]) == number == int(record["index"]), f"Function index mismatch: {path}")
        check(
            source.findtext("id") == record["id"] and tree(root[0]) == tree(source),
            f"Function XML or ID differs from application: {path}",
        )
        sources.append(
            {
                "path": path.relative_to(CORPUS).as_posix(),
                "sha256": digest(path.read_bytes()),
                "reference_app": app.relative_to(CORPUS).as_posix(),
                "reference_app_sha256": digest(raw_app),
                "app_xpath": f"/application/functions/functions/function[{number + 1}]",
                "function_id": source.findtext("id"),
                "name": record["name"],
                "typeid": source.get("typeid"),
                "eventtype": source.findtext("eventtype") or "",
                "xml_tree_match": "true",
            }
        )
    return sources


def templates_and_relocations():
    index = CORPUS / "type_templates/INDEX.csv"
    count = 0
    if index.is_file():
        for record in rows(index):
            check((CORPUS / record["representative_source"]).is_file(), "Template source missing")
            root = ET.parse(CORPUS / "type_templates" / record["representative_fragment"]).getroot()
            check(root.get("typeid") == record["typeid"], "Template typeid mismatch")
            count += 1
    relocation = CORPUS / "catalogs/relocation.csv"
    if relocation.is_file():
        for record in rows(relocation):
            path = CORPUS / record["path"]
            if path.is_file():
                check(digest(path.read_bytes()) == record["sha256"], f"Relocated evidence changed: {path}")
    return count


def inventory():
    records = []
    for path in sorted(CORPUS.rglob("*")):
        if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(CORPUS).parts):
            continue
        check(not path.is_symlink(), f"Unexpected symlink: {path}")
        if not path.is_file() or path == CORPUS / "MANIFEST.csv":
            continue
        check(path.suffix not in {".aspy", ".aspyview", ".appview"}, f"Retired format: {path}")
        raw = path.read_bytes()
        records.append({"path": path.relative_to(CORPUS).as_posix(), "bytes": str(len(raw)), "sha256": digest(raw)})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if not CORPUS.is_dir():
        print(f"AUTOSUITE AUDIT: skipped — no corpus at {CORPUS}; see autosuite/README.md")
        return
    members = archives_and_catalogs()
    sources = derived_references()
    templates = templates_and_relocations()
    mapping = CORPUS / "catalogs/archive_members.csv"
    function_mapping = CORPUS / "extracted/latest_app/function_sources.csv"
    manifest = CORPUS / "MANIFEST.csv"
    if args.write_manifest:
        if members:
            write_rows(mapping, ["archive", "member", "path", "bytes", "sha256"], members)
        if sources:
            write_rows(function_mapping, list(sources[0]), sources)
        # Take the inventory after those two writes, so the manifest records the
        # catalogs as they now stand and a following audit is clean.
        files = inventory()
        write_rows(manifest, ["path", "bytes", "sha256"], files)
        added, removed = [], []
    else:
        files = inventory()
        if mapping.is_file():
            compare(rows(mapping), members, lambda record: (record["archive"], record["member"]))
        if function_mapping.is_file() and sources:
            compare(rows(function_mapping), sources, lambda record: record["path"])
        recorded = rows(manifest) if manifest.is_file() else []
        added, removed = compare(recorded, files, lambda record: record["path"])
    drift = f", {len(added)} new, {len(removed)} missing" if added or removed else ""
    print(
        f"AUTOSUITE AUDIT: OK — {len(files)} files, {len(members)} archive entries, "
        f"{len(sources)} function XML matches, {templates} templates{drift}"
    )
    if added or removed:
        print("Run --write-manifest to record the current corpus.", file=sys.stderr)


if __name__ == "__main__":
    main()
