# Layout templates

This folder is bundled inside the `vams-to-miro` skill (not a separate,
external location) — copying or packaging the skill folder brings a working
starter template set with it automatically. All of the skill's scripts
default to scanning this folder; pass an explicit path or `--templates-dir`
to point at a different/external template library instead.

A template here is a **raw Miro board JSON export** (the same shape produced
by reading a board through the Miro API / MCP — `board`, `items`, etc.), not
a hand-written schema. Draw the reference layout visually in Miro, export the
board, and drop the JSON file in this folder.

## What makes something a usable template

Within the exported JSON's `items[]`, one or more top-level `frame` items are
candidate templates — **except** frames whose title matches the standard VAMS
legend/reference set (`Components`, `Applications`, `Middleware & System`,
`Platforms`, `Groups`, `Nodes`, `Flows`, `Data`, `Event` — see
`vams/examples/miro-board-template.json`). Those are decorative type/style
legends, never real layouts. Any other frame title (e.g. `"Basic B2B"`) is a
selectable template — pass it via `generate_layout_dsl.py --frame "<title>"`.

## Groups vs. slots

A shape is a **group** if it's drawn with reduced fill opacity (< 1.0 —
the same "transparent background container" convention
`vams-miro-shape-mapping.json` already uses for `Group`/`Platform` nodes).
Groups are always treated as top-level regions, even if their box happens to
geometrically overlap a sibling group's box (a wide background rectangle can
incidentally bounding-box-overlap an unrelated group next to it without
being its real container — this bit us during testing, see
`b2b-core-modules` nested inside `vtex-core-services` purely by coincidence
of a wide box before this rule was added).

Every other (fully opaque) shape is a **slot** — a fixed, pre-designed
position for one specific expected node (e.g. "Catalog", "OMS", "Checkout").
Slots nest under whichever group's box geometrically contains them (the same
bounding-box "smallest shape that fully contains me wins as parent" logic
the `vams-miro-integration` app already uses to read boards back into VAMS).

Either kind is matched against a VAMS node's `name` (anywhere in the
document, any depth, case/whitespace/punctuation-insensitive). When a group
matches, that VAMS node is drawn at the group's exact position/size, and
matching continues recursively among that node's own children vs. the
group's inner slots.

Unmatched template slots/groups are simply not drawn (no empty placeholder
clutter) — the template only ever adds structure, it never requires it.

The reverse direction matters just as much: **a template positions known
things, it never restricts what can exist.** Any VAMS node that doesn't
match anything — a whole new Platform, a Component the template never
modeled, a second node that lost a name-match tie to its sibling — is still
drawn in full, with its own real parent/child hierarchy preserved (a new
group with five components under it renders as a labeled container holding
five boxes, not five loose shapes), auto-positioned in a labeled section
below the template instead of at a hand-placed spot. `generate_layout_dsl.py`
asserts this as a hard internal check — every node always ends up placed
somewhere, and the script fails loudly rather than silently produce an
incomplete diagram. The JSON report always breaks down exactly what was
template-matched vs. auto-placed, and why, for a human to read.

## Tools

(paths relative to the skill root, one level up from this folder)

- `scripts/generate_layout_dsl.py` — VAMS + template → Miro layout DSL (the
  main generator; see the skill's `SKILL.md`).
- `scripts/select_template.py` — given a VAMS doc, ranks every template frame
  by top-level name-match score, for auto-selecting a template when one
  already exists (dedupes identical files by content hash).
- `scripts/describe_template.py` — prints a template frame's group/slot
  outline (or, with `--list`, every frame across every file here), for
  showing a user what to fill in / choose from when they pick a template
  *before* a VAMS doc exists.

## Building a new template

1. In Miro, lay out one frame per business pattern (e.g. "Basic B2C",
   "Marketplace"). Use big, low-opacity shapes for groups and small opaque
   shapes for slots, named after the VAMS node names you expect to see.
2. Export the board to JSON (e.g. via the bundled Miro REST client in the
   `vams` repo, `scripts/read-miro-board.js`, or the Miro MCP's
   `layout_read`/`board_list_items`) and save it here.
3. Naming matters for nested slots — a slot inside a group is only useful
   if its shape's text content matches the real VAMS node `name` you expect
   to see nested there, since matching below the top level is name-only
   (see the skill's `SKILL.md` for why: nested slots are usually many
   identically-styled Components, so a type/environment fallback can't
   tell them apart). Top-level groups are more forgiving — if a document's
   root node is styled the same way (matching `type`/`environment` per
   `references/vams-miro-shape-mapping.json`) but named differently (e.g.
   a customer's "VTEX Platform" vs. this template's "VTEX Core Services"),
   it still recognizes the group as long as it's styled consistently with
   that convention. So: name top-level groups after the *convention*
   (what a `Platform`/vtex-styled root usually looks like), and name nested
   slots after the *specific* service you expect (exact strings matter).

### Standard layout convention

Most VTEX solution architectures share a recognizable shape — following it
when placing groups makes different templates feel consistent, and makes a
generated diagram easy to read at a glance regardless of which template
produced it:

- **Top**: front-end / channels (storefront, mobile app, POS, etc.)
- **Middle**: the VTEX Platform itself (core services, catalog, checkout,
  OMS, ...)
- **Below that**: middleware / integration layer
- **Bottom**: merchant back-office systems (ERP, WMS, PIM, CRM, ...)
- **Right side**: 3rd-party applications

## Existing templates

This list grows over time — rather than duplicate it here (and have it go
stale), run:

```bash
python3 ../scripts/describe_template.py --list
```

to see every template currently in this folder, with each frame's size and
top-level group/slot count.
