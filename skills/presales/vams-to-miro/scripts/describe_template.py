#!/usr/bin/env python3
"""
Print a human-readable outline of a template frame's groups and slots — used
in the "from scratch" flow, where the user picks a template *before* a VAMS
document exists, so there's nothing yet to auto-match against. Showing this
outline lets the user (or Claude, on their behalf) see exactly what's
pre-positioned and name their real nodes to match it.

Usage:
    python3 describe_template.py <template.json> [--frame "Basic B2B"] [--json]
    python3 describe_template.py --list [--templates-dir <dir>]

With no --frame and more than one candidate template frame in the file,
lists the candidates instead (same as generate_layout_dsl.py's behavior).
--list scans every *.json file in the templates folder (bundled with this
skill by default) and prints every usable frame across all of them — use
this to show the user their options before they pick one (Mode B, step 1).
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vams_common import (  # noqa: E402
    find_template_frame, find_usable_frames, build_region_tree, resolve_template_path,
    BUNDLED_TEMPLATES_DIR,
)


def list_templates(templates_dir):
    for path in sorted(glob.glob(os.path.join(templates_dir, "*.json"))):
        try:
            with open(path) as f:
                template_doc = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for frame_item in find_usable_frames(template_doc):
            roots, w, h = build_region_tree(template_doc, frame_item)
            title = frame_item.get("data", {}).get("title", "")
            print(f'{os.path.basename(path)}  ::  "{title}"  ({w:.0f} x {h:.0f}, {len(roots)} top-level groups/slots)')


def region_to_dict(r):
    return {
        "name": r.name,
        "kind": "group" if not r.is_leaf else "slot",
        "children": [region_to_dict(c) for c in r.children],
    }


def print_outline(roots, indent=0):
    for r in roots:
        kind = "group" if not r.is_leaf else "slot"
        print("  " * indent + f"- {r.name}  [{kind}]")
        print_outline(r.children, indent + 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("template_path", nargs="?", help="Path to a template file, or just its filename to use the bundled templates/ folder")
    ap.add_argument("--frame", help="Title of the template frame to describe")
    ap.add_argument("--json", action="store_true", help="Print JSON instead of a text outline")
    ap.add_argument("--list", action="store_true", help="List every usable frame across all template files instead of describing one")
    ap.add_argument("--templates-dir", help="Directory to scan for --list (defaults to the bundled templates/ folder)")
    args = ap.parse_args()

    if args.list:
        list_templates(args.templates_dir or BUNDLED_TEMPLATES_DIR)
        return

    if not args.template_path:
        raise SystemExit("template_path is required unless --list is given.")

    with open(resolve_template_path(args.template_path)) as f:
        template_doc = json.load(f)

    if not args.frame:
        usable = find_usable_frames(template_doc)
        if len(usable) > 1:
            titles = [f.get("data", {}).get("title", "") for f in usable]
            raise SystemExit(f"Multiple candidate template frames; pass --frame to pick one: {titles}")

    frame_item = find_template_frame(template_doc, args.frame)
    roots, frame_w, frame_h = build_region_tree(template_doc, frame_item)

    if args.json:
        print(json.dumps({
            "frame": frame_item.get("data", {}).get("title", ""),
            "size": {"w": frame_w, "h": frame_h},
            "regions": [region_to_dict(r) for r in roots],
        }, indent=2))
        return

    print(f'Template frame: "{frame_item.get("data", {}).get("title", "")}"  ({frame_w:.0f} x {frame_h:.0f})')
    print()
    print_outline(roots)
    print()
    print(
        "Groups (marked [group]) accept any real node with a matching name — its own\n"
        "children then fill the group's [slot] entries the same way. Slots (marked\n"
        "[slot]) are single fixed positions for one specific expected node. Anything\n"
        "you name differently, or add beyond what's listed here, still gets drawn —\n"
        "it's placed in an auto-laid-out section below the template instead of a\n"
        "pre-designed spot."
    )


if __name__ == "__main__":
    main()
