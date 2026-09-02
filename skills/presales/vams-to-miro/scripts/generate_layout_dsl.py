#!/usr/bin/env python3
"""
Generate Miro `layout_create` DSL text from a VAMS architecture document plus
a predefined layout template (a raw Miro board JSON export).

The template is a POSITIONING GUIDE, not a restriction: any VAMS node whose
name matches a predefined slot/group snaps to that exact spot. Everything
else — new groups, platforms, components, whole subsystems the template
never anticipated — is still drawn in full, with its own real parent/child
hierarchy preserved (not flattened). Two hard rules this script enforces:

  1. A node's children are always rendered nested WITHIN that node's own
     box, never shipped off elsewhere disconnected from their real parent.
     If a template-matched group's real VAMS children outnumber its
     predefined slots, the group's box grows (taller) to fit the rest
     underneath the existing slots, instead of exiling them to a separate
     section.
  2. Growing a box must not make it overlap a sibling positioned below it
     in the same horizontal band — a compaction pass pushes any such
     sibling (and everything nested inside it) down to clear the new size.

Anything with no template-matched ancestor at all becomes its own labeled,
self-contained new group further down the board, sized to its own content.

Nothing is ever silently dropped: this script asserts that every node ends
up placed somewhere, and fails loudly if that invariant is ever violated.

No third-party dependencies (stdlib only) so it runs anywhere Python 3 runs.

Usage:
    python3 generate_layout_dsl.py <vams.json> <template.json> \
        [--frame "Basic B2B"] [--title "Board title"] \
        [--out out.dsl] [--report report.json]

Prints the DSL to stdout (or --out) and a JSON report to stderr (or --report)
describing what was snapped to a predefined slot/group vs. auto-placed
(nested under a real parent, or as a brand-new top-level group), and any
flow whose origin/destination id doesn't exist in the document at all.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vams_common import (  # noqa: E402
    norm, sanitize_id, dsl_escape, resolve_template_path,
    find_template_frame, build_region_tree, flatten_regions_preorder, load_vams,
    infer_region_classification, node_matches_classification, unwrap_export_envelope,
    detect_frame_wrapper_root, unwrap_frame_wrapper_root,
)

GAP = 24            # px gap between auto-laid-out cells
GROUP_HEADER_H = 40  # reserved height for a group/section's own label
MIN_CELL_W = 220
MIN_CELL_H = 90
DEFAULT_CELL_W = 320
DEFAULT_CELL_H = 120


# --------------------------------------------------------------------------
# Shape / connector style mapping (VAMS -> DSL attrs)
# --------------------------------------------------------------------------

def load_shape_mappings(path):
    with open(path) as f:
        return json.load(f)["mappings"]


def load_connector_mappings(path):
    with open(path) as f:
        return json.load(f)["mappings"]


def match_shape_style(node, mappings):
    ntype = node.get("type")
    env = node.get("environment")
    impl = node.get("implementation")
    for m in mappings:
        v = m["vams"]
        if v["type"] != ntype:
            continue
        if v["environment"] != "*" and v["environment"] != env:
            continue
        if v["implementation"] != "*" and v["implementation"] != impl:
            continue
        return m["miro"]
    # Fallback: plain rectangle, neutral gray border.
    return {"data": {"shape": "rectangle"}, "style": {
        "fillColor": "#ffffff", "fillOpacity": "1.0",
        "borderColor": "#595959", "borderStyle": "normal",
    }}


def shape_dsl_attrs(miro_style):
    data = miro_style.get("data", {})
    style = miro_style.get("style", {})
    attrs = {"type": data.get("shape", "rectangle")}
    if "fillColor" in style:
        attrs["fill"] = style["fillColor"]
    if "fillOpacity" in style:
        attrs["fill_opacity"] = style["fillOpacity"]
    if "borderColor" in style:
        attrs["border_color"] = style["borderColor"]
    if "borderStyle" in style:
        # DSL only knows normal/dashed/dotted.
        bstyle = style["borderStyle"]
        attrs["border_style"] = bstyle if bstyle in ("normal", "dashed", "dotted") else "normal"
    if "color" in style:
        attrs["color"] = style["color"]
    return attrs


def match_connector_style(flow, mappings):
    ftype = flow.get("type", "Data")
    timing = flow.get("timing", "Async")
    for m in mappings:
        v = m["vams"]
        if v["type"] == ftype and v["timing"] == timing:
            return m["miro"]["style"]
    return {"strokeStyle": "normal", "strokeColor": "#333333",
            "startStrokeCap": "none", "endStrokeCap": "rounded_stealth"}


def connector_dsl_attrs(miro_style):
    attrs = {}
    if "strokeColor" in miro_style:
        attrs["stroke_color"] = miro_style["strokeColor"]
    if "strokeStyle" in miro_style:
        attrs["stroke_style"] = miro_style["strokeStyle"]
    if "startStrokeCap" in miro_style:
        attrs["start_cap"] = miro_style["startStrokeCap"]
    if "endStrokeCap" in miro_style:
        attrs["end_cap"] = miro_style["endStrokeCap"]
    return attrs


# --------------------------------------------------------------------------
# Shared helpers for recursive natural-size packing (used both for growing a
# template-matched group's box, and for laying out a brand-new group with no
# template anchor at all).
# --------------------------------------------------------------------------

def collect_all_descendants(node_id, children_by_parent):
    out = []
    stack = [node_id]
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(children_by_parent.get(cur, []))
    return out


def compute_natural_size(node_id, children_by_parent, memo):
    """Bottom-up: the (w, h) box a node's whole (unplaced) subtree needs,
    recursively sized to fit a near-square grid of its children's own
    natural sizes."""
    if node_id in memo:
        return memo[node_id]

    children = children_by_parent.get(node_id, [])
    if not children:
        size = (DEFAULT_CELL_W, DEFAULT_CELL_H)
    else:
        child_sizes = [compute_natural_size(c, children_by_parent, memo) for c in children]
        cell_w = max(w for w, h in child_sizes)
        cell_h = max(h for w, h in child_sizes)
        n = len(children)
        cols = max(1, round(n ** 0.5))
        rows = (n + cols - 1) // cols
        inner_w = cols * cell_w + (cols - 1) * GAP
        inner_h = rows * cell_h + (rows - 1) * GAP
        size = (max(inner_w + 2 * GAP, MIN_CELL_W), inner_h + 2 * GAP + GROUP_HEADER_H)

    memo[node_id] = size
    return size


def place_auto_subtree(node_id, children_by_parent, x, y, sizes, out_placed):
    """Top-down: assign (x, y, w, h) to node_id and recursively to its whole
    subtree, using the sizes computed by compute_natural_size. Every
    descendant ends up with an absolute box strictly inside its parent's."""
    w, h = sizes[node_id]
    children = children_by_parent.get(node_id, [])
    out_placed[node_id] = (x, y, w, h, "auto-group" if children else "auto-leaf")

    if not children:
        return

    child_sizes = [sizes[c] for c in children]
    cell_w = max(cw for cw, _ in child_sizes)
    cell_h = max(ch for _, ch in child_sizes)
    n = len(children)
    cols = max(1, round(n ** 0.5))
    inner_x, inner_y = x + GAP, y + GROUP_HEADER_H + GAP

    for i, c in enumerate(children):
        row, col = divmod(i, cols)
        cx = inner_x + col * (cell_w + GAP)
        cy = inner_y + row * (cell_h + GAP)
        place_auto_subtree(c, children_by_parent, cx, cy, sizes, out_placed)


def pack_variable_sized(node_ids, sizes, left, top, max_w, gap=GAP):
    """Left-to-right row packing of boxes with varying (w, h), wrapping when
    a box would exceed max_w. Returns {node_id: (x, y)} plus total height."""
    x, y, row_h, row_started = left, top, 0, False
    positions = {}
    for nid in node_ids:
        w, h = sizes[nid]
        if row_started and (x + w > left + max_w):
            x, y, row_h, row_started = left, y + row_h + gap, 0, False
        positions[nid] = (x, y)
        x += w + gap
        row_h = max(row_h, h)
        row_started = True
    total_h = (y - top) + row_h if row_started else 0
    return positions, total_h


def unplaced_view(children_by_parent, used_node_ids):
    """A children_by_parent map filtered to exclude anything already placed
    — recursion must never re-touch (and thereby clobber) a node that
    already has a real position, wherever it's used."""
    return {
        pid: [c for c in kids if c not in used_node_ids]
        for pid, kids in children_by_parent.items()
    }


# --------------------------------------------------------------------------
# Phase 1: snap VAMS nodes onto predefined template regions (slots/groups)
# --------------------------------------------------------------------------

def region_ancestor_names(region_roots):
    """Map id(region) -> normalized names of every region enclosing it (root
    first, region itself excluded) — used to disambiguate a name that
    appears on more than one template region (e.g. two slots both named
    "Search" under different groups)."""
    chains = {}

    def visit(region, chain):
        chains[id(region)] = chain
        for c in region.children:
            visit(c, chain + [norm(region.name)])

    for root in region_roots:
        visit(root, [])
    return chains


def node_ancestor_names(node_id, nodes):
    """Normalized names of a VAMS node's real ancestors (immediate parent
    first, node itself excluded)."""
    names = []
    parent = nodes[node_id].get("parent")
    while parent is not None:
        names.append(norm(nodes[parent].get("name", "")))
        parent = nodes[parent].get("parent")
    return names


def match_regions_to_nodes(regions, candidate_node_ids, nodes, used_node_ids,
                           node_to_region, ancestor_of_region):
    """Greedily pair `regions` (a flat list — no recursion into children)
    against `candidate_node_ids` by normalized name. When a name is shared
    by more than one region or more than one node among the candidates,
    prefer whichever pairing has the highest overlap between the region's
    enclosing-group names and the node's real VAMS ancestor names (ties
    broken by region order, for determinism). Mutates used_node_ids and
    node_to_region in place. Returns the list of node_ids matched here."""
    regions_by_name = {}
    for r in regions:
        regions_by_name.setdefault(norm(r.name), []).append(r)

    newly_matched = []
    for norm_name, region_list in regions_by_name.items():
        # Sorted (not just filtered from candidate_node_ids, which may be a
        # plain set — Python doesn't guarantee set iteration order for
        # strings) so a tie between two identically-scored candidates
        # resolves the same way on every run, not by hash-seed luck.
        candidates = sorted(
            nid for nid in candidate_node_ids
            if nid not in used_node_ids and norm(nodes[nid].get("name", "")) == norm_name
        )
        if not candidates:
            continue

        pairs = []  # (score, region, node_id)
        for region in region_list:
            region_chain = set(ancestor_of_region[id(region)])
            for nid in candidates:
                score = len(region_chain & set(node_ancestor_names(nid, nodes)))
                pairs.append((score, region, nid))
        # Stable sort on score alone: region_list and candidates are both
        # already in deterministic order, so equal-score pairs keep their
        # original (deterministic) relative order rather than needing an
        # id()-based key, which is only stable within a single run.
        pairs.sort(key=lambda p: -p[0])

        claimed_regions, claimed_nodes = set(), set()
        for _score, region, nid in pairs:
            if id(region) in claimed_regions or nid in claimed_nodes:
                continue
            region.matched_node_id = nid
            node_to_region[nid] = region
            used_node_ids.add(nid)
            claimed_regions.add(id(region))
            claimed_nodes.add(nid)
            newly_matched.append(nid)

    return newly_matched


def match_regions_to_nodes_by_classification(regions, candidate_node_ids, nodes,
                                              used_node_ids, node_to_region, shape_mappings):
    """Second-chance matching for whatever didn't align by name: a region's
    own rendered style implies a VAMS (type, environment, implementation)
    classification (see infer_region_classification) — if a still-unmatched
    candidate node has that same classification, treat it as "the same kind
    of thing" even though it's spelled differently (e.g. a document's root
    literally named "VTEX Platform" recognized as the same concept as a
    template's "VTEX Core Services" region, both being a Platform in the
    vtex environment). Only ever runs on what name-matching left unmatched,
    and never crosses a real parent/child boundary — it's used exactly
    where name-matching would have been used, just as a fallback signal.

    Regions are tried richest-first (most nested children) since a
    classification can be ambiguous (more than one region can render with
    the same style) and the most substantial region is the more plausible
    "main" one for that classification. Returns the list of newly matched
    node ids."""
    unmatched_regions = sorted(
        (r for r in regions if r.matched_node_id is None),
        key=lambda r: -len(r.children),
    )
    if not unmatched_regions:
        return []

    candidates = sorted(nid for nid in candidate_node_ids if nid not in used_node_ids)
    newly_matched = []

    for region in unmatched_regions:
        classification = infer_region_classification(region, shape_mappings)
        if classification is None:
            continue
        for nid in candidates:
            if nid in used_node_ids:
                continue
            if not node_matches_classification(nodes[nid], classification):
                continue
            region.matched_node_id = nid
            node_to_region[nid] = region
            used_node_ids.add(nid)
            newly_matched.append(nid)
            break

    return newly_matched


def scope_match_children(region, children_by_parent, nodes, used_node_ids,
                          node_to_region, ancestor_of_region, shape_mappings):
    """For an already-matched region, match its own nested regions (slots or
    sub-groups) against ONLY the DIRECT VAMS children of its matched node —
    never a grandchild reached by skipping past an intermediate node, and
    never a coincidentally-named node living anywhere else in the document.

    This must be direct children only, not every transitive descendant: if
    an intermediate child (e.g. "vtex-core-services") doesn't itself match
    anything, its own children (e.g. "catalog") are NOT eligible to reach
    up and claim one of this region's nested slots — that would place
    "catalog" inside the "Vtex Core Services" *template region* (fine) but
    NOT inside "vtex-core-services" the *real VAMS node's own rendered box*
    (which ends up somewhere else entirely, auto-placed as one of
    vtex-platform's extras) — a mandatory containment violation this was
    tested and caught doing. Matching one level at a time, exactly like the
    real tree, is what keeps every node inside its own real parent's box.

    Name match only at this tier — deliberately NOT the type/environment
    classification fallback used for top-level regions (see
    place_on_template): a group's nested slots are typically many
    same-styled Components (e.g. every VTEX-native component renders
    identically), so classification can't tell "Catalog" apart from
    "Pricing Hub" — trying it here was tested and caused real, wrong
    reassignments (a plain extra component landing on an unrelated named
    slot purely by shared generic styling).

    A nested slot with no matching direct child by name simply stays unused
    (that content is still drawn — Phase 2 nests it inside the parent's own
    box regardless — just not at that predefined position). Recurses into
    any matched sub-group the same way, one direct-child level at a time."""
    if region.matched_node_id is None or not region.children:
        return

    direct_children = set(children_by_parent.get(region.matched_node_id, []))
    match_regions_to_nodes(region.children, direct_children, nodes, used_node_ids,
                           node_to_region, ancestor_of_region)

    for child in region.children:
        scope_match_children(child, children_by_parent, nodes, used_node_ids,
                              node_to_region, ancestor_of_region, shape_mappings)


def reuse_spare_slots_for_leftover_children(region, nodes, children_by_parent, used_node_ids,
                                            node_to_region, shape_mappings, spare_reused_ids):
    """After name-based matching is fully resolved, a matched group may still
    have (a) real children with no name match, and (b) sibling slots with no
    name match either — both leftovers of the SAME name-matching pass, never
    anything that could have been claimed by name. Pair them up by rendered
    style classification (same type/environment/implementation) before
    falling back to growing the group or creating a brand-new shape: since
    every slot in a classification bucket renders identically, handing a
    leftover "G Pay" component an unused "Pricing Hub"-shaped slot (then
    labeling it correctly) is exactly as arbitrary as the alternative
    (auto-placing it in a fresh grid cell below), except it reuses a
    position/style the template already laid out nicely and costs nothing
    extra to create — unlike a name-based guess, there's no "correct" slot
    being second-guessed here, since neither side had one.

    This is NOT the classification fallback scope_match_children explicitly
    avoids — that would have let classification override an actual name
    match's competitor pool; this only ever touches what's left after every
    name match (real and possible) has already been decided.

    Only ever considers a leftover child that has NO real children of its
    own. A template slot is a fixed size chosen for a simple leaf label —
    reusing it for a node that itself needs to become a growable container
    was tried and caused a real bug: the reused slot's rigid width doesn't
    flex for whatever that node's own children need, so a wide sub-tree
    silently overflowed past its "parent" slot's right edge. A node with
    real children of its own belongs in the normal growth/auto-placement
    path, which sizes a box from its actual content instead of wedging it
    into a pre-existing size that was never meant to hold it."""
    if region.matched_node_id is None or not region.children:
        return

    leftover_children = sorted(
        (
            c for c in children_by_parent.get(region.matched_node_id, [])
            if c not in used_node_ids and not children_by_parent.get(c)
        ),
        key=lambda nid: nodes[nid].get("name", ""),
    )
    if not leftover_children:
        return

    unused_slots = [r for r in region.children if r.matched_node_id is None]
    if not unused_slots:
        return

    for child_id in leftover_children:
        node = nodes[child_id]
        for slot in unused_slots:
            if slot.matched_node_id is not None:
                continue
            classification = infer_region_classification(slot, shape_mappings)
            if classification and node_matches_classification(node, classification):
                slot.matched_node_id = child_id
                node_to_region[child_id] = slot
                used_node_ids.add(child_id)
                spare_reused_ids.add(child_id)
                break


def place_on_template(nodes, children_by_parent, roots, region_roots, shape_mappings):
    """Match VAMS nodes onto template regions. Returns (used_node_ids,
    all_regions, node_to_region). Region geometry (region.top/left/right/
    bottom) is read live at DSL emission time, not captured here — Phase 2
    may still grow a matched group's box, so nothing final is decided yet.

    Containment is MANDATORY and driven by the VAMS `parent` attribute, not
    by node name — the template only ever suggests a POSITION, it never
    overrides real hierarchy:

    - Only actual VAMS root nodes (no `parent` at all) may match a
      top-level template region. A non-root node can never "jump" to an
      unrelated top-level region just because its name happens to match
      one — if the template doesn't model its real parent as a root
      concept, that whole branch renders as new/auto-placed instead (see
      Phase 4), which is correct: the template's assumed top-level shape
      doesn't fit this document's real structure, and hierarchy fidelity
      wins over template fit every time.
    - A root is matched to a top-level region by name first; if nothing
      matches by name, a (type, environment, implementation) classification
      inferred from the region's own rendered style is tried instead — so
      a document's "VTEX Platform" root can still recognize a template's
      "VTEX Core Services" region as the same kind of thing (both a
      Platform in the vtex environment) even though the strings differ.
    - Once a region is matched, its own nested slots/sub-groups are matched
      ONLY against that node's real VAMS descendants, by NAME only — never
      a global search, and deliberately no classification fallback at this
      tier (see scope_match_children for why: many nested slots share
      identical generic styling, so classification can't tell them apart
      and would assign an extra component to an arbitrary unrelated named
      slot). A slot named "Orders" inside "VTEX Core Services" can only
      catch a node that's actually part of VTEX Core Services in the
      document; an unrelated "Orders" node three branches away (e.g. in an
      ERP system) is never eligible, no matter how the strings compare. A
      slot with no matching real descendant just goes unused — that
      content still renders (nested inside the true parent, Phase 2), just
      not at that predefined position.

    A name can legitimately appear on more than one template region at the
    same tier (e.g. a "Search" slot both under "VTEX Core Services" and
    under "3rd Party Optional") or, less commonly, more than one VAMS node
    can share a name; see match_regions_to_nodes for how those ties break."""
    all_regions = flatten_regions_preorder(region_roots)
    ancestor_of_region = region_ancestor_names(region_roots)
    used_node_ids = set()
    node_to_region = {}
    spare_reused_ids = set()

    # Phase A: top-level regions may ONLY match actual VAMS roots — a node
    # with a real parent must nest inside that parent, mandatorily, never
    # at a top-level slot/group elsewhere just because the name matches.
    match_regions_to_nodes(region_roots, roots, nodes, used_node_ids,
                           node_to_region, ancestor_of_region)
    match_regions_to_nodes_by_classification(region_roots, roots, nodes,
                                             used_node_ids, node_to_region, shape_mappings)

    # Phase B: every matched region's own children are scoped to its real
    # VAMS descendants only, recursively — no global fallback at any depth.
    for region in region_roots:
        scope_match_children(region, children_by_parent, nodes, used_node_ids,
                             node_to_region, ancestor_of_region, shape_mappings)

    # Phase B.5: only after every possible name match (at every depth) is
    # fully resolved, let each matched group reuse its own leftover unused
    # slots for leftover real children of the same style classification —
    # see reuse_spare_slots_for_leftover_children for why this is safe.
    def reuse_recursive(region):
        reuse_spare_slots_for_leftover_children(
            region, nodes, children_by_parent, used_node_ids,
            node_to_region, shape_mappings, spare_reused_ids,
        )
        for child in region.children:
            reuse_recursive(child)

    for region in region_roots:
        reuse_recursive(region)

    return used_node_ids, all_regions, node_to_region, spare_reused_ids


# --------------------------------------------------------------------------
# Phase 2: grow every matched region to contain ALL of its matched node's
# real VAMS children — not just the ones with their own predefined slot.
# Recursion is bottom-up (deepest regions first) so a parent's growth
# calculation always sees its children's FINAL (already-grown) size.
# --------------------------------------------------------------------------

def grow_region_for_real_children(region, nodes, children_by_parent, used_node_ids,
                                   auto_placed, container_node_ids, extras_root_of, root,
                                   grew_node_ids):
    for child in region.children:
        grow_region_for_real_children(child, nodes, children_by_parent, used_node_ids,
                                       auto_placed, container_node_ids, extras_root_of, root,
                                       grew_node_ids)

    if region.matched_node_id is None:
        return

    real_children = children_by_parent.get(region.matched_node_id, [])
    extra_children = sorted(
        (c for c in real_children if c not in used_node_ids),
        key=lambda c: nodes[c].get("name", ""),
    )

    content_bottom = max((c.bottom for c in region.children), default=region.top + GROUP_HEADER_H)

    if extra_children:
        container_node_ids.add(region.matched_node_id)
        grew_node_ids.add(region.matched_node_id)
        unplaced = unplaced_view(children_by_parent, used_node_ids)
        sizes = {}
        for ec in extra_children:
            compute_natural_size(ec, unplaced, sizes)

        pack_top = content_bottom + GAP
        positions, pack_h = pack_variable_sized(extra_children, sizes, region.left + GAP, pack_top, region.w - 2 * GAP)
        for ec in extra_children:
            ex, ey = positions[ec]
            place_auto_subtree(ec, unplaced, ex, ey, sizes, auto_placed)
            for did in collect_all_descendants(ec, unplaced):
                used_node_ids.add(did)
                extras_root_of[did] = root

        content_bottom = pack_top + pack_h

    region.bottom = max(region.bottom, content_bottom)


# --------------------------------------------------------------------------
# Phase 3: compaction — if growth made a top-level region taller than its
# template size, push any sibling below it (in the same horizontal band)
# down far enough to clear it, so growth never creates a new overlap.
# --------------------------------------------------------------------------

def compute_top_level_shifts(region_roots):
    placed_boxes = []  # (left, right, bottom_after_shift)
    shifts = {}
    for r in sorted(region_roots, key=lambda r: r.top):
        min_top = r.top
        for (left, right, bottom) in placed_boxes:
            if not (r.right <= left or right <= r.left):  # x-ranges overlap
                min_top = max(min_top, bottom + GAP)
        shift = min_top - r.top
        shifts[id(r)] = shift
        placed_boxes.append((r.left, r.right, min_top + r.h))
    return shifts


def apply_shift_to_region_subtree(region, dy):
    if dy == 0:
        return
    region.top += dy
    region.bottom += dy
    for c in region.children:
        apply_shift_to_region_subtree(c, dy)


# --------------------------------------------------------------------------
# Phase 4: anything with no template-matched ancestor at all — a whole new
# subsystem the template has no concept of — becomes its own self-contained
# group further down the board.
# --------------------------------------------------------------------------

def topmost_unplaced_ancestor(node_id, nodes, used_node_ids):
    current = node_id
    while True:
        parent = nodes[current].get("parent")
        if parent is None or parent in used_node_ids:
            return current
        current = parent


def nearest_placed_ancestor_name(node_id, nodes, used_node_ids):
    parent = nodes[node_id].get("parent")
    while parent is not None:
        if parent in used_node_ids:
            return nodes[parent]["name"]
        parent = nodes[parent].get("parent")
    return None


def auto_place_new_top_level_groups(nodes, children_by_parent, used_node_ids,
                                     container_node_ids, left, top, max_w):
    unplaced = [nid for nid in nodes if nid not in used_node_ids]

    auto_roots = []
    seen_roots = set()
    for nid in unplaced:
        root = topmost_unplaced_ancestor(nid, nodes, used_node_ids)
        if root not in seen_roots:
            seen_roots.add(root)
            auto_roots.append(root)

    unplaced_children = unplaced_view(children_by_parent, used_node_ids)
    sizes = {}
    for root in auto_roots:
        compute_natural_size(root, unplaced_children, sizes)
        if unplaced_children.get(root):
            container_node_ids.add(root)

    roots_sorted = sorted(auto_roots, key=lambda nid: nodes[nid].get("name", ""))
    positions, total_h = pack_variable_sized(roots_sorted, sizes, left, top + GROUP_HEADER_H, max_w)

    placed = {}
    for root in roots_sorted:
        rx, ry = positions[root]
        place_auto_subtree(root, unplaced_children, rx, ry, sizes, placed)

    return placed, roots_sorted, total_h


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vams_path")
    ap.add_argument("template_path", help="Path to a template file, or just its filename to use the bundled templates/ folder")
    ap.add_argument("--frame", help="Title of the template frame to use (required if the template file has more than one candidate)")
    ap.add_argument("--title", help="Title for the generated board frame (defaults to the VAMS document name)")
    ap.add_argument("--out", help="Write DSL to this file instead of stdout")
    ap.add_argument("--report", help="Write the placement report JSON to this file instead of stderr")
    ap.add_argument("--shape-mapping", default=None)
    ap.add_argument("--connector-mapping", default=None)
    args = ap.parse_args()

    script_dir = __file__.rsplit("/", 1)[0]
    shape_mapping_path = args.shape_mapping or f"{script_dir}/../references/vams-miro-shape-mapping.json"
    connector_mapping_path = args.connector_mapping or f"{script_dir}/../references/vams-miro-connector-mapping.json"

    with open(args.vams_path) as f:
        vams_doc = unwrap_export_envelope(json.load(f))
    with open(resolve_template_path(args.template_path)) as f:
        template_doc = json.load(f)

    shape_mappings = load_shape_mappings(shape_mapping_path)
    connector_mappings = load_connector_mappings(connector_mapping_path)

    frame_item = find_template_frame(template_doc, args.frame)
    region_roots, frame_w, frame_h = build_region_tree(template_doc, frame_item)

    nodes, children_by_parent, roots, data_entities, flows = load_vams(vams_doc)

    # Documents exported via the existing Miro->VAMS importer wrap
    # everything under one generic Group node named after the source Miro
    # frame — an export artifact, not a real architectural concept. Left
    # alone, it would block every real top-level concept beneath it from
    # ever matching a template region. Detected narrowly (the document's
    # own metadata names the frame; the wrapper's name must match exactly)
    # so a genuine user-authored top-level Group is never touched.
    frame_wrapper_id = detect_frame_wrapper_root(vams_doc, nodes, roots)
    frame_wrapper_info = None
    if frame_wrapper_id:
        frame_wrapper_info = {
            "id": frame_wrapper_id,
            "name": nodes[frame_wrapper_id]["name"],
            "children_promoted_to_root": len(children_by_parent.get(frame_wrapper_id, [])),
        }
        nodes, children_by_parent, roots = unwrap_frame_wrapper_root(
            nodes, children_by_parent, roots, frame_wrapper_id
        )

    # Phase 1: name-match onto the template (root nodes only may match a
    # top-level region; everything else is scoped to its real VAMS parent).
    used_node_ids, all_regions, node_to_region, spare_reused_ids = place_on_template(
        nodes, children_by_parent, roots, region_roots, shape_mappings
    )
    slot_ids = {nid for nid, r in node_to_region.items() if r.is_leaf} - spare_reused_ids
    group_ids_before_growth = {nid for nid, r in node_to_region.items() if not r.is_leaf} - spare_reused_ids

    # Phase 2: grow matched groups (or matched "slots" whose node turned out
    # to have real children after all) to nest ALL their real children.
    auto_placed = {}
    container_node_ids = set(group_ids_before_growth)
    extras_root_of = {}
    grew_node_ids = set()
    for root_region in region_roots:
        grow_region_for_real_children(
            root_region, nodes, children_by_parent, used_node_ids,
            auto_placed, container_node_ids, extras_root_of, root=id(root_region),
            grew_node_ids=grew_node_ids,
        )

    # Phase 3: compaction so growth never creates a new sibling overlap.
    shifts = compute_top_level_shifts(region_roots)
    for root_region in region_roots:
        apply_shift_to_region_subtree(root_region, shifts[id(root_region)])
    for node_id in list(auto_placed.keys()):
        root_key = extras_root_of.get(node_id)
        dy = shifts.get(root_key, 0)
        if dy:
            x, y, w, h, via = auto_placed[node_id]
            auto_placed[node_id] = (x, y + dy, w, h, via)

    content_bottom = max((r.bottom for r in all_regions), default=0)

    # Phase 4: whole new top-level subsystems the template has no concept of.
    new_groups_placed, new_group_roots, new_groups_h = auto_place_new_top_level_groups(
        nodes, children_by_parent, used_node_ids, container_node_ids,
        left=GAP, top=content_bottom + GAP * 3, max_w=frame_w - 2 * GAP,
    )
    auto_placed.update(new_groups_placed)

    extra_bottom_h = (GROUP_HEADER_H + new_groups_h) if new_group_roots else 0
    total_frame_h = max(frame_h, content_bottom + GAP * 3 + extra_bottom_h)

    # Hard invariant: every node must end up placed somewhere (either on the
    # template, live via node_to_region, or in auto_placed).
    placed_ids = set(node_to_region.keys()) | set(auto_placed.keys())
    missing = set(nodes.keys()) - placed_ids
    if missing:
        missing_desc = ", ".join(f'{nid} ({nodes[nid].get("name")!r})' for nid in sorted(missing))
        raise RuntimeError(
            f"Internal error: {len(missing)} node(s) were never placed: {missing_desc}. "
            "This should be impossible — please report it."
        )

    # --- Emit DSL ---
    used_ids = set()
    node_alias = {}
    lines = []

    board_title = args.title or vams_doc.get("name", "VAMS Architecture")
    frame_alias = sanitize_id("board_frame", "frame", used_ids)
    lines.append(
        f'{frame_alias} FRAME x=0 y=0 w={frame_w:.0f} h={total_frame_h:.0f} "{dsl_escape(board_title)}"'
    )

    def render_shape(node_id, left, top, w, h, as_container):
        node = nodes[node_id]
        miro_style = match_shape_style(node, shape_mappings)
        attrs = shape_dsl_attrs(miro_style)
        alias = sanitize_id(node["id"], f"n{len(node_alias)}", used_ids)
        node_alias[node_id] = alias
        attr_str = " ".join(f"{k}={v}" for k, v in attrs.items())
        align = "align=left valign=top size=18 " if as_container else ""
        lines.append(
            f'{alias} SHAPE parent={frame_alias} x={left + w/2:.0f} y={top + h/2:.0f} '
            f'w={w:.0f} h={h:.0f} {attr_str} {align}"<p><strong>{dsl_escape(node["name"])}</strong></p>"'
        )

    # Containers first (template groups incl. grown "slots", plus new
    # top-level groups) so children visually sit on top of them. Sorted —
    # container_node_ids is a set, and set iteration order for strings
    # isn't guaranteed, which would otherwise make the DSL's line order
    # (not its geometry) vary run to run for no reason.
    for node_id in sorted(container_node_ids):
        if node_id in node_to_region:
            r = node_to_region[node_id]
            render_shape(node_id, r.left, r.top, r.w, r.h, as_container=True)
        else:
            x, y, w, h, _via = auto_placed[node_id]
            render_shape(node_id, x, y, w, h, as_container=True)

    if new_group_roots:
        alias = sanitize_id("hdr-new-groups", "hdr", used_ids)
        header_y = content_bottom + GAP * 3
        lines.append(
            f'{alias} TEXT parent={frame_alias} x={frame_w/2:.0f} y={header_y + GROUP_HEADER_H/2:.0f} '
            f'w={frame_w - 2*GAP:.0f} align=center size=20 '
            f'"<strong>New top-level groups (not covered by the template)</strong>"'
        )

    # Every remaining leaf/slot shape.
    for node_id, region in node_to_region.items():
        if node_id in node_alias:
            continue
        render_shape(node_id, region.left, region.top, region.w, region.h, as_container=False)
    for node_id, (x, y, w, h, _via) in auto_placed.items():
        if node_id in node_alias:
            continue
        render_shape(node_id, x, y, w, h, as_container=False)

    # Connectors.
    connector_report = []
    for i, flow in enumerate(flows):
        origin, dest = flow.get("origin"), flow.get("destination")
        if origin not in node_alias or dest not in node_alias:
            connector_report.append({
                "flow_id": flow.get("id", f"flow-{i}"),
                "origin": origin, "destination": dest,
                "reason": "endpoint id not found in this document's nodes",
            })
            continue
        style = match_connector_style(flow, connector_mappings)
        attrs = connector_dsl_attrs(style)
        attr_str = " ".join(f"{k}={v}" for k, v in attrs.items())
        caption_names = []
        for d_id in flow.get("data", []) or []:
            d = data_entities.get(d_id)
            caption_names.append(d["name"] if d else d_id)
        caption = f' "[{", ".join(caption_names)}]"' if caption_names else ""
        alias = sanitize_id(flow.get("id", f"flow{i}"), f"f{i}", used_ids)
        lines.append(
            f'{alias} CONNECTOR from={node_alias[origin]} to={node_alias[dest]} '
            f'shape=elbowed {attr_str}{caption}'
        )

    dsl_text = "\n".join(lines) + "\n"

    if args.out:
        with open(args.out, "w") as f:
            f.write(dsl_text)
    else:
        sys.stdout.write(dsl_text)

    report = {
        "frame_used": frame_item.get("data", {}).get("title"),
        "frame_wrapper_unwrapped": frame_wrapper_info,
        "template_size": {"w": frame_w, "h": frame_h},
        "generated_frame_size": {"w": frame_w, "h": total_frame_h},
        "nodes_total": len(nodes),
        "nodes_snapped_to_slot": len(slot_ids),
        "nodes_snapped_to_group": len(group_ids_before_growth),
        "nodes_reused_spare_slot": len(spare_reused_ids),
        "nodes_nested_under_matched_group": len(extras_root_of),
        "matched_groups_grown_for_extra_children": sorted(nodes[nid]["name"] for nid in grew_node_ids),
        "nodes_in_new_top_level_groups": len(new_groups_placed),
        "new_top_level_group_names": [nodes[r]["name"] for r in new_group_roots],
        "flows_total": len(flows),
        "flows_rendered": len(flows) - len(connector_report),
        "flows_skipped": connector_report,
    }

    report_text = json.dumps(report, indent=2)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report_text)
    else:
        sys.stderr.write(report_text + "\n")


if __name__ == "__main__":
    main()
