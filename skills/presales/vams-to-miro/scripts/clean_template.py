#!/usr/bin/env python3
"""
Strip Miro export-only metadata from every item in a template file, in place.

Raw Miro board exports carry per-item bookkeeping (`links`, `createdAt`,
`createdBy`, `modifiedAt`, `modifiedBy`) that's irrelevant once the JSON is
just a layout template — it's noise for anyone reading the file and stale
the moment the board changes again. This trims it down to the geometry/style
data the vams-to-miro scripts actually use.

Usage:
    python3 clean_template.py <template.json> [<template2.json> ...]
    python3 clean_template.py --all [--templates-dir <dir>]

With no arguments, --all scans the bundled templates/ folder (this skill's
templates/) rather than requiring every filename to be spelled out.
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vams_common import resolve_template_path, BUNDLED_TEMPLATES_DIR  # noqa: E402

STRIP_KEYS = ("links", "createdAt", "createdBy", "modifiedAt", "modifiedBy")


def clean_file(path):
    with open(path) as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{os.path.basename(path)}: skipped, not valid JSON ({e})")
            return

    removed = 0
    for item in doc.get("items", []):
        for key in STRIP_KEYS:
            if key in item:
                del item[key]
                removed += 1

    with open(path, "w") as f:
        f.write(json.dumps(doc, indent=4))

    print(f"{os.path.basename(path)}: removed {removed} keys from {len(doc.get('items', []))} items")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template_paths", nargs="*", help="Template file(s) to clean, or just filenames to resolve against the bundled templates/ folder")
    ap.add_argument("--all", action="store_true", help="Clean every *.json file in the templates folder instead of specific files")
    ap.add_argument("--templates-dir", help="Directory to scan for --all (defaults to the bundled templates/ folder)")
    args = ap.parse_args()

    if args.all:
        paths = sorted(glob.glob(os.path.join(args.templates_dir or BUNDLED_TEMPLATES_DIR, "*.json")))
        if not paths:
            raise SystemExit("No *.json files found to clean.")
    elif args.template_paths:
        paths = [resolve_template_path(p) for p in args.template_paths]
    else:
        raise SystemExit("Pass one or more template paths, or --all.")

    for path in paths:
        clean_file(path)


if __name__ == "__main__":
    main()
