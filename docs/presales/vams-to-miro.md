## What it does

`vams-to-miro` turns a VAMS (VTEX Architecture Modeling Specification) JSON architecture document
into a real Miro board, using the Miro MCP tools and a predefined layout template. It snaps VAMS
nodes onto a template's pre-positioned "group" regions and "slot" shapes so generated diagrams stay
visually consistent across architectures instead of reinventing a layout every time. Containment
follows the VAMS document's real `parent` hierarchy as a hard invariant — a node always renders
nested inside its actual parent's box, never by name-matching alone, and the template is only a
positioning suggestion, never an override of real structure. It also handles the reverse flow: no
VAMS file yet, pick a template first, then describe the architecture to fill it in.

## When to reach for it

Fires on "generate the Miro diagram for this architecture", "draw this VAMS file in Miro", "create
a board from this architecture JSON", "visualize this solution architecture", or after producing a
new VAMS document when the user wants to see it visually.

## Prerequisites

- **Miro MCP tools** (`board_create`, `layout_get_dsl`, `layout_create`).
- **Python 3**, stdlib only — no pip installs needed.
- It's used as a dependency of [solution-design](./solution-design.md) specifically for the final,
  consolidated project architecture diagram, but works standalone for any VAMS document.

## Reference files

| File | Purpose |
|---|---|
| `references/vams-spec-summary.md` | Summary of the VAMS spec |
| `references/vams-miro-shape-mapping.json` | Maps VAMS node types to Miro shapes |
| `references/vams-miro-connector-mapping.json` | Maps VAMS relationships to Miro connectors |
| `references/solution-architecture.schema.json` | JSON schema for the architecture document |

`scripts/` holds the Python implementation (`select_template.py`, `describe_template.py`,
`clean_template.py`, `generate_layout_dsl.py`, `vams_common.py`). `templates/` holds the
pre-built layout templates (`b2b-basic`, `b2b-headless`, `b2b-franchise`, `b2b-headless-franchise`,
`b2c-basic`, `b2c-headless`, `b2c-franchise`, `b2c-headless-franchise`), each a reference board
someone already designed by hand.

## Author

Miguel Carrera / João Guilherme Porto — shared as a dependency of `solution-design` in `#global-se`
(26/08/2026).
