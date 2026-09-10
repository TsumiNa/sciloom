#!/usr/bin/env python3
"""Verify the organized AutoSuite references; never rewrite XML evidence.

Use --write-manifest after intentional reference updates to record current
hashes and the mapping from original archive entries to unique expanded files.
"""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_rows(path, fields, records):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def tree(element):
    text = element.text
    if len(element) and (text is None or not text.strip()):
        text = None
    tail = element.tail if element.tail and element.tail.strip() else None
    return (element.tag, sorted(element.attrib.items()), text, tail,
            tuple(tree(child) for child in element))


def check(condition, message):
    if not condition:
        raise ValueError(message)


def archives_and_catalogs():
    members = []
    for kind, expected in (("app", 68), ("asfp", 58)):
        files = sorted((BASE / kind).glob(f"*.{kind}"))
        check(len(files) == expected, f"Unexpected {kind} reference count")
        by_hash = {}
        for path in files:
            raw = path.read_bytes()
            key = digest(raw)
            check(key not in by_hash, f"Duplicate expanded {kind}: {path}")
            by_hash[key] = path.relative_to(BASE).as_posix()
            root = ET.fromstring(gzip.decompress(raw) if kind == "app" else raw)
            check(root.tag == ("application" if kind == "app" else "functions"),
                  f"Unexpected XML root: {path}")
        archive_path = BASE / "archives" / f"{kind}_type_files.zip"
        matched = set()
        with zipfile.ZipFile(archive_path) as archive:
            for member in sorted(archive.namelist()):
                if not member.endswith(f".{kind}"):
                    continue
                raw = archive.read(member)
                key = digest(raw)
                check(key in by_hash, f"Archive member is not preserved: {member}")
                matched.add(key)
                members.append({"archive": archive_path.relative_to(BASE).as_posix(),
                                "member": member, "path": by_hash[key],
                                "bytes": str(len(raw)), "sha256": key})
        check(matched == set(by_hash), f"Expanded {kind} files lack original archive evidence")
        catalog_path = BASE / "catalogs" / f"{kind}_catalog"
        catalog = json.loads(catalog_path.with_suffix(".json").read_text())
        csv_catalog = rows(catalog_path.with_suffix(".csv"))
        check(len(catalog) == len(files) == len(csv_catalog), f"{kind} catalog count mismatch")
        for entries in (catalog, csv_catalog):
            check({r["file"] for r in entries} == {p.name for p in files},
                  f"{kind} catalog filenames differ")
            for record in entries:
                raw = (BASE / kind / record["file"]).read_bytes()
                check(digest(raw) == record["sha256"] and len(raw) == int(record["bytes"]),
                      f"Catalog hash/size differs: {record['file']}")
    check(len(members) == 127, "Expected 68 APP and 59 ASFP archive entries")
    return members


def derived_references():
    app = BASE / "app/config20260909_polymerization.app"
    raw_app = app.read_bytes()
    xml = gzip.decompress(raw_app)
    extracted = BASE / "extracted/latest_app"
    check(xml == (extracted / "application.xml").read_bytes(), "Decompressed APP differs")
    functions = ET.fromstring(xml).findall("./functions/functions/function")
    packages = sorted((extracted / "functions").glob("*.asfp"))
    index = rows(extracted / "function_index.csv")
    check(len(functions) == len(packages) == len(index) == 52, "Function counts differ")
    sources = []
    for number, (source, path, record) in enumerate(zip(functions, packages, index)):
        root = ET.parse(path).getroot()
        check(root.tag == "functions" and len(root) == 1, f"Not a single-function package: {path}")
        check(int(path.name.split("_", 1)[0]) == number == int(record["index"]),
              f"Function index mismatch: {path}")
        check(source.findtext("id") == record["id"] and tree(root[0]) == tree(source),
              f"Function XML or ID differs from application: {path}")
        sources.append({
            "path": path.relative_to(BASE).as_posix(),
            "sha256": digest(path.read_bytes()),
            "reference_app": app.relative_to(BASE).as_posix(),
            "reference_app_sha256": digest(raw_app),
            "app_xpath": f"/application/functions/functions/function[{number + 1}]",
            "function_id": source.findtext("id"),
            "name": record["name"],
            "typeid": source.get("typeid"),
            "eventtype": source.findtext("eventtype") or "",
            "xml_tree_match": "true",
        })
    templates = rows(BASE / "schema/type_templates/INDEX.csv")
    check(len(templates) == 67, "Expected 67 representative templates")
    for record in templates:
        check((BASE / record["representative_source"]).is_file(), "Template source missing")
        root = ET.parse(BASE / "schema/type_templates" / record["representative_fragment"]).getroot()
        check(root.get("typeid") == record["typeid"], "Template typeid mismatch")
    for record in rows(BASE / "catalogs/relocation.csv"):
        path = BASE / record["path"]
        check(digest(path.read_bytes()) == record["sha256"], f"Relocated evidence changed: {path}")
    return sources


def inventory():
    records = []
    for path in sorted(BASE.rglob("*")):
        if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(BASE).parts):
            continue
        check(not path.is_symlink(), f"Unexpected symlink: {path}")
        if not path.is_file() or path == BASE / "MANIFEST.csv":
            continue
        check(path.suffix not in {".aspy", ".aspyview", ".appview"}, f"Retired format: {path}")
        raw = path.read_bytes()
        records.append({"path": path.relative_to(BASE).as_posix(),
                        "bytes": str(len(raw)), "sha256": digest(raw)})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    members = archives_and_catalogs()
    sources = derived_references()
    mapping = BASE / "catalogs/archive_members.csv"
    function_mapping = BASE / "extracted/latest_app/function_sources.csv"
    if args.write_manifest:
        write_rows(mapping, ["archive", "member", "path", "bytes", "sha256"], members)
        write_rows(function_mapping, list(sources[0]), sources)
        write_rows(BASE / "MANIFEST.csv", ["path", "bytes", "sha256"], inventory())
    else:
        check(rows(mapping) == members, "Archive mapping differs")
        check(rows(function_mapping) == sources, "Function-to-application mapping differs")
        check(rows(BASE / "MANIFEST.csv") == inventory(), "Reference manifest differs; review changes before updating")
    print("AUTOSUITE AUDIT: OK — 68 APP, 58 ASFP, 127 archive entries, 52 function XML matches, 67 templates")


if __name__ == "__main__":
    main()
