## What it does

`demo-video-production` packages the pipeline the SE team built to produce VTEX demo videos. It has
two modes.

**Re-edit an existing recording:**
- transcribes it on a RunPod GPU endpoint;
- swaps the narrator's voice with ElevenLabs Speech-to-Speech, keeping the original timing;
- replaces the intro, the outro and any watermarked stretches with on-brand slides, using lossless
  ffmpeg keyframe cuts.

**Build a video from scratch:**
- researches VTEX docs and Atlas, and writes a production script where every claim carries a
  verification note;
- generates narration per segment with ElevenLabs TTS;
- builds animated slides (Hyperframes) on the official VTEX Design System;
- captures stills from a live demo store or Admin;
- assembles the segments losslessly, after checking that codec parameters match.

Every paid call is a dry run until the user approves it.

The step-by-step guide for a new user (setup, keys, costs, troubleshooting) lives next to the
skill, in [`skills/presales/demo-video-production/README.md`](../../skills/presales/demo-video-production/README.md).

## When to reach for it

Use it when someone needs a demo video for a vertical or a capability: redoing a colleague's
recording with a better voice and proper bookends, removing a burned-in watermark, rebranding
slides, or producing a new 2-10 minute video. It is **user-invoked only**
(`disable-model-invocation: true`) because it spends ElevenLabs and RunPod credits. Run it with
`/demo-video-production`.

| Your situation | Where to go |
|---|---|
| Need a demo **video** | this skill |
| Need a branded deck, document or diagram | `vtex-brand-guidelines` |
| Need animation/motion work beyond the standard slide layouts | the external `hyperframes` skill |

## Prerequisites

- **Local tools:** ffmpeg/ffprobe, Python 3.10+, Google Chrome. Node 22+ only for Hyperframes.
- **API keys:** `ELEVENLABS_API_KEY`, `RUNPOD_FASTER_WHISPER_API_KEY` and
  `RUNPOD_FASTER_WHISPER_ENDPOINT_ID`. They are not in this repo. The maintainers share them
  privately, and each user stores them in `~/.config/vtex-se-skills/.env`. The keys are scoped:
  - ElevenLabs: TTS / Speech-to-Speech / audio features only, with a credit cap.
  - RunPod: restricted to the single transcription endpoint.
- **VTEX Trust font:** proprietary, so it is **not** in this public repo. Each user keeps the
  official `.otf` files in `~/.config/vtex-se-skills/fonts/`. Without them, slides render in
  Helvetica and print a warning.
- **Hyperframes:** an external npm package (`npx hyperframes`, Apache 2.0) with telemetry disabled.
  Not bundled.
- **Claude in Chrome:** used for navigation during demo capture and for large Drive downloads.
- **macOS:** needed only for demo-still capture (`screencapture` + AppleScript, with Screen
  Recording and Accessibility permissions). Transcription, voice, slides and assembly work on any
  OS and any runtime, so the capture step is Claude Code on a Mac only.
- **Research connectors (mode B):** VTEX Developer MCP, Atlas MCP (`atlas-agent`), Google Drive,
  Slack.

## Reference files

| File | Purpose |
|---|---|
| `references/transcription.md` | RunPod Faster Whisper endpoint, chunking, output shape, ASR pitfalls |
| `references/voice.md` | Choosing S2S vs. hybrid vs. TTS, validated voices, credits, audio concat rules |
| `references/video-editing.md` | Keyframe cut + lossless concat recipes, `time_base` bug, watermark badge |
| `references/slides.md` | VTEX brand rules, `slides.json` types, static PNG vs. Hyperframes |
| `references/recording.md` | Never-confirm rule, stills capture, macOS permissions, click fallbacks |
| `references/assembly.md` | Normalization target, `assemble.py`, QA checklist, delivery |
| `references/from-scratch-flow.md` | Research sources and hierarchy, script rules, structure from 8 real videos |
| `references/folder-conventions.md` | Per-video folder layout and file naming |

## Author

Djan Magno and Noé Eustaquio, VTEX Solution Engineering. Migrated from their working pipeline in
the SE Co-pilot project (`demo-videos/`, documented in `PIPELINE.en.md`), which produced the team's
demo videos from August to September 2026.

Changes made while packaging it:
- API keys are now loaded from the user's environment instead of a vault `.env`.
- Video-specific slide content was removed from the generators.
- New scripts: `speech_to_speech.py` (the step was previously done by hand), `build_slides.py`,
  `assemble.py`, `capture_chrome_window.sh` and `check_setup.sh`.
- The pre-Design-System HTML templates were dropped in favor of the brand-kit generators.
- The VTEX Trust font was removed from the bundle because the repo is public.

## Common questions

**What has been verified end to end in this packaged form, and what hasn't?**

Tested on 2026-09-28, spending no credits:
- PNG and Hyperframes slide builds;
- clip normalization;
- `assemble.py`, including its `time_base` guard, which rejected a real `1/15360` clip;
- the dry runs of both paid scripts;
- key loading from `~/.config`.

Not yet run for real: a paid `speech_to_speech.py` call (new script; the request shape follows
ElevenLabs' API reference) and `capture_chrome_window.sh` (it needs the macOS permissions). Treat
the first run of each as a test: use `--preview 30`, and capture a harmless tab.
