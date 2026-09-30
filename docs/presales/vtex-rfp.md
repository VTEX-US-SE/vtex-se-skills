## What it does

`vtex-rfp` drafts answers to an RFP, RFI or security questionnaire, one requirement at a time. Each answer is
grounded in VTEX's published documentation (via the VTEX Developer MCP) or the Trust Center, carries a source
URL for every factual claim, and gets a coverage value in the client's own scoring vocabulary. The output is a
draft for the SE who owns the opportunity. It is never a client-ready file.

Around the per-row answering, it does the work that decides whether the answers hold up:

- reads the client's original document first (language, countries, architecture intent, their scale)
- pulls prior contact (Rocketlane, Granola, Drive) and precedent from comparable VTEX clients (Atlas, Slack)
- proposes an architecture and solution set and asks the SE to confirm it before any row is written
- rolls up coverage with the arithmetic visible, and groups the rows that need human judgment into a review
  queue

Every rule in the skill comes from a measured failure on a real run (false refusals, dead links to unpublished
pages, legacy documentation, gaps bleeding across rows, verdicts restated in prose), and the skill says which.

## When to reach for it

Fires when someone pastes RFP/RFI requirements, a security questionnaire, or a requirements matrix and wants
VTEX's answers.

It handles mixed documents section by section. Functional sections get the full workflow. Security
questionnaires skip the architecture discussion and go to SE review row by row. Pricing, contract and legal
questions are not answered; they're flagged for the SE to direct. The SE chooses whether to review in chat, in
Google Sheets or Excel, or both.

| Your situation | Where to go |
|---|---|
| Answer the client's matrix requirement by requirement, with coverage values | `vtex-rfp` |
| Write the narrative, persuasive architecture document for the same opportunity | [`solution-design`](./solution-design.md) |
| Map who decides on the client side before or during the RFP | [`stakeholder-scout`](./stakeholder-scout.md) |

## Prerequisites

- **VTEX Developer MCP** (`vtex-developer`): required. Without it the skill stops rather than answering from
  memory.
- **Optional connectors**, read only: Rocketlane, Granola, Google Drive, Slack, and `atlas-agent`. Each one
  adds context. The skill says so when one is missing and keeps going.
- **`vtex-architect` and `vtex-expert`**: optional. **External prerequisite, not bundled in this repo.**
  They ship in the Ai Atlas Claude plugin, which the Atlas team maintains (the same maintainer as
  `vams-to-miro`, see [`solution-design`](./solution-design.md)). It's released from
  `vtexprojects/ai-atlas-integrations` as a "Claude Plugin" GitHub Release, and you install it by opening the
  `.plugin` file. Copying them here would create a second copy that drifts (see `CONTRIBUTING.md`, "Hard
  dependencies on externally-maintained skills"). Without them, the skill searches the documentation directly.
- **Python 3 and `curl`**, only to run the scripts. Stdlib only, nothing to install.

## Reference files

| File | Purpose |
|---|---|
| `templates/rfp.config.example.json` | Per-RFP config: the client's coverage scale mapped to roles, field names, row-ID pattern, locale, extra patterns in the client's language, the confirmed architecture, and the write-back column mapping |
| `scripts/corpus.py` + `scope_guard.py` | Local copy of the cited VTEX pages; refuses hidden, unpublished and legacy / out-of-scope pages |
| `scripts/derive_evidence.py` | Derives each row's evidence URL from the page containing its quote |
| `scripts/validate_draft.py` | The main gate before anything reaches the client's file |
| `scripts/gap_scope.py` | Stops a gap from spreading across capabilities |
| `scripts/sync_registry.py` | One canonical verdict per capability across sections and workers |
| `scripts/verify_quotes.py` | Checks each quote on the live page the evaluator will open |
| `scripts/rollup.py` | Step 4 coverage numbers with the arithmetic shown |
| `scripts/write_back.py` | Writes into a copy of the client's `.xlsx` without dropping drawings or tables; derives the Owner column |
| `scripts/edit_row.py` | Applies an edit the SE asks for in chat, logs it, and re-checks the row at once |
| `scripts/handoff.py` | Freezes the review workbook sent to the SE and reads their edits back with a three-sided diff, so later edits of ours are never reverted |
| `scripts/tests/test_gates.py` | Seeds one bad row per check and asserts it is rejected |

## Author

Djan Magno, built iteratively across real EMEA/APAC RFPs between July and August 2026 (from 109 up to 800
requirements), with review feedback from the SE team. The original lives in Djan's SE Co-pilot working folder.
The copy here is the canonical one from now on.
