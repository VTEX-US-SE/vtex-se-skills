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
  They're part of the Ai Atlas Claude plugin, maintained by its own owners. Copying them here would create a
  second copy that drifts (see `CONTRIBUTING.md`, "Hard dependencies on externally-maintained skills").
  Without them, the skill searches the documentation directly.
- **Validation and write-back scripts: not shipped yet.** The skill lists the checks to run by hand under
  "Validation gates". Generalized scripts are planned for a follow-up PR.

## Common questions

**Why doesn't it answer in English by default?**

The prose is pasted into the client's matrix and read by their evaluation committee, so it goes in the
language of their document. The skill confirms that with the SE. When the SE reviews before delivery, it
drafts in the SE's working language and translates once, after review, so the two versions can't drift apart.

**Why is it stricter about "not supported" than about "supported"?**

On real runs, the costly mistake was refusing things VTEX actually publishes, not inventing capabilities.
That's why a "not supported" answer needs two separate searches first.

## Author

Djan Magno, built iteratively across real EMEA/APAC RFPs between July and August 2026 (from 109 up to 800
requirements), with review feedback from the SE team. The original lives in Djan's SE Co-pilot working folder.
The copy here is the canonical one from now on.
