## What it does

`solution-design` produces a technical, persuasive, pre-sales Solution Design document for an
enterprise RFP/RFQ opportunity — the deliverable that shows a technical buyer's committee that
VTEX's architecture fits, with enough depth to be credible and enough narrative discipline to stay
readable. It's a structured process, not a template: it takes an opportunity from intake through
section planning, architecture decisions, case study research, section-by-section drafting with
embedded diagrams and tables, and a standardized RFP Coverage Appendix when the opportunity has
one. Every architectural decision gets discussed with the user before it's written, not handed over
as a fait accompli. Every integration point gets a boundary table showing what VTEX owns versus
what stays with the customer's system of record.

## When to reach for it

Fires on requests like "create the solution design", "let's start the SD for [customer]", "draft
the architecture section on X", "map the integration for Y", or "add the RFP coverage appendix" —
including when only one section is requested, since that section still needs the same research and
validation steps. This is the narrative, persuasive, technically-deep architecture document — it
is **not** the RFP response itself (requirement-by-requirement matrix answering), which is a
separate skill/workflow.

## Prerequisites

- **VTEX Developer MCP** — required. The whole point of this skill is grounding every section in
  real documentation, not general web search.
- **`vams-to-miro`** — used specifically for the final, consolidated project architecture diagram.
- **Miro MCP** — required for that diagram, via `vams-to-miro`.
- **Google Drive connector** — for reading RFP/Q&A source files and maintaining the decision log
  and deliverables folder.
- **Slack connector** — used during case study research.

## Reference files

| File | Purpose |
|---|---|
| `references/architecture-decision-catalog.md` | Catalog of architecture decisions this skill can draw on |
| `references/boundary-table-pattern.md` | The pattern for the VTEX-owns-vs-customer-owns integration boundary table |

## Common questions

**Why can't Claude just append every section into one Google Doc as it goes?**

Claude doesn't have the capability of appending sections to a single Google Doc, and a large
Solution Design is normally a big document. The current process creates multiple Google Docs (one
per session) and requires a manual consolidation pass into one final document afterward. HTML
intermediate files were tried (easier to append) but the HTML-to-Google-Docs conversion breaks down
at this document size. Open problem as of 28/08/2026 — no fix shipped yet.

## Author

João Guilherme Porto, shared in `#global-se` (26/08/2026, updated 28/08/2026 after a first round
of feedback). Already used to build the Solution Design for Santander's Global Loyalty Marketplace
and Ralph Lauren's Global B2B opportunity (both EMEA). Work in progress, not a finished product.
