---
name: vams-to-miro
description: Turns a VAMS (VTEX Architecture Modeling Specification) JSON architecture document into an actual Miro board, using the Miro MCP tools and a predefined layout template. Use this whenever the user has a VAMS architecture document (or asks to model one) and wants it drawn, visualized, diagrammed, or "put on a board" in Miro — phrases like "generate the Miro diagram for this architecture", "draw this VAMS file in Miro", "create a board from this architecture JSON", or "visualize this solution architecture" should all trigger it. Also handles the reverse starting point — the user has no VAMS file yet and wants to pick a template first, then describe the real architecture to fill it in. Also use it after producing a new VAMS document (e.g. with a VAMS-authoring skill) if the user wants to see it visually.
compatibility: Requires Miro MCP tools (board_create, layout_get_dsl, layout_create) and Python 3 (stdlib only, no pip installs needed).
version: 0.1.0
---

# VAMS → Miro

Renders a VAMS architecture document as a real Miro board by snapping VAMS
nodes onto a **predefined layout template** — a reference board someone
already designed by hand, with named "group" regions and pre-positioned
"slot" shapes for common services. This keeps generated diagrams visually
consistent across architectures instead of reinventing a layout every time.

**The template is a positioning guide, not a restriction — it only ever
suggests where something goes; it never overrides real hierarchy.**
Containment is **mandatory** and driven by the VAMS document's `parent`
attribute, never by node name. Three guarantees this script enforces as
hard, checked invariants, not just intentions:

- **A node with a `parent` always renders nested inside that real parent's
  box — never anywhere else, no matter what its name matches.** Only an
  actual VAMS root (no `parent` at all) may match a top-level template
  region directly — by name first, or by a `(type, environment,
  implementation)` classification inferred from the region's own rendered
  style when nothing matches by name (so a document's root literally named
  "VTEX Platform" is still recognized as the same kind of thing as a
  template region named "VTEX Core Services", both being a Platform in the
  vtex environment — see Step 2). If the template doesn't model a
  document's real top-level structure at all, that whole branch renders as
  new/auto-placed instead of using the template's positions for it —
  hierarchy fidelity always wins over template fit, deliberately, even
  when it means most of a template goes unused for a given document. This
  is normal, expected behavior, not a failure to fix.
- **Matching goes one real tree level at a time — a slot can never be
  claimed by skipping past an unmatched intermediate node to reach one of
  its children.** Once a region is matched, its own nested slots are
  checked only against the matched node's DIRECT children; a grandchild
  is never eligible just because no intermediate node claimed anything.
  Reaching straight through to a grandchild was tried and caused a real
  containment bug (a slot's exact position landed inside the *template
  region*, correctly, but NOT inside the real intermediate parent's own
  rendered box) — one level at a time is what keeps every node inside its
  own real parent, always.
- **Every child renders nested inside its own parent's box, never
  somewhere disconnected from it.** If a template-matched group's real
  children outnumber its predefined slots, the group's box grows (taller)
  to fit the rest underneath — the extras are never shipped off to some
  separate, unrelated section of the board.
- **Growing a box never creates a new overlap.** If making a group taller
  would run into whatever's positioned below it, that sibling — and
  everything nested inside it — gets pushed down far enough to clear it.
- **Before growing a group or creating a brand-new shape, a leftover real
  child (no name match) reuses one of that same group's own unused sibling
  slots, if one shares its exact style classification** (same type/
  environment/implementation — e.g. a leftover "G Pay" component can reuse
  an unused "Pricing Hub"-styled slot instead of extending the group or
  creating a fresh shape). Every slot in a classification bucket renders
  identically, so this is exactly as arbitrary as auto-placing it in a new
  grid cell — except it reuses a position the template already laid out,
  for free, and it's decided offline before anything is created, so the
  slot gets its real, final label from the start (no rename step, ever).
  Only applies to a leftover node with no children of its own — one that
  needs to become a container is sized from its actual content instead
  (see Limitations).

New groups, new platforms, an entirely unanticipated subsystem: all of it
is created, in full, correctly nested per the document's real structure,
never blocked or dropped.

**One narrow, verified exception to "only a root can match a top-level
region":** documents generated by the existing Miro→VAMS importer wrap
their entire content under one generic Group node named after the source
Miro frame — an export artifact of "the whole frame became a node," not an
intentional architectural concept. Left alone, that single wrapper would
block every real top-level concept beneath it (a document's actual VTEX
Platform, Merchant Channels, etc.) from ever matching anything, for every
document exported this way. Detected narrowly and verifiably — the
document's own `metadata.description` names the source frame, and the
wrapper's name must match it exactly, so a genuine user-authored top-level
Group is never touched — its direct children are promoted to real roots
for matching purposes; the wrapper node itself still renders in full, just
no longer as a blocking ancestor.

Read `references/vams-spec-summary.md` first if you're not already familiar
with VAMS's node/flow/dataEntity shape — it's short and has exactly what this
skill needs, no more.

## The template is never converted into a VAMS document — don't do this yourself either

This tripped up an earlier run of this skill, so it's worth stating flatly:
**a template is already a Miro diagram.** `generate_layout_dsl.py` reads its
raw JSON purely as geometry and style data (box positions, shape/fill/border
per item) — it is never parsed into VAMS `nodes`/`flows`, never treated as
if it were someone's real architecture, and never round-tripped through a
"convert template → VAMS → Miro" detour. Don't improvise that detour by
hand either (e.g. by calling Miro tools to read a template board live and
manually drafting a VAMS-shaped document from its shapes) — it accomplishes
nothing except badly re-deriving what the bundled template file already
has, and risks treating the template's own placeholder content (its
"Catalog"/"OMS"/etc. example labels) as if it were the user's real system.

The whole pipeline is one offline computation over two local files — the
VAMS document and the template JSON — producing one fully-resolved DSL,
created with a single `layout_create` call. No intermediate VAMS
representation of the template, no live read-back, no multi-step edit
sequence. Run `scripts/generate_layout_dsl.py`; don't reimplement any part
of what it does by hand.

## Why scripts, not free-hand DSL authoring or eyeballed template matching

Matching dozens of nodes against a template's geometry, scoring which
template fits an architecture best, and hand-computing non-overlapping grid
coordinates — recursively, for whatever the template didn't anticipate, with
its real hierarchy intact — are exactly the kind of deterministic,
error-prone-by-hand work that belongs in code. Use the bundled
`scripts/*.py` (stdlib-only Python, runs anywhere) — don't hand-place shapes
or eyeball a template choice yourself. `generate_layout_dsl.py` asserts, as a
hard internal check, that every single node in the document ends up placed
somewhere — it fails loudly instead of silently producing an incomplete
diagram. Every template's match score is written out for you to read and
relay, too.

All example commands below use `scripts/<name>.py`, relative to this skill
folder's own root (i.e. run with this folder as the working directory, or
adjust the path to wherever it's actually installed) — deliberately not a
path baked in from any one repo layout, since this skill folder is meant to
be copied/installed as a self-contained unit.

## Step 0: which board? (ask this first, before anything else)

Before touching the VAMS document or a template, find out where the diagram
should end up — this shapes what you call at the end of the workflow and is
worth settling before doing any analysis work:

- **A new board** — you'll call `board_create` later (with confirmation,
  since it's a real resource that can't be un-created).
- **An existing board** — get its Miro URL (and, optionally, whether it
  should go inside a specific existing frame there via `?moveToWidget=`).
  In this case `layout_create` targets that board directly and
  `board_create` is skipped entirely.

## Step 1: which starting point?

This skill supports two different entry points — figure out which one the
user is in (often obvious from what they've already given you: a pasted/
referenced VAMS JSON means Mode A; "I want to build one" or "let's start from
a template" means Mode B).

### Mode A — an existing VAMS document

Use this when the user already has (or you already produced) a VAMS JSON.

1. Sanity-check the document has `name`, `level`, and
   `architecture.{nodes,flows,dataEntities}` — full JSON Schema validation
   isn't required for diagramming, but if the user cares about strictness,
   check it against `references/solution-architecture.schema.json`. You
   don't need to handle two real-world quirks yourself — every script
   handles both automatically:
   - A file straight from `vams-miro-integration`'s Drive/GitHub export step
     is wrapped in an envelope (`{"architecture": <the whole VAMS
     document>, "clientId": ..., ...}` — note the outer `architecture` key
     holds an entire document, not nodes/flows directly). Unwrapped
     automatically; nothing to do.
   - A document generated by the existing Miro→VAMS importer wraps
     everything under one generic Group node named after the source Miro
     frame (an export artifact, not real modeling — see the intro above).
     Detected and promoted automatically when the document's own metadata
     confirms it (`generate_layout_dsl.py`'s report includes
     `frame_wrapper_unwrapped` when this happens — mention it to the user,
     it's a good thing, not an error).

2. **Auto-select the template — don't ask, run the numbers:**

   ```bash
   python3 scripts/select_template.py <path-to-vams.json>
   ```

   With no `--templates-dir`, this scans the `templates/` folder bundled
   inside this skill by default (pass `--templates-dir <dir>` instead to use
   a different/external template library). It scores every usable frame by
   how many of its **top-level group/slot names** have a same-named VAMS
   node somewhere in the document, with total-region match count as a
   tie-break. Take the top-ranked candidate. State it plainly rather than
   silently
   picking — e.g. "Using the 'Basic B2B' template — it matched 4 of 6
   top-level groups (Vtex Core Services, VTEX IO, B2B Core Modules, Merchant
   Back Office)." If the top score is weak (few top-level matches) or two
   candidates are close, say so and let the user override before continuing
   — this is auto-selection, not a blind guess the user can't correct.

3. Continue to **Step 2 (generate)** with the VAMS document and the
   auto-selected `(template file, frame title)`.

### Mode B — building from scratch against a template

Use this when there's no VAMS document yet — the user wants to pick a
template first and then describe the real architecture to fill it in.

1. **Ask the user to choose a template explicitly.** There's nothing to
   auto-match against yet, so list the candidates:

   ```bash
   python3 scripts/describe_template.py --list
   ```

   (see `templates/README.md` for how frames are found / which are excluded
   as legends) and let them pick.

2. **Show them the template's shape** so they know what to fill in:

   ```bash
   python3 scripts/describe_template.py \
     "<template filename>" --frame "<chosen frame title>"
   ```

   This prints every group and slot as a readable outline. Share it with the
   user (or the relevant parts, if it's long) and ask them to map their real
   architecture onto it: for each group/slot, what's the actual system or
   component (keep the same name to snap into that exact predefined
   position, or give it a different name — it'll still be drawn, just
   auto-laid-out below the template instead of at a hand-placed spot), plus
   anything extra the template doesn't cover, plus how things connect
   (data/event flows between them).

3. **Assemble a minimal VAMS document** from what they tell you — just
   enough structure to drive the diagram: `nodes[]` with `id`/`name`/`type`
   (and `parent` for anything nested under a group), `flows[]` with
   `id`/`type`/`origin`/`destination`. This doesn't need to be a
   fully-governed VAMS document (metadata, compliance tags, etc.) unless the
   user wants one for other purposes — if they do, that's a separate,
   heavier authoring task (a dedicated VAMS-authoring skill, if available, or
   a lot more back-and-forth), not something to fold into a quick diagram
   request. Say so if the user seems to want both.

4. Continue to **Step 2 (generate)** with the assembled VAMS document and the
   template the user picked in step 1 (no auto-selection needed — it's
   already fixed).

## Step 2: generate

```bash
python3 scripts/generate_layout_dsl.py \
  <path-to-vams.json> "<template filename or path>" \
  --frame "<template frame title>" \
  --title "<board title, defaults to the VAMS doc's name>" \
  --out /tmp/vams-board.dsl --report /tmp/vams-board.report.json
```

A bare filename (e.g. `b2b-basic.json`) resolves against the bundled
`templates/` folder automatically — no need to spell out the full path
unless you're pointing at an external template library.

Read the report:

- `nodes_snapped_to_slot` / `nodes_snapped_to_group` — a VAMS root matched
  a top-level template region (by name, or by a type/environment
  classification fallback — see above), exact predefined position; or a
  non-root matched a nested slot by name, scoped to its direct parent.
- `nodes_reused_spare_slot` — no name match, but reused one of that same
  group's own unused sibling slots sharing its exact style classification
  (see above) — still an exact predefined position, just not the one the
  template happened to label for it.
- `nodes_nested_under_matched_group` — no predefined slot and no same-
  classification spare available, but their real DIRECT parent matched a
  template region, so they're nested right inside that region's (possibly
  now-taller) box. `matched_groups_grown_for_extra_children` names which
  groups had to grow.
- `nodes_in_new_top_level_groups` — no template-matched ancestor anywhere;
  drawn as brand-new, self-contained groups further down the board.
  `new_top_level_group_names` names them.

These five counts always sum to `nodes_total` — the script enforces this
itself, so if you ever see it error out about an internal invariant, that's
a real bug to stop and report, not something to work around.

**Surface the split to the user before creating anything** — e.g. "2 nodes
snapped to predefined groups (one of them — 'VTEX Platform' — recognized
by type/environment even though the template's region is named 'VTEX Core
Services'), 62 more nested inside those groups because they're real direct
or indirect children, and 58 more are new relative to this template —
mostly the ERP/WMS/analytics back-office branch — all still fully drawn
and correctly nested per the document's real structure, just
auto-positioned. Want me to continue, or does a different/extended
template fit this document's structure better?" This isn't apologizing for
a gap — a low match rate is often just what
happens when a document's real hierarchy doesn't line up with a template
built around a different one, and that's fine — but it's still worth
flagging as "maybe a different template fits this document's shape better"
before spending a
board-creation action on it.

## Step 3: build it in Miro

Using the board target from Step 0:

- **New board:** confirm the title with the user, call `board_create`, then
  `layout_create` against the board it returns.
- **Existing board:** call `layout_create` directly with the `miro_url` the
  user gave you in Step 0 (with `?moveToWidget=<frame_id>` if they wanted it
  inside a specific existing frame).

Call `layout_get_dsl` once per conversation (skip it if you've already
called it earlier in this conversation — reuse the spec) so the exact syntax
is in context, then call `layout_create` with the DSL text from Step 2's
`--out` file as `dsl`. Set `invocation_source: "skill"`.

## Step 4: report back

Give the board URL and a short summary from the report (slotted / grouped /
nested / new-top-level-group counts). Name `matched_groups_grown_for_extra_
children` and `new_top_level_group_names` by their actual names (not raw
ids) so the user can see what's new relative to the template and decide
whether a different/extended template would fit better next time — not
because anything was lost, but because a template that covers more of the
architecture makes for a tidier diagram.

## Choosing/creating a template

Templates live in `templates/` **inside this skill folder** — bundled with
it, so importing/copying `skills/vams-to-miro/` anywhere brings a working
starter template set with it; no separate handoff needed. One JSON file per
exported reference board (can contain multiple usable frames). All three
scripts default to this bundled folder automatically; pass an explicit path
or `--templates-dir` only when you want to use a different/external template
library instead (e.g. a larger org-wide set maintained outside this skill
package). See `templates/README.md` for the full mechanics — in short:
templates are **real Miro boards someone designed and exported**, and
matching is by shape/group **name**, not by any manual node-to-region
mapping file. If no existing template fits the architecture's business
pattern well (Mode A's selection score will make this obvious — low
top-level match count, or the generation report shows lots of "Unmapped"),
say so and ask whether the user wants to design a new template in Miro and
export it (add it to this folder), rather than forcing a bad fit.

## Limitations (be upfront about these, don't paper over them)

- **Spare-slot reuse only ever applies to a leftover node with no children
  of its own.** A template slot's size was chosen for a simple leaf label;
  reusing it for a node that itself needs to become a growable container
  was tried and caused a real bug (the reused slot's fixed width doesn't
  flex for whatever that node's own children need — a wide sub-tree
  silently overflowed past its "parent" slot's right edge). A leftover
  node with real children of its own always goes through normal growth/
  auto-placement instead, which sizes its box from actual content.
- **The frame-wrapper exception only fires for the exact, verifiable
  Miro-importer signature** (`metadata.description` matching `Generated
  from Miro board ... (frame "X")`, and a root literally named `X`). A
  document that wraps everything under a generic top Group for some OTHER
  reason — hand-authored, or exported by a different tool — is left alone;
  that Group is treated as a real, intentional root like any other, and
  won't get this promotion. If a document like that scores unexpectedly
  low across every template, that's the likely cause — worth mentioning to
  the user rather than silently living with a bad auto-selection.
- **A node only gets its own predefined slot if the template models its
  exact position in its exact real hierarchy.** Otherwise it's still drawn
  — in full, correctly nested inside whatever real parent it has (growing
  that parent's box if needed), or as its own self-contained new group if
  nothing in its ancestor chain matched the template at all. This is
  expected, routine behavior for any document whose real structure doesn't
  line up 1:1 with the template's assumed shape, not a defect to fix.
- **Only an actual VAMS root can match a top-level template region — never
  a node with a real parent, no matter how well its name matches.** If a
  document models something (say "VTEX Platform") as the real parent of
  several services the template assumes are themselves top-level concepts
  (e.g. "VTEX Core Services", "B2B Core Modules"), none of those services'
  matching template regions get used for this document at all — the whole
  branch renders as one new, self-contained, correctly-nested group instead
  (see `new_top_level_group_names` in the report), UNLESS the document's
  root itself shares a `(type, environment, implementation)` classification
  with one of the template's top-level regions (a root named "VTEX
  Platform" with `type: Platform, environment: vtex` still recognizes a
  region named "VTEX Core Services" styled the same way as the same kind of
  thing). That fallback only ever applies at this top level, deliberately —
  see the next bullet for why. Even with it, a template that looks like a
  great fit by name can end up barely used once real hierarchy is
  enforced — that's the point, not a bug: hierarchy fidelity to the actual
  document always wins over template fit.
- **Matching inside an already-matched region is scoped to that node's
  DIRECT VAMS children only — one real tree level at a time, by name only,
  never a global search, and never the classification fallback.** A slot
  named "Orders" inside "VTEX Core Services" can only match a node that's
  a genuinely a *direct child* of whatever matched "VTEX Core Services";
  a same-named grandchild (reached by skipping past an intermediate node
  that didn't itself match anything) is never eligible, and neither is a
  same-named node living in a completely unrelated branch (e.g. an ERP
  system) — that slot just goes unused instead, and the node it would have
  wrongly caught still gets drawn, correctly nested under its own real
  parent. Classification-based matching is deliberately NOT used at this
  tier: a group's nested slots are typically many components sharing
  identical generic styling (every VTEX-native Component looks the same),
  so classification can't tell "Catalog" apart from "Pricing Hub" — trying
  it here was tested and caused real wrong reassignments (a legitimate
  extra component landing on an unrelated named slot purely by shared
  styling), which is why it's restricted to the top level only, where a
  template usually has just one distinctive region per classification.
- **Two candidates tied at the same scope (two regions, or two nodes,
  sharing a name with nothing to prefer one over the other) resolve
  deterministically but arbitrarily** — the same input always produces the
  same output, but which one wins isn't a meaningful signal. This matters
  more than you'd expect for regions: two hand-drawn "same row" boxes can
  be a fraction of a pixel apart in their raw coordinates, which used to
  decide the winner by accident before ancestor-chain scoring was added.
  For two real VAMS nodes sharing both a name AND a parent (e.g. a
  duplicated "VTEX IO" node), there's no signal left to break the tie with —
  rename one of them if it matters which gets the shared slot.
- **Auto-placed layout is a simple recursive grid**, not hand-tuned — it's
  meant to make new content clearly visible and readable, not to look as
  polished as the template's hand-placed slots.
- **Auto-selection (Mode A) only looks at name matches, not semantics** — a
  template can score well on matched group names while still being a poor
  fit for the actual business pattern (e.g. matching generic names like
  "Search" or "OMS" that show up across unrelated architectures). Treat the
  score as a strong hint to state and let the user confirm/override, not an
  infallible verdict.
