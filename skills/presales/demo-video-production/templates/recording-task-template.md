<!-- Recording task: the execution spec for capturing a video's live-demo segments. Copy it to
     `<video-folder>/RECORDING_TASK.md`. Any agent (a Claude session, a GPT computer-use agent) or a
     person should be able to follow it mechanically without chat history. Content and narration
     stay in `production-script.md`: this file says HOW to execute it, never WHAT to say. If the two
     disagree on content, production-script.md wins. -->

# Recording Task — {{VIDEO_TITLE}}

**Read `production-script.md` first.** It has the narration, the verification notes and the
real narration durations (`audio/tts_manifest.json`).

**Status:** {{PLANNED | EXPLORED | CAPTURED | ASSEMBLED}}, updated {{YYYY-MM-DD}}.

## Hard rules (every segment, no exceptions)

1. Interact freely; **never click Save / Confirm / Approve / Publish / Place order / Execute.** Stop
   at the decision point and capture that state.
2. {{Which accounts are sandboxes and which are real customer production sites. Real customer
   sites: public storefront only, never their Admin, never an order.}}
3. Re-verify each live site loads and is still on VTEX on the recording day.
4. Capture only the Chrome window region (`scripts/capture_chrome_window.sh`), with Do Not
   Disturb on.
5. Save every still under `demos/<segment-slug>/`, numbered in display order.
6. Credentials are never written here. Ask the account owner.

## Accounts and start state

| Segment | Account / domain | Type (sandbox / real) | Login needed | Start state |
|---|---|---|---|---|
| {{seg1_slug}} | {{primegoods.b2cdemostore.com}} | {{sandbox}} | {{yes: buyer X}} | {{storefront home, empty cart}} |

## Segment {{N}} — {{name}} (real narration: {{s}} s)

**Tool:** {{claude-in-chrome | GPT computer-use for steps X-Y}}

| # | Action (exact label / URL) | Expected screen after | Still |
|---|---|---|---|
| 0 | Open `{{start URL}}` in a new tab | {{what's visible}} | — |
| 1 | {{Type "Quantum Nexus Group" in the Search field}} | {{table shows 1 of 1}} | — |
| 2 | {{Click the row "…"}} | {{contract detail, Active}} | `01_{{state}}.png` |
| 3 | {{Click expand chevron on "…" (computer-use: DOM click ignored here)}} | {{children visible}} | `02_{{state}}.png` |
| — | **STOP** before {{the button that would persist}} | | |

**Duration split** (sums to the real narration): `01` → {{x}} s, `02` → {{y}} s.

**Demo data used / already used** (so re-takes don't collide): {{e.g. assortment "Papers" →
contract "Analyst Demo Buyer"; already linked: …}}

**Findings from the exploration pass:** {{labels that differed from the script, extra clicks
needed, flaky screens and how they recovered}}

*(repeat per live-demo segment)*

## Crop and assembly notes

- Raw capture size: {{e.g. 2560x1540 retina}}. Crop: {{e.g. `crop=2560:1210:0:300`}}, verified per
  still (the debug banner isn't always there).
- Pad color: {{white / page background}}.
- Output clips: `final/{{seg}}_stills.mp4` → listed in `plan.json` for `assemble.py`.
