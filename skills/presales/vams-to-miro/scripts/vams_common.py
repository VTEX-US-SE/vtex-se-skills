"""
Shared parsing helpers for the vams-to-miro scripts: turning a raw Miro board
JSON export into a group/slot region tree, and loading a VAMS document into
easy-to-walk lookups. No third-party dependencies.
"""

import os
import re

# Frame titles that belong to the standard VAMS legend/reference board and are
# never themselves usable layout templates (see vams/examples/miro-board-template.json).
LEGEND_FRAME_TITLES = {
    "components", "applications", "middleware & system", "middleware &amp; system",
    "platforms", "groups", "nodes", "flows", "data", "event",
}

# templates/ bundled alongside this skill (scripts/../templates) — the
# default source of layout templates for anyone who imports just this
# skill folder. Pass an explicit path/--templates-dir to use a different,
# e.g. org-wide shared, template library instead.
BUNDLED_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")


def resolve_template_path(path):
    """If `path` doesn't exist as given, try it as a filename inside the
    bundled templates/ folder — lets callers pass just "b2b-basic.json"
    instead of a full path."""
    if os.path.exists(path):
        return path
    candidate = os.path.join(BUNDLED_TEMPLATES_DIR, os.path.basename(path))
    if os.path.exists(candidate):
        return candidate
    raise SystemExit(
        f'Template file "{path}" not found (also checked {os.path.abspath(candidate)}).'
    )


def norm(s):
    """Normalize a name for matching: lowercase, strip non-alphanumerics."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def strip_html(raw):
    if not raw:
        return ""
    text = re.sub(r"<[^>]*>", "", raw)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def sanitize_id(raw, fallback_prefix, used):
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "-", str(raw))
    if not cleaned or cleaned == "-":
        cleaned = fallback_prefix
    candidate = cleaned
    i = 2
    while candidate in used:
        candidate = f"{cleaned}-{i}"
        i += 1
    used.add(candidate)
    return candidate


def dsl_escape(text):
    return (text or "").replace('"', "'")


# --------------------------------------------------------------------------
# Template parsing: extract the containment (group/slot) tree of one frame
# from a raw Miro board JSON export.
# --------------------------------------------------------------------------

class Region:
    __slots__ = ("name", "left", "top", "right", "bottom", "source_id",
                 "children", "matched_node_id", "style", "shape")

    def __init__(self, name, left, top, right, bottom, source_id, style, shape=None):
        self.name = name
        self.left, self.top, self.right, self.bottom = left, top, right, bottom
        self.source_id = source_id
        self.children = []
        self.matched_node_id = None
        self.style = style or {}
        self.shape = shape  # Miro shape type (e.g. "round_rectangle") — for reverse VAMS classification

    @property
    def w(self):
        return self.right - self.left

    @property
    def h(self):
        return self.bottom - self.top

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def area(self):
        return self.w * self.h


def find_usable_frames(template_doc):
    """All top-level frames in this board export except the standard legend
    frames (Components, Applications, Flows, ...) — each is a candidate
    layout template."""
    items = template_doc.get("items", [])
    frames = [i for i in items if i.get("type") == "frame"]
    return [
        f for f in frames
        if norm(f.get("data", {}).get("title", "")) not in {norm(t) for t in LEGEND_FRAME_TITLES}
    ]


def find_template_frame(template_doc, frame_title=None):
    """Resolve a single usable frame by title, or the only candidate if there's
    just one. Raises SystemExit with the available titles otherwise."""
    usable = find_usable_frames(template_doc)

    if frame_title:
        for f in usable:
            if norm(f.get("data", {}).get("title", "")) == norm(frame_title):
                return f
        available = [f.get("data", {}).get("title", "") for f in usable]
        raise SystemExit(
            f'Frame "{frame_title}" not found. Available template frames: {available}'
        )

    if len(usable) == 1:
        return usable[0]

    available = [f.get("data", {}).get("title", "") for f in usable]
    raise SystemExit(
        "Multiple candidate template frames found; pass --frame to pick one: "
        f"{available}"
    )


def build_region_tree(template_doc, frame_item):
    """Build a containment tree of shapes that are direct children of frame_item.

    Containment is geometric (smallest-area shape whose box fully contains
    another shape's box wins as parent), mirroring the bounding-box logic
    already used by vams-miro-integration's Miro->VAMS importer.
    """
    frame_id = str(frame_item["id"])
    items = template_doc.get("items", [])
    shapes = [
        i for i in items
        if i.get("type") == "shape" and str(i.get("parent", {}).get("id")) == frame_id
    ]

    boxes = {}
    for s in shapes:
        geom = s.get("geometry", {})
        pos = s.get("position", {})
        w, h = float(geom.get("width", 0)), float(geom.get("height", 0))
        cx, cy = float(pos.get("x", 0)), float(pos.get("y", 0))
        boxes[s["id"]] = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def contains(outer, inner, eps=0.5):
        return (
            outer[0] <= inner[0] + eps and outer[1] <= inner[1] + eps and
            outer[2] >= inner[2] - eps and outer[3] <= 1e18 and
            outer[3] >= inner[3] - eps
        )

    def area(b):
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])

    regions = {}
    for s in shapes:
        name = strip_html(s.get("data", {}).get("content", "")) or s.get("id")
        left, top, right, bottom = boxes[s["id"]]
        shape_type = s.get("data", {}).get("shape")
        regions[s["id"]] = Region(name, left, top, right, bottom, s["id"], s.get("style"), shape_type)

    def fill_opacity(shape):
        try:
            return float(shape.get("style", {}).get("fillOpacity", 1.0))
        except (TypeError, ValueError):
            return 1.0

    parent_of = {}
    for s in shapes:
        # Group-style shapes (reduced fill opacity, per vams-miro-shape-mapping.json's
        # convention for Group/Platform containers) are always top-level regions.
        # A big background rectangle can incidentally bounding-box-overlap an
        # unrelated sibling group without being its real container — only
        # genuinely opaque "slot" shapes get nested by pure geometry.
        if fill_opacity(s) < 0.99:
            parent_of[s["id"]] = None
            continue

        my_box = boxes[s["id"]]
        best_id, best_area = None, float("inf")
        for other in shapes:
            if other["id"] == s["id"]:
                continue
            other_box = boxes[other["id"]]
            if not contains(other_box, my_box):
                continue
            a = area(other_box)
            if a < best_area:
                best_area = a
                best_id = other["id"]
        parent_of[s["id"]] = best_id

    roots = []
    for s in shapes:
        pid = parent_of[s["id"]]
        if pid is None:
            roots.append(regions[s["id"]])
        else:
            regions[pid].children.append(regions[s["id"]])

    def sort_key(r):
        return (r.top, r.left)

    def sort_tree(r):
        r.children.sort(key=sort_key)
        for c in r.children:
            sort_tree(c)

    roots.sort(key=sort_key)
    for r in roots:
        sort_tree(r)

    frame_geom = frame_item.get("geometry", {})
    return roots, float(frame_geom.get("width", 0)), float(frame_geom.get("height", 0))


def infer_region_classification(region, shape_mappings):
    """Reverse of the forward VAMS -> Miro style mapping
    (vams-miro-shape-mapping.json): given a template region's own rendered
    shape/style, infer the (type, environment, implementation) it implies.
    Mirrors vams-miro-integration's Miro->VAMS matchShapeToVams logic — the
    same convention already used to STYLE nodes is reused here to CLASSIFY
    a region, so a root node whose name doesn't match any template region
    (e.g. a document's "VTEX Platform" vs. a template's "VTEX Core
    Services") can still be recognized as "the same kind of thing" (a
    Platform in the vtex environment) and matched on that basis. Returns
    None if no mapping row fits."""
    item_shape = region.shape
    item_style = region.style or {}

    for m in shape_mappings:
        miro = m["miro"]
        vams = m["vams"]
        expected_shape = miro.get("data", {}).get("shape")
        if expected_shape and expected_shape != item_shape:
            continue

        style_matches = True
        for key, expected_value in miro.get("style", {}).items():
            if str(item_style.get(key)) != str(expected_value):
                style_matches = False
                break
        if not style_matches:
            continue

        return {
            "type": vams["type"],
            "environment": None if vams["environment"] == "*" else vams["environment"],
            "implementation": None if vams["implementation"] == "*" else vams["implementation"],
        }

    return None


def node_matches_classification(node, classification):
    """True if a VAMS node's own (type, environment, implementation) fits a
    classification inferred by infer_region_classification (None fields in
    the classification are wildcards and always match)."""
    if classification is None:
        return False
    if node.get("type") != classification["type"]:
        return False
    if classification["environment"] is not None and node.get("environment") != classification["environment"]:
        return False
    if classification["implementation"] is not None and node.get("implementation") != classification["implementation"]:
        return False
    return True


def flatten_regions_preorder(roots):
    out = []

    def visit(r):
        out.append(r)
        for c in r.children:
            visit(c)

    for r in roots:
        visit(r)
    return out


# --------------------------------------------------------------------------
# VAMS parsing
# --------------------------------------------------------------------------

def unwrap_export_envelope(raw_doc):
    """Real files coming out of vams-miro-integration's Drive/GitHub export
    step (buildArchitectureExportContent) are wrapped in an envelope:
    {"architecture": <the whole VAMS document>, "clientId": ..., "accounts":
    [...], "level": ...} — the outer "architecture" key holds an entire
    VAMS document (itself with its OWN "architecture" key holding nodes/
    flows/dataEntities/environments), not those fields directly. Handed to
    load_vams() unwrapped, this silently yields 0 nodes rather than an
    error, which is worse. Detect the shape and return the real inner
    document; a plain, already-correct VAMS document passes through
    unchanged."""
    inner = raw_doc.get("architecture")
    if (
        isinstance(inner, dict)
        and "nodes" not in inner
        and isinstance(inner.get("architecture"), dict)
        and "nodes" in inner["architecture"]
    ):
        return inner
    return raw_doc


def load_vams(vams_doc):
    vams_doc = unwrap_export_envelope(vams_doc)
    arch = vams_doc.get("architecture", {})
    nodes = {n["id"]: n for n in arch.get("nodes", [])}
    children_by_parent = {}
    for n in arch.get("nodes", []):
        p = n.get("parent")
        children_by_parent.setdefault(p, []).append(n["id"])
    roots = children_by_parent.get(None, [])
    data_entities = {d["id"]: d for d in arch.get("dataEntities", [])}
    flows = arch.get("flows", [])
    return nodes, children_by_parent, roots, data_entities, flows


def detect_frame_wrapper_root(vams_doc, nodes, roots):
    """The existing Miro->VAMS importer (miroToVamsService.ts) models the
    WHOLE source frame as an outer wrapping Group node — every real
    top-level architectural concept (a Platform, a Group like "Merchant
    Channels", ...) ends up as ITS child, one level below where a
    hand-built VAMS document would normally put them. That wrapper carries
    no real architectural meaning; it's a side effect of "the frame itself
    became a node", not intentional modeling — so it should never be what
    blocks real content from matching a top-level template region.

    Detected narrowly and verifiably, not by a loose shape-based guess: the
    importer always writes a metadata.description of the form
    'Generated from Miro board <id> (frame "<name>")', and the wrapper
    root's own name is exactly that frame name. Returns the wrapper's node
    id, or None if this document doesn't match that specific signature (a
    genuine user-authored top-level Group is left alone)."""
    description = (vams_doc.get("metadata", {}) or {}).get("description", "") or ""
    m = re.search(r'\(frame\s+"([^"]+)"\)', description)
    if not m:
        return None

    frame_name = norm(m.group(1))
    for rid in roots:
        if norm(nodes[rid].get("name", "")) == frame_name:
            return rid
    return None


def unwrap_frame_wrapper_root(nodes, children_by_parent, roots, wrapper_id):
    """Given a confirmed frame-wrapper root (see detect_frame_wrapper_root),
    return (nodes, children_by_parent, roots) with that wrapper's direct
    children promoted to real roots — eligible for top-level template
    matching same as any other root — while the wrapper node itself is
    kept (as a childless leaf) so it's still fully rendered, just no longer
    acting as a blocking ancestor. Does not mutate the inputs.

    wrapper_id must be a real, confirmed node id (the caller's own
    `if frame_wrapper_id:` check before calling this is the guard) — passing
    None here is a caller bug, not "no wrapper": children_by_parent[None]
    is the ROOTS list, so treating None as a wrapper id would corrupt
    every root's parent, not fix anything. Fail loudly instead."""
    if wrapper_id is None:
        raise ValueError(
            "unwrap_frame_wrapper_root() called with wrapper_id=None — "
            "check detect_frame_wrapper_root()'s result before calling this, "
            "don't call it unconditionally."
        )
    promoted = list(children_by_parent.get(wrapper_id, []))

    new_nodes = dict(nodes)
    for nid in promoted:
        new_nodes[nid] = {**nodes[nid], "parent": None}

    new_children_by_parent = {k: list(v) for k, v in children_by_parent.items() if k != wrapper_id}
    new_children_by_parent[None] = [r for r in roots if r != wrapper_id] + promoted

    new_roots = [r for r in roots if r != wrapper_id] + promoted
    return new_nodes, new_children_by_parent, new_roots
