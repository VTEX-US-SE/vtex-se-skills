<!-- Production script template: the start of every from-scratch video. Copy it to
     `<video-folder>/production-script.md` and fill it in. Don't write narration before the research
     pass: "Sources & Verification" is the input the narration comes from, not an appendix.
     generate_tts.py reads the ">" blockquote under each "**Narration:**" line mechanically, so keep
     that exact shape and never put bracketed stage directions inside a narration blockquote: TTS
     reads them aloud. -->

# Production Script — {{VIDEO_TITLE}}

> Status: {{DRAFT | IN REVIEW | RECORDED | DELIVERED}}. Once delivered, add the final video link
> here and treat this file as historical — corrections to a delivered script go in a new dated file,
> never edited in place (same immutability rule as everything else this pipeline produces once a
> pilot is marked complete).

**Format:** {{e.g. "Shark Tank" pitch — differentiators-focused, not a full product walkthrough}}
**Recording language:** {{English / other}}
**Target duration:** {{e.g. 7-10 min}}
**Quality reference video:** {{link to a video whose pacing/structure you want to match}}

---

## Pre-recording checklist

- [ ] Research pass complete for every claim below (see "Sources & Verification") — nothing goes to
  narration on inference alone
- [ ] All slides described in `slides.json` (copy `templates/slides.example.json`) and built with
  `scripts/build_slides.py` — see "Slides to build"
- [ ] All URLs/admin panels needed for the recording open and access-confirmed
- [ ] Narration generated with `generate_tts.py` and each segment's real duration read from
  `audio/tts_manifest.json` (see "Recording Cue Sheet")
- [ ] Script grepped for leftover persona names and bracketed stage directions

---

## SEGMENT 0 — Hook ({{start}}–{{end}})

**Screen:** Slide 1 (opening) — see spec below.

**Narration:**
> {{Hook narration. What's the pain/opportunity, in one paragraph, ending with a transition into
> the first proof point.}}

## SEGMENT 0.5 — Quick capability map ({{start}}–{{end}}) — optional

Only include this if the video needs a short "here's what you'll see" orientation before diving
into the first client/topic — skip it if the format is short enough that a map would eat into the
proof segments' budget.

> Pick ONE of 3 validated formats (see references/from-scratch-flow.md, evidence from 8 real videos): a **numbered
> agenda** (01/02/03 — best for 3+ discrete capabilities), a **pain-point/persona** slide (best when
> the audience needs to feel the problem before the product), or a **numbered flow** (1→2→3 — best
> for a sequential journey). Whichever you pick, add one social-proof element (a stat, a client
> logo, or a short "market reference" callout) — its absence is a documented weak point, not a
> stylistic choice to skip.

**Screen:** Slide 2 (capability map) — see spec below.

**Narration:**
> {{One sentence per capability you're about to prove live, ending with a transition line like
> "Let's see them live."}}

## SEGMENT N — {{Client/topic name}} ({{start}}–{{end}})

**Screen:** {{live navigation target — URL or admin path}}

**What to show, in order:**
1. {{Step 1 — be specific: exact button/field/menu, not "navigate around"}}
2. {{Step 2}}
3. {{...}}

**Narration:**
> {{Narration for this segment. Write it describing its own action — "Let's search for X" right
> before the action it cues — not as a separate stage direction in brackets. This works better when
> whoever is recording is alone, following the script and replicating it manually on screen.}}

`[VERIFICATION NOTE]` {{Every non-obvious claim in this segment's narration needs a note here: what
was checked, against what source, and the result. E.g. "Confirmed via [source] — the client runs X,
not Y as initially assumed." or "NOTE: confirm the exact selector text live before recording — not
yet verified." Never let a claim reach the narration above without one of these.}}

*(repeat "SEGMENT N" for every client/topic segment the video needs)*

## SEGMENT — Closing / CTA ({{start}}–{{end}})

**Screen:** Slide 3 (closing) — see spec below. Consider a "bookend" effect with Slide 2 (same
capability map, now with proof/logos under each capability).

**Narration:**
> {{Recap the capabilities with the specific proof from each segment, land on one connecting idea
> that ties the segments together, close with a call to action.}}

---

## Slides to build

Describe every slide in `slides.json` (copy `templates/slides.example.json`) and build it with
`scripts/build_slides.py` — never design from scratch or hand-write the palette. Available types:
`opening`, `split` (two columns), `grid` (numbered cards, Hyperframes only) and `closing`. See
references/slides.md.

### Slide 1 — Opening (Segment 0)
- Title: {{big title}}
- Subtitle: {{one line}}
- Presenter credit (optional)

### Slide 2 — Capability map (Segment 0.5, if used)
- Title: {{e.g. "How VTEX powers X"}}
- One block per capability you'll prove live: {{label}} — {{one-line description}} — {{which
  segment proves it}}

### Slide 3 — Closing (Segment N)
- Same layout as Slide 2 (callback effect) — add proof (logo/name) under each capability block
- Final CTA line + link

---

## Recording Cue Sheet (narration ↔ screen sync)

This is audio-first: generate the narration, then size every slide and demo clip to the real
measured duration in `audio/tts_manifest.json`. A words-per-minute estimate is only for drafting
toward the target runtime, never for sync.

| Segment | Budget | Real narration (manifest) | Visual | Clip plan |
|---|---|---|---|---|
| 0 — Hook | {{Xs}} | {{s}} | Slide 1 | {{Hyperframes / PNG}} |
| N — {{name}} | {{Xs}} | {{s}} | {{live demo stills}} | {{still 1 → X s, still 2 → Y s}} |
| Closing | {{Xs}} | {{s}} | Slide 3 | {{...}} |

**Total real duration**: {{sum}}. Compare it against the target at the top. A segment over budget
is fine if there's slack elsewhere, but note it rather than letting the whole video drift.

---

## Sources & Verification

List every source actually checked for this script — this section is the audit trail, not an
afterthought. Update it as research happens, before writing the narration that depends on it.

- {{Official VTEX documentation (developers.vtex.com, help center) — what it confirmed}}
- {{Internal knowledge base entry (Atlas) / ADR / architecture doc — what it confirmed}}
- {{Shared deck / official slide source, if slides are being duplicated from one}}
- {{Direct screenshot/first-hand confirmation — from whom, of what, when}}
- {{Live fetch of a public URL — confirms the domain loads / the stack is what's claimed}}

**Source hierarchy**: a final narration claim must rest on official VTEX documentation,
product-team material, or a live test. A colleague's demo, deck or recording is a lead to
investigate, never the sole basis for a line.

**Rule**: a claim only earns a narration line once it has one of the above next to it. If you can't
point to a specific verification for something you want to say, either don't say it, or mark it
`[NOTE] not yet verified` and resolve it before recording — never let an unverified claim sit
silently in the narration.

---

## Wrap-up

`[Once delivered]` Remove any earlier raw narration drafts that got fully superseded by the final
version above — keep the file to the version actually used for recording, and link the delivered
video + retrospective/lessons-learned note here.
