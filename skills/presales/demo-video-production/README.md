# demo-video-production

Make VTEX solution demo videos with the same pipeline the SE team has used on ~15 delivered videos,
across Fashion, B2B, Pharmacy, Banking, Fast Food and other verticals. You describe the video; the
agent runs the pipeline and checks with you before every step that costs money.

**What you get:** a finished `final/<name>_FINAL_v1.mp4` at 1920x1080. It has a professional
narrator voice, VTEX-branded animated slides that follow the official Design System, and real
screens from a live VTEX store or Admin.

## Two ways to use it

| You have... | Mode | What happens |
|---|---|---|
| An existing recording (yours or a colleague's) that needs a better voice, a proper intro/closing, or a watermark removed | **A — Re-edit** | Transcribe → swap the voice (same words, same timing) → replace the opening/closing/watermarked parts with branded slides → same-length video out |
| A topic, a vertical, a capability to show, and no video yet | **B — From scratch** | Research VTEX docs → write a verified script → generate narration → build slides → capture screens from a demo store → assemble |

## Setup (once, about 15 minutes)

### 1. Install the tools

macOS with [Homebrew](https://brew.sh):

```bash
brew install ffmpeg python node
```

You also need **Google Chrome** installed in `/Applications`. Versions required: Python 3.10+, and
Node 22+ (Node is only used for animated slides).

### 2. Install the skill

Clone this repo, then make the skill visible to your agent. For Claude Code:

```bash
git clone git@github.com:VTEX-US-SE/vtex-se-skills.git ~/dev/vtex-se-skills
mkdir -p ~/.claude/skills
ln -s ~/dev/vtex-se-skills/skills/presales/demo-video-production ~/.claude/skills/demo-video-production
```

Alternatively, install the whole repo as a plugin (see the repo's root `README.md` for Codex and
Cursor). Pull the repo from time to time to get fixes.

### 3. Add the API keys

The pipeline uses two paid services:

- **ElevenLabs:** voice swap and narration.
- **RunPod:** transcription on a GPU.

**Ask Djan Magno or Noé Eustaquio for the key values.** They're shared privately, never in Slack
channels, never in a repo.

Put them in a file only you can read:

```bash
mkdir -p ~/.config/vtex-se-skills
cp ~/dev/vtex-se-skills/skills/presales/demo-video-production/.env.example ~/.config/vtex-se-skills/.env
chmod 600 ~/.config/vtex-se-skills/.env
open -e ~/.config/vtex-se-skills/.env    # paste the three values, save
```

Prefer your own accounts? That works too, and it makes spend traceable per person:
- **ElevenLabs:** a paid plan (Free has no commercial license). Create an API key with only
  Text-to-Speech, Speech-to-Speech, Audio Isolation and Voice Generation set to Access, and Voices
  set to Read. Turn on "auto-disable if leaked" and set a credit cap on the key itself.
- **RunPod:** add credit, deploy **Faster Whisper** (`runpod-workers/worker-faster_whisper`) from
  the RunPod Hub as a serverless endpoint, copy its endpoint ID, and create an API key restricted
  to that endpoint.

Scripts look for each key in this order:
1. an environment variable
2. `~/.config/vtex-se-skills/.env`
3. a `.env` in the folder you're working in, or any of its parents

Never paste a key into a chat with the agent, a script, or a file inside a git repo.

### 4. Add the VTEX Trust font

VTEX Trust is VTEX's proprietary brand font. This repo is public, so the font is **not** in it.
Get the official `VTEXTrust-Regular`, `VTEXTrust-Medium` and `VTEXTrust-Italic` files (`.otf`)
from the VTEX brand kit, or ask the maintainers, and put them here:

```bash
mkdir -p ~/.config/vtex-se-skills/fonts
cp VTEXTrust-{Regular,Medium,Italic}.otf ~/.config/vtex-se-skills/fonts/
```

Without them, slides still render, but in Helvetica, which is not brand-compliant. The scripts
print a warning when that happens.

### 5. Check everything

```bash
bash ~/.claude/skills/demo-video-production/scripts/check_setup.sh
```

Every line should say `ok`. A `warn` about node or macOS permissions is fine for now. This spends
nothing and never prints key values.

### 6. Only for animated slides: one-time Hyperframes setup

```bash
export HYPERFRAMES_NO_TELEMETRY=1
npx --yes hyperframes browser ensure     # ~93 MB download, first time only
```

Add `export HYPERFRAMES_NO_TELEMETRY=1` to your `~/.zshrc` so telemetry stays off.

### 7. Only for mode B (capturing screens): macOS permissions

Capturing screens needs two permissions, both in **System Settings → Privacy & Security**, both
granted to the app your agent runs in (the Claude desktop app, Terminal, or iTerm):

- **Screen Recording**
- **Accessibility**

After granting them, **quit that app completely and reopen it**. Permissions don't apply to an
already-running app.

Screen capture also needs the **Claude in Chrome** extension connected, which the agent uses to
navigate the demo store.

## Using it

Start your agent in any folder where you keep videos (not inside this repo) and invoke the skill:

```
/demo-video-production
```

Then describe what you want. Examples:

> Mode A: "Re-edit Isa's Fashion video in ~/videos/isa-fashion/raw/fashion.mp4. Swap the voice to
> Sarah, replace the Descript intro with our opening slide, and add a closing slide with the CTA."

> Mode B: "Build a 3-minute from-scratch demo video for the Pharmacy vertical showing prescription
> upload and subscriptions on the pharmacy demo store. Male voice."

The agent creates the video folder, works step by step, and stops for your approval at these
points:

1. **The script** (mode B), before any narration is generated.
2. **Every paid call.** You see a dry run first, with the exact text and an estimated cost; nothing
   is spent until you say go.
3. **A voice preview**, only if you pick a voice other than Roger or Sarah.
4. **Moments that need your hand**, such as a login, or a click the automation can't do.
5. **The final video.** Watch it before sharing.

Where things land: see [`references/folder-conventions.md`](references/folder-conventions.md).
Everything for one video lives in its own folder (`raw/`, `audio/`, `slides/`, `demos/`, `final/`).

## What it costs

| Step | Service | Typical cost |
|---|---|---|
| Transcription | RunPod | a few cents per video |
| Voice swap (mode A) | ElevenLabs Speech-to-Speech | ~1000 credits per minute (an 8 min video ≈ 8300 credits) |
| Narration (mode B) | ElevenLabs TTS | billed per character (a 3-minute script is a few thousand credits) |
| Slides, editing, assembly | local | free |

Credits come from the team's shared accounts, so don't run full-length jobs just to experiment:
use `--preview 30` or the dry run. If a job stops with `[CREDITS EXHAUSTED]`, tell the
maintainers. Don't retry in a loop.

## Rules the agent follows (and you should too)

- **Never saves or confirms anything in a store or Admin while recording.** It clicks through a
  flow up to the final button and stops.
- **On a real customer's live site, it only uses the public storefront.** It never opens that
  customer's Admin or places an order. Demo accounts (e.g. `*.b2cdemostore.com`) are the default.
- **Every claim in a script is backed by official VTEX docs, product material, or a live test.** A
  colleague's video is a lead, not a source.
- **Captures only the browser window, never the full screen.** Turn on **Do Not Disturb** before
  recording so Slack or email notifications don't end up in the video.
- **Slides follow the official VTEX brand:** VTEX Trust font, regular-weight titles, no ALL CAPS,
  pink as an accent.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ELEVENLABS_API_KEY is not set` | The key file is missing or in the wrong place. Re-do Setup step 3 and run `check_setup.sh`. |
| `--check-credits` / `--check-balance` return 401 | Expected: the team keys are deliberately scoped to do only the pipeline's calls. Real runs still work. |
| RunPod `exceeded max body size of 10MiB` | Audio too long for one request. Use 64 kbps mono MP3 and split into ≤10 min chunks. |
| The final video plays but freezes or skips when you seek | A clip with a different `time_base` was concatenated. `assemble.py` catches this; for manual edits, see `references/video-editing.md`. |
| Screen capture fails with the same error every time | The app wasn't restarted after granting Screen Recording/Accessibility. Quit it fully and reopen. |
| The capture shows the wrong tab or a black frame | The agent raises the matching tab first. Make sure the URL substring it uses is unique, and that the page finished loading. |
| A click in the VTEX Admin does nothing | Some Admin components ignore automated clicks. The agent will ask you to click that one element. |
| Chrome shows a "started debugging this browser" bar | Normal while the extension is attached. It's cropped out of the stills. |
| Drive download fails for a big video | The Drive connector refuses files over 10 MB. The agent downloads through Chrome instead. |

## What's inside

| Path | What |
|---|---|
| `SKILL.md` | Instructions the agent follows |
| `scripts/` | The pipeline tools (listed with costs in `SKILL.md`) |
| `references/` | Deep detail per stage: transcription, voice, video editing, slides, recording, assembly, from-scratch flow, folder conventions |
| `templates/production-script-template.md` | The script format for from-scratch videos |
| `templates/slides.example.json` | Slide spec example (opening, capability grid, split, closing) |
| `templates/assembly-plan.example.json` | Assembly plan example |
| `assets/vtex-brand/` | Official VTEX color tokens and logo. The font lives on your machine (Setup step 4) |
| `.env.example` | The key names. Copy it to `~/.config/vtex-se-skills/.env` |

## Maintainers

Djan Magno and Noé Eustaquio (VTEX Solution Engineering). Found a new gotcha? Add it to the
matching file in `references/` in a PR, so the next person doesn't hit it too.
