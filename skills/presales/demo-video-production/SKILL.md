---
name: demo-video-production
description: Produce VTEX solution demo videos with the SE team's pipeline — either re-edit an existing recording (transcribe with RunPod, swap the voice with ElevenLabs Speech-to-Speech, replace intro/outro/watermarks with on-brand slides via lossless ffmpeg keyframe cuts) or build a new video from scratch (verified research, production script, per-segment ElevenLabs TTS narration, VTEX-branded slides via Hyperframes or static PNG, live-demo stills captured from Chrome, lossless assembly). Use when someone asks to make, redo, re-voice, rebrand, fix, or assemble a demo video for a vertical or capability.
version: 1.0.0
disable-model-invocation: true
---

# Demo Video Production

The SE team's pipeline for VTEX demo videos, proven on ~15 delivered videos. Two modes share one
toolbox:

- **Mode A — Re-edit an existing video:** download → transcribe → voice swap → swap
  intro/outro/watermarked stretches for on-brand slides → remux. The original audio timing is
  preserved, so the result has the same length as the source.
- **Mode B — Build a video from scratch:** research → production script → per-segment TTS →
  slides → live-demo stills → assembly. Audio comes first and every visual is sized to it.

`<skill>` below means the folder containing this file. Scripts are in `<skill>/scripts/`, deep
detail in `<skill>/references/`, starting files in `<skill>/templates/`.

## Step 0 — Every session

1. Run `bash <skill>/scripts/check_setup.sh`. If a key shows `MISS`, stop and point the user to
   the README's "Setup" section. Never ask them to paste a key into chat. If the VTEX Trust font is
   missing, tell them the slides won't be brand-compliant until they add it (README step 4).
2. Ask which mode, and which video folder to use (create it per
   `references/folder-conventions.md`, outside this repo).
3. Ask the requester's voice choice: Roger (male) or Sarah (female) are validated. Any other voice
   needs a ~30 s preview approved first (`speech_to_speech.py --preview 30`).

## Hard rules — never skip

1. **Paid calls are dry-run first.** `generate_tts.py` and `speech_to_speech.py` print text and
   cost without `--confirm`. Show the user the dry-run output and get an explicit go-ahead before
   adding `--confirm`. Transcription is cheap, but still say what you're sending.
2. **Never click Save / Publish / Confirm order / Complete purchase while recording.** Interact up
   to the decision point, then stop. Real customer production accounts: public storefront only.
3. **Match `time_base` before any `-c copy` concat.** A mismatch produces a file with the right
   duration that can't be seeked. Render with `-video_track_timescale 90000` (or the source's
   value in mode A) and let `assemble.py` verify.
4. **No bracketed stage directions in narration.** TTS reads them aloud.
5. **`Vitex` → `VTEX` only when the sentence still makes sense.** Otherwise flag it as garbled
   speech.
6. **Final script claims rest on official VTEX docs, product-team material, or a live test.** A
   colleague's demo is a lead, never the source.
7. **Concat audio as WAV, never MP3 pieces.** Encode to AAC only at the final mux.
8. **Capture only the Chrome window region, with Do Not Disturb on.** Never take a full-screen
   screenshot.
9. **Look at the output.** Extract frames at the start, middle, end and every boundary. Exit code
   0 does not prove the video is right.
10. **Brand:** only the kit in `vtex_brand.py`. Never commit the VTEX Trust font files (this repo is public). Titles Regular, no ALL CAPS, no letter-spacing,
    pink as an accent.

## Mode A — Re-edit an existing video

1. **Get the source.** The Drive MCP refuses files over 10 MB. Use `claude-in-chrome` to open the
   file's Drive page and click download, then move it from `~/Downloads/` into `raw/`.
2. **Inspect it.** Run `ffprobe` for resolution, fps, time_base and profile, and sample frames (a
   contact sheet) to confirm it's a real screen recording and not a narrated slide deck.
   → `references/video-editing.md`
3. **Transcribe.** Extract the audio (64 kbps mono MP3, ≤10 min per chunk), then
   `python3 <skill>/scripts/transcribe_runpod.py raw/audio_original_64kbps.mp3 --out transcript/audio_original.json`.
   Write `script.md` (English, timestamped). → `references/transcription.md`
4. **Decide the voice method** per `references/voice.md`: S2S for the same words, a hybrid when a
   few lines change, per-block TTS when most wording changes. Then run
   `speech_to_speech.py raw/audio_original.wav --voice <v> --out audio/audio_s2s_<v>.mp3` (dry run,
   approval, `--confirm`).
5. **Slides.** Write `slides.json` with the new opening/closing (plus a badge for watermarks), then
   build them. → `references/slides.md`
6. **Cut and remux.** Find keyframes, stream-copy the untouched body, render the slides at the
   exact gap durations with the source's time_base, concat the video, remux the new audio. The last
   slide absorbs S2S drift. → `references/video-editing.md`
7. **QA and deliver.** → `references/assembly.md`

## Mode B — Build from scratch

1. **Research** with the VTEX Developer MCP, Atlas, Drive, Slack and live fetches. Record every
   source. → `references/from-scratch-flow.md`
2. **Script.** Copy `templates/production-script-template.md` to
   `<video-folder>/production-script.md`. Use the skeleton opening → capability map → demo
   (Admin ↔ storefront) → closing with a CTA. Put a verification note on every claim. Get the
   requester's approval on the script before any paid call.
3. **Narration.** Run `python3 <skill>/scripts/generate_tts.py <video-folder> --voice <v>` (dry
   run), get approval, add `--confirm`. The durations in `audio/tts_manifest.json` now drive
   everything.
4. **Slides.** Copy `templates/slides.example.json` to `slides.json`, pointing each slide's
   `audio` at its WAV. Hyperframes is the default; static PNG is fine for simple slides.
   → `references/slides.md`
5. **Demo stills.** Navigate with `claude-in-chrome` and capture with
   `scripts/capture_chrome_window.sh`. Then crop, pad and hold each still for its share of the
   narration. macOS only; needs Screen Recording + Accessibility. → `references/recording.md`
6. **Assemble.** Write `plan.json` (`templates/assembly-plan.example.json`), then run
   `python3 <skill>/scripts/assemble.py plan.json --out final/<slug>_FINAL_v1.mp4`.
   → `references/assembly.md`
7. **QA and deliver.** → `references/assembly.md`

## Scripts

| Script | Does | Costs money |
|---|---|---|
| `check_setup.sh` | Preflight: tools, keys present, macOS capture | no |
| `transcribe_runpod.py` | Audio → word-timestamped JSON | RunPod (cents) |
| `speech_to_speech.py` | Voice swap, silence-aware chunking, `--preview` | ElevenLabs, dry run by default |
| `generate_tts.py` | Per-segment narration from `production-script.md` | ElevenLabs, dry run by default |
| `build_slides.py` | `slides.json` → branded HTML → PNG or Hyperframes compositions | no |
| `build_slide_clip.sh` | PNG → normalized silent clip of N seconds | no |
| `build_footage_clip.sh` | Footage excerpt padded with a frozen last frame to N seconds | no |
| `capture_chrome_window.sh` | Screenshot one Chrome tab's window region (macOS) | no |
| `assemble.py` | Verify, mux each segment with its WAV, lossless concat | no |

## Not in scope

The RFP response itself, full-length webinar editing, and publishing to YouTube or the website. For
brand questions outside video slides, use `vtex-brand-guidelines`.
