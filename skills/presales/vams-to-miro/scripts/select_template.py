#!/usr/bin/env python3
"""
Rank candidate layout templates against an existing VAMS document, so a
template can be auto-selected instead of asked for — used when the user
already has a VAMS JSON and just wants it drawn.

Scores every usable frame across the given template file(s) by how many of
its TOP-LEVEL regions actually match, using the SAME hierarchy-scoped
matching generate_layout_dsl.py itself uses (not an independent name-overlap
heuristic — that used to drift out of sync with what generation actually
does, e.g. counting a match against any node with the right name instead of
only real VAMS roots, which the generator mandates for top-level regions).
Total-region match count is the tie-breaker. Identical template files
(byte-for-byte, e.g. a "_bkp" copy) are deduplicated so they don't show up
twice.

Usage:
    python3 select_template.py <vams.json> --templates-dir <dir>
    python3 select_template.py <vams.json> <template1.json> [<template2.json> ...]

Prints a JSON array to stdout, best match first. This only ranks — it never
picks silently on the caller's behalf without the score being visible; always
show the top candidate's score/matched names to the user before proceeding.
"""

import argparse
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vams_common import (  # noqa: E402
    find_usable_frames, build_region_tree, flatten_regions_preorder, load_vams,
    unwrap_export_envelope, detect_frame_wrapper_root, unwrap_frame_wrapper_root,
)
from generate_layout_dsl import place_on_template, load_shape_mappings  # noqa: E402


def candidate_template_files(explicit_paths, templates_dir):
    paths = list(explicit_paths)
    if templates_dir:
        paths.extend(sorted(glob.glob(os.path.join(templates_dir, "*.json"))))

    seen_hashes = set()
    deduped = []
    for p in paths:
        with open(p, "rb") as f:
            content = f.read()
        h = hashlib.sha256(content).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        deduped.append(p)
    return deduped


def score_frame(nodes, children_by_parent, roots, region_roots, shape_mappings):
    top_level = region_roots
    all_regions = flatten_regions_preorder(region_roots)

    # Run the real matcher — same rules generation will actually apply
    # (only VAMS roots can match a top-level region, by name or by a
    # type/environment classification fallback; nested regions are scoped
    # strictly to real descendants, same two-signal matching, no
    # cross-branch fallback ever).
    place_on_template(nodes, children_by_parent, roots, region_roots, shape_mappings)

    top_matched = [r.name for r in top_level if r.matched_node_id is not None]
    top_unmatched = [r.name for r in top_level if r.matched_node_id is None]
    all_matched_count = sum(1 for r in all_regions if r.matched_node_id is not None)

    return {
        "top_level_total": len(top_level),
        "top_level_matched": len(top_matched),
        "top_level_matched_names": top_matched,
        "top_level_unmatched_names": top_unmatched,
        "total_regions": len(all_regions),
        "total_regions_matched": all_matched_count,
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_templates_dir = os.path.join(script_dir, "..", "templates")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vams_path")
    ap.add_argument("template_paths", nargs="*")
    ap.add_argument(
        "--templates-dir",
        help="Directory to glob *.json template files from. Defaults to the "
             "templates/ folder bundled with this skill; pass this to use an "
             "external/shared template library instead.",
    )
    args = ap.parse_args()

    templates_dir = args.templates_dir
    if not templates_dir and not args.template_paths:
        templates_dir = bundled_templates_dir

    template_files = candidate_template_files(args.template_paths, templates_dir)
    if not template_files:
        raise SystemExit(
            "No template files found (looked in "
            f"{templates_dir or '(none given)'}). Pass explicit paths and/or --templates-dir."
        )

    with open(args.vams_path) as f:
        vams_doc = unwrap_export_envelope(json.load(f))
    nodes, children_by_parent, roots, _data_entities, _flows = load_vams(vams_doc)

    # Same frame-wrapper detection generate_layout_dsl.py applies — without
    # it, a document exported from the existing Miro->VAMS importer would
    # always score 0 here (everything sits one level below its own
    # artifact wrapper), misleadingly suggesting no template fits.
    frame_wrapper_id = detect_frame_wrapper_root(vams_doc, nodes, roots)
    if frame_wrapper_id:
        nodes, children_by_parent, roots = unwrap_frame_wrapper_root(
            nodes, children_by_parent, roots, frame_wrapper_id
        )

    shape_mapping_path = os.path.join(script_dir, "..", "references", "vams-miro-shape-mapping.json")
    shape_mappings = load_shape_mappings(shape_mapping_path)

    candidates = []
    for path in template_files:
        with open(path) as f:
            template_doc = json.load(f)
        for frame_item in find_usable_frames(template_doc):
            region_roots, frame_w, frame_h = build_region_tree(template_doc, frame_item)
            score = score_frame(nodes, children_by_parent, roots, region_roots, shape_mappings)
            candidates.append({
                "template_file": path,
                "frame": frame_item.get("data", {}).get("title", ""),
                **score,
            })

    candidates.sort(
        key=lambda c: (c["top_level_matched"], c["total_regions_matched"]),
        reverse=True,
    )

    for i, c in enumerate(candidates):
        c["rank"] = i + 1

    print(json.dumps(candidates, indent=2))


if __name__ == "__main__":
    main()
