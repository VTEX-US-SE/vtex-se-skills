---
name: solution-design
description: Use this skill whenever a Solution Engineer asks to build, draft, outline, or update a Solution Design document for an RFP/RFQ opportunity, including requests like "create the solution design", "let's start the SD for [customer]", "draft the architecture section on X", "map the integration for Y", or "add the RFP coverage appendix". Trigger it even if the user only asks for one section (e.g. "write the multi-seller section") since that section still needs to be produced with this workflow's research and validation steps. This is a pre-sales deliverable, not the RFP response itself. Do not use the RFP-matrix, requirement-by-requirement skill/workflow for this; use this skill for the narrative, persuasive, technically-deep architecture document.
version: 0.2.0
---

# Solution Design Generator

Produces a technical, persuasive, pre-sales Solution Design document for an enterprise RFP
opportunity. This is the deliverable that shows a technical buyer's committee that VTEX's
architecture is the right fit, with enough depth to be credible and enough narrative discipline to
stay persuasive rather than becoming a spec sheet.

This skill does not have a fixed table of contents, and it does not copy RFP section headings
directly into the document either. Every opportunity gets its own section list, derived by
understanding the opportunity's context, weighing the relevance of what the RFP actually asks for,
and including whatever foundational sections the deal's nature calls for, even ones the RFP never
names as a heading. A global opportunity leveraging VTEX's native B2B capabilities needs a Global
Readiness section and a B2B Buyer Portal section whether or not the RFP has a chapter called
either of those things. **Never reuse a previous project's section list as a template. Derive it
fresh from this project's documents and context (Phase 1), then let the SE approve or redirect it.**

## Operating principles (read before starting)

1. **Sections come from judgment, not from copying RFP headings or a fixed template.** Read the RFP
   and the architecture note, understand what kind of opportunity this actually is, weigh how
   relevant each RFP theme really is, and draft a section list that reflects both, including
   necessary foundational sections the RFP itself never names. `references/architecture-decision-catalog.md`
   is a memory-jog for Phase 1, not a checklist to work through mechanically. Present the draft
   list to the SE for approval or redirection before writing anything. **This holds even when a
   past Solution Design is available as a style reference (principle #9): a reference calibrates
   tone and depth, never section structure.**
2. **Each approved section becomes its own complete document.** Build every section, core or
   deep-dive, as a standalone file with full prose, mandatory tables, and embedded diagrams, not a
   chat draft and not a bare-bones Google Doc section. There is no reliable way to append to an
   existing document, so build each new section aware of every section already approved before it:
   consistent terminology, no re-explaining a boundary already established, correct
   cross-references to where things actually live, so that when the SE copies everything into one
   final document in order, it reads as one coherent argument, not a stitched-together set of
   files. Track every decision in the decision log as you go, not just at the end.
3. **Batch validation checkpoints. Don't stop after every micro-decision.** Validate at three
   points: (a) the proposed section list, (b) the full set of architectural decisions together,
   (c) the full set of integration mappings together. Don't interrupt the SE after every single
   item.
4. **Never assert specificity the customer hasn't confirmed.** Before describing any external
   system's interface, mechanics, or data model, check the Q&A doc for what's actually been
   disclosed. If it's undisclosed, describe VTEX's readiness across the plausible patterns rather
   than presenting one as defined fact. Flag these as open items in the decision log.
5. **The customer-facing document never sounds uncertain, even about things that genuinely are.**
   This is distinct from principle #4. Once something is written into the deliverable, state it
   plainly and confidently. Hedges, "one thing I want to flag rather than assume," visible
   back-and-forth about what might be true: none of that belongs in the document itself. Open
   questions, caveats, and things still awaiting confirmation live in the decision log and get
   raised to the SE directly in conversation, never narrated inside the deliverable.
6. **This is pre-sales, not the RFP response.** No requirement-by-requirement walkthrough. Mention
   specific requirements only to demonstrate command of the brief. Gaps are fine to name but should
   be framed as scoped customization or third-party integration, not dwelt on. The document's
   center of gravity is why VTEX fits.
7. **Every integration point gets a boundary table. This is mandatory, not a default to reach
   for.** See `references/boundary-table-pattern.md`. Any section describing how VTEX talks to an
   external system of record is incomplete without one. This is the single most persuasive
   recurring device in past successful Solution Designs, and integrations are exactly where a
   technical buyer's committee is testing whether VTEX is honest about ownership boundaries.
8. **Ground every section in the VTEX Developer MCP and the RFP content, if one exists. Never in
   general web search.** The MCP is the required source for anything about native VTEX capability.
   If a narrow `tool_search` query doesn't surface it, retry with a broad single-word query
   ("VTEX") before concluding it's unavailable. If it's genuinely not accessible after that,
   **stop and tell the SE directly** so they can check the connection. Do not substitute general
   web search as a workaround. Web search does not produce the depth this document needs, and a
   section built on it will need to be rebuilt.
9. **Reference case studies, verified for product-generation match.** Don't rely on memory for
   which VTEX customer stories are analogous, research it fresh per Phase 3. If the SE points to a
   past Solution Design or diagram as a reference, use it only to calibrate tone, depth, and visual
   convention. **Never use it as a section-structure template.** Section structure always comes
   from this project's own Phase 1 analysis, whether or not a reference exists; see principle #1.
   When a case study is being used to support a claim about a specific product surface (Buyer
   Portal vs. B2B Suite, a particular API generation), verify the case study customer is actually
   running that surface. A forced or mismatched analogy is worse than no case study at all.
10. **Architecture decisions are a discussion, not a unilateral recommendation.** Before writing any
    section that hinges on an architectural decision, talk through the real options with the SE
    first. Most of the time the SE already has a direction. The SE decides not just which option
    to go with, but how the final document should present it: a single confident answer, or
    multiple options with one clearly recommended. Don't default to always presenting options, and
    don't default to always presenting one answer. Ask.
11. **The RFP Coverage Appendix never touches the SE's numbers.** If this opportunity has an RFP,
    this appendix is mandatory, always structured the same way, and always placed immediately
    after the Conclusion. The classification numbers (Out of the Box, Custom, Roadmap, Not
    Supported, by category) always come from the SE. This skill builds the standardized format
    and narrative around those numbers; it never generates, adjusts, or reclassifies them.
12. **Diagrams: build them yourself, except the one that has to live in Miro.** Every section-level
    diagram can be built directly, whatever tool actually produces the right result for that
    diagram. The one exception is the final, consolidated architecture diagram for the whole
    project: that one is mandatory in Miro, because it needs to stay maintainable and updatable
    after delivery. The best way to get that specific diagram right is still being worked out (see
    Phase 5). Treat it as a maintained, evolving step, not a solved one, and keep the checkpoint
    before finalizing it regardless of which approach produces it.
13. **Brand colors are fixed. Use exactly these, verified against brand.vtex.com:** Rebel Pink
    `#F71963` (primary), Serious Black `#142032` (secondary), Soft Pink `#FFF3F6`, Yogurt Pink
    `#FFE0EF`, Bubble Gum Pink `#FFC4DD` (all derived from Rebel Pink), and grays and blues derived
    from Serious Black: `#787C89`, `#C3C6CC`, `#DFE9F8`, `#F5F9FF`. Headings use Rebel Pink (H1)
    and Serious Black (H2); table headers use Serious Black with white text; hyperlinks use Rebel
    Pink. A technical architecture diagram legitimately needs more simultaneous colors than a
    marketing composition would; that's fine, this palette is what to draw from.
14. **Plain ASCII only, everywhere, including chat.** No em dash, no en dash. Use a comma or start a
    new sentence instead. Write ranges as "A to B," never with a dash. No curly quotes, no
    ellipsis character, no other typographic symbols. This applies to every document this skill
    produces and to conversation with the SE while producing it.
15. **Check for a Deliverables folder before assuming one exists.** Not every project has one
    created yet. Look for it under the project's Drive folder first; if it isn't there, create it,
    then use it for the decision log and every document this skill produces.
16. **The SE chooses the language.** Don't default to English. Confirm which language the Solution
    Design should be written in during Phase 0, and hold that choice throughout every section and
    the appendix.

---

## Phase 0 - Intake and Context Gathering

Before anything else, confirm you have (or can get) all source material. Ask the SE directly for
anything missing rather than guessing:

- The RFP/RFQ document(s) and the sourcing brief, if this opportunity has one
- The Q&A document (critical: this is where "confirmed vs. withheld by the customer" lives, see
  principle #4)
- Any architecture or ecosystem note from the customer
- **The exact file(s) where the RFP was already answered** (matrix or narrative). Ask explicitly if
  not obvious, since Solution Design should stay consistent with prior answers, not contradict them
- Whether project knowledge or Drive already has these, or they need to be located
- **Confirm the VTEX Developer MCP is actually accessible right now.** Don't discover this
  mid-Phase-4. If it isn't, tell the SE immediately (principle #8)
- **Ask whether the SE wants to point to a past Solution Design or diagram as a style reference**
  for tone, depth, and visual convention. If they do, treat it strictly as that; Phase 1 still
  derives this opportunity's own section list fresh, regardless (principle #9)
- **Ask which language the Solution Design should be written in** (principle #16)
- **Check whether a Deliverables folder already exists under this project's Drive folder.** If not,
  create one (principle #15)

Read everything before proceeding. Do not start drafting on a partial picture.

## Phase 1 - Section Planning

1. Understand the opportunity itself first: scale, region(s), business model, what kind of deal
   this actually is, not just the RFP's literal table of contents.
2. From the RFP and architecture note, identify the actual themes this opportunity requires: which
   architectural decisions need to be made, which native VTEX capability areas are central, which
   external systems must integrate, and which foundational sections this kind of opportunity needs
   regardless of whether the RFP names them (a global, multi-region B2B deal needs Global Readiness
   and B2B Buyer Portal sections on their own merits).
3. Weigh relevance, don't just enumerate. A theme the RFP mentions once in passing doesn't need the
   same section-level treatment as one it returns to repeatedly.
4. Cross-reference against `references/architecture-decision-catalog.md` only as a memory-jog.
5. Draft a proposed section list (typically 8 to 14 major sections plus the mandatory RFP Coverage
   appendix, if this opportunity has an RFP; see Phase 9).
6. **Validate the section list with the SE before drafting anything.** This is checkpoint 1 of 3.
   Expect and invite redirection, not just approval.

## Phase 2 - Architectural Decision Mapping

Map every decision this opportunity actually requires a stance on, e.g. headless vs. white-label
frontend, single account vs. multi-account, native vs. third-party partner or seller management
layer, native vs. external CMS.

**Discuss before writing, don't just recommend.** Most of the time the SE already has a direction.
For each decision:

- Talk through the real options with the SE
- Let the SE decide which option to go with
- Let the SE decide how it should read in the document: one confident answer, or multiple options
  with a clear recommendation
- Ground whichever direction is chosen in VTEX Developer MCP documentation (fetch the actual docs,
  don't rely on memory for API or protocol specifics)
- Note trade-offs honestly, in the conversation with the SE, not as visible hedging in the document
  itself (principle #5)

**Validate the full set of decisions with the SE together.** This is checkpoint 2 of 3. Record each
validated decision in the decision log immediately after validation, not at the end of the project.

## Phase 3 - Reference Case Study Research

For each major architectural theme or integration pattern in this document, search for VTEX
customer stories that are genuinely analogous. Don't default to whichever case studies were used
last time.

- **Google Drive**: `search_files` for prior case study writeups, competitive battlecards, or
  reference architecture notes already saved by the team.
- **Slack**: `slack_search_public_and_private` with queries combining the architecture pattern and
  "case study," "reference," or customer names. Read full threads with `slack_read_thread` when a
  result looks relevant; the real color is often in the replies, not the original message.
- **Web**: VTEX's own commerce-executive-stories pages and vtex.com product pages for public-facing
  versions of the same stories.

Prioritize cases where the industry vertical, scale, or architectural pattern is genuinely close to
this opportunity. A forced analogy is worse than no case study. **If a case study is backing a
claim about a specific product surface** (Buyer Portal vs. B2B Suite, a particular API generation),
verify the case study customer is actually running that surface before citing it; don't assume from
general familiarity with the account. Use these findings to ground recommendations in Phase 4 and
to build the Conclusion in Phase 6.

## Phase 3.5 - Decision Log

Maintain a lightweight running decision log as a Drive doc in the project's Deliverables folder
(e.g. `[Customer]_SolutionDesign_DecisionLog`; check principle #15 first if you haven't confirmed
this folder exists yet). After each validation checkpoint, append: what was decided, why, and any
open items still awaiting customer disclosure (per principle #4). Mark entries that exclude a
specific reasoning path (e.g. "data residency explicitly excluded as a justification") clearly
enough that they read as a hard constraint, not just a note.

**This log has an active job, not just an archival one.** Before regenerating, expanding, or
touching any section that relates to a previously-logged decision, re-read the relevant entry
first. Don't let a later pass quietly reintroduce reasoning that was already excluded. This is what
lets any session, yours or a teammate's, pick up the project without re-litigating settled
questions.

## Phase 4 - Section Drafting

Build one section at a time, fully, as its own complete document:

1. **Research first.** Use the VTEX Developer MCP (`fetch_document` with exact URLs is more
   reliable than keyword search) for the native capability being described, and the RFP/Q&A content
   for anything customer-specific. If the MCP doesn't surface via a scoped search, retry with a
   broad query before concluding it's unavailable (principle #8). Never substitute general web
   search for MCP depth.
2. **Write the section at full depth** in a real document: solid, detailed, persuasive prose, not a
   bullet outline and not a chat reply calibrated to "normal message" length. Use the boundary-
   table pattern (`references/boundary-table-pattern.md`), mandatory, not optional, wherever an
   external system is involved. Use tables for protocol endpoints, decision-factor comparisons, and
   step sequences.
3. **Build every diagram this section needs directly** (see Phase 5) and embed it in the document.
   Don't leave a placeholder for someone to build later, except for the one project-wide
   architecture diagram that belongs in Miro.
4. **Write with every previously-approved section in mind.** Match terminology exactly, don't
   re-explain a boundary or mechanism already established earlier, and make sure any
   cross-reference actually points at where that content lives. This section needs to read as a
   continuation of an existing argument, not a fresh start.
5. Where the section touches an undisclosed customer system, apply principle #4 explicitly and flag
   it in the decision log. Keep the prose itself hedge-free per principle #5.
6. **Get SE approval on this section before moving to the next one.** Log the outcome, then move
   on. Don't circle back to polish tone yet, that happens in consolidation.

## Phase 5 - Diagramming

Two different things, handled two different ways:

**Section-level diagrams.** Build these yourself, directly, as part of drafting that section
(Phase 4.3). Use whichever approach actually produces a clear, correct result for that specific
diagram; there's no single mandated tool here.

**The final, consolidated project architecture diagram.** This one is mandatory in Miro, because it
needs to stay maintainable and updatable by the team after delivery, not locked inside a static
image. The `vams-to-miro` skill is the current attempt at this and should be kept and maintained,
but it hasn't reliably produced the right result on the first try. Treat the actual approach (VAMS-
driven template matching vs. a hand-composed layout vs. something else) as still being tuned, not
settled. Whichever approach is used:

- Use the brand colors from principle #13
- **Validate with the SE before considering it final.** Diagrams are easy to get subtly wrong on
  data flow direction or ownership, and this is the most visible artifact in the whole deliverable
- If the SE has pointed to a past reference diagram (principle #9), use it to calibrate the level
  of detail and visual convention only, never to copy its actual structure or content

## Phase 6 - Consolidation

The SE merges the individually-approved section documents into one final document, in order. Once
that merge happens, **request the mandatory pre-delivery merge-coherence pass.** This is not
optional and not "if there's time":

1. **Renumber every figure to one consistent scheme** across the whole document. Merged sections
   will otherwise each have their own restarted or differently-styled numbering.
2. **Verify every cross-reference actually resolves** to where it claims. Merged content frequently
   has stale references pointing at a section number that meant something different in the
   original standalone file.
3. **Search for content duplicated across sections** (the same mechanism explained twice, often
   near-verbatim, because two sections were drafted independently) and consolidate to one
   explanation with a cross-reference from the other.
4. **Flatten heading levels** wherever a merged section's own top-level heading is now sitting three
   or four levels deep in the combined document.
5. Add connective narrative between sections so the document reads as one argument.
6. **Write the opening framing and the Conclusion last**, once every section's actual content is
   known. This is where Phase 3's case-study research pays off, tying architecture decisions back
   to proof points. Confirm first whether the SE or sales owns the executive framing; don't assume
   it defaults to this skill.

## Phase 7 - Brand and Voice Pass

- Heading hierarchy and colors per principle #13
- Correct VTEX terminology throughout (Trade Policies, Sponsor Account/Edition Apps, Payment
  Provider Protocol, BYOIDP, etc.; never approximate these)
- Confirm the hedge-free tone rule (principle #5) held throughout. Re-read for any surviving "one
  thing worth flagging," visible uncertainty, or narrated doubt, and move it to the decision log if
  it's still there
- Confirm plain ASCII throughout (principle #14): no em dash, no en dash, no curly quotes
- Does each section open with the customer's context rather than a VTEX capability? Is the customer
  positioned as protagonist? Is jargon defined on first use? Are "leverage," "seamless,"
  "best-in-class," "game-changing" absent?

## Phase 8 - Consistency QA Pass

Run alongside or immediately after Phase 6's merge-coherence pass:

- Same account architecture decision referenced consistently everywhere it comes up
- Same protocol and field names used verbatim across sections
- No section quietly re-opens a decision that was already validated and closed (check the decision
  log, principle #10 and Phase 3.5)

## Phase 9 - RFP Coverage Appendix

**Mandatory whenever this opportunity has an RFP. Always placed immediately after the Conclusion.
Always the same structure.** This section should look the same across every Solution Design this
skill produces:

- Methodology note explaining the classification categories
- Headline aggregate numbers
- A per-domain narrative: where VTEX's native platform is the differentiator, and where its
  extensibility and composability close the gap, framed as architecture, not apology
- **The classification numbers themselves always come from the SE.** This skill never generates,
  infers, or adjusts them, and never reclassifies an item to change a reported percentage. If a
  detailed row-by-row table would be overwhelming or isn't meant for customer eyes, the SE decides
  what level of granularity actually goes in; this skill just needs to know which, not decide it.

## Phase 10 - Delivery

Each approved section already exists as its own complete document (Phase 4). The SE merges them
into the final document, requests the merge-coherence pass (Phase 6), and remains the final
approver before anything goes to the customer.

---

## Reference files

- `references/boundary-table-pattern.md`: the "VTEX role vs. customer owns" table pattern, with a
  template and worked example. Mandatory for every integration point (principle #7).
- `references/architecture-decision-catalog.md`: a menu of architectural decision themes and
  native-capability areas to check against the RFP during Phase 1 (not a checklist to fulfill).
