# From-scratch video — research, script, structure

## Flow

```
1 RESEARCH → 2 SCRIPT → 3 NARRATION (TTS) → 4 SLIDES → 5 DEMO STILLS → 6 ASSEMBLY → 7 QA
```

This is audio-first: narration is generated before visuals, and every visual is sized to the
measured narration. Prove steps 2→3→4→6 on slide-only segments before spending time on the live
demo capture.

## 1. Research

- Sources, in the order to reach for them: **official VTEX docs** (VTEX Developer MCP / developers
  portal / help center), **Atlas** (`atlas-agent` MCP: case studies, ADRs, which customers run
  which capabilities), **Google Drive** (official decks, e.g. success-case decks by industry),
  **Slack** (`#global-se` context), and **WebFetch** on the live site (does it load, is it really
  VTEX).
- Before relying on Atlas, make one real `retrieve_context` call and confirm it returns content.
  A missing error doesn't prove the connector is alive.
- **Source hierarchy for a final script line:** official VTEX documentation, product-team
  material, or a live test. A colleague's demo, deck or recording is a lead only. It tells you
  something exists; the line goes in once an official source or a live test confirms it.
- First-hand verification catches real mistakes. On one precedent, it caught 3 claims that
  would have gone in by inference (e.g. "search is external" when it was the opposite).

## 2. Script

Copy `templates/production-script-template.md` to `<video-folder>/production-script.md`.

- Research and script live in the same file. Every non-obvious narration claim gets a
  `[VERIFICATION NOTE]` saying what was checked, against what, and the result.
- Narration **describes its own action** ("Let's search for a kettle — instant results") instead
  of bracketed stage directions. Brackets inside a `> ` narration blockquote get read aloud by TTS.
- Write in an inclusive voice ("we're going to show you"), not first person singular.
- Tie the segments together with one conceptual thread in the close, and put a bridging line at
  every segment transition.
- Words per minute is only for drafting toward the target length. Sync comes from the real
  generated durations.

## Structure — evidence from 8 real team videos

Analyzed with a 16-frame contact sheet per video, made independently by 8 different SEs:

1. **Universal skeleton:** opening slide → concept block → demo → closing, in 7 of 8 videos.
2. **The middle varies:** linear (all concept slides, then one demo), interleaved (diagram ↔
   demo, back and forth), or stitched multi-demo (several accounts or brands glued together).
   Choose per video.
3. **Concept slide formats that recur:** numbered agenda (01/02/03), pain-point/persona, numbered
   flow (1→2→3). Nearly always with one **social-proof** element (a stat, client logos, a "market
   reference" box).
4. **A real demo always interleaves Admin ↔ storefront.** No video shows only one side.
5. **Closing with a CTA and a real demo (not mockups) are quality requirements.** The videos
   without them were exactly the ones flagged as weak in review.

Typical length: 2-10 minutes. A short capability piece (~2-3 min) is a valid format.

## 3-7

- Narration: `generate_tts.py <video-folder> --voice roger|sarah` (dry run), then add `--confirm`.
  See voice.md.
- Slides: slides.md. Demo stills: recording.md. Assembly and QA: assembly.md.
- Keep a `RECORDING_TASK.md` next to the script for anything non-trivial. It holds the execution
  mechanics only (which URL, which click, exact stop points, where stills go), so another agent or
  person can resume without chat history.
