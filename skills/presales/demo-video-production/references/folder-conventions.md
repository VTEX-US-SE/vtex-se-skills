# Folder and naming conventions

One folder per video, anywhere on your machine (not inside this skills repo):

```
<video-folder>/                 e.g. kai-logistics, pharmacy-scratch
  raw/                          source video from Drive + extracted audio
  transcript/                   RunPod JSON (source of truth) + any .srt/.txt exports
  audio/                        voice-swapped or TTS audio + tts_manifest.json
  slides/                       slide HTML + rendered PNGs (static method)
  hyperframes-project/          Hyperframes project + renders/ (animated method)
  demos/<segment-slug>/         live-demo stills, numbered in order
  final/                        per-segment clips + the final video
  production-script.md          from-scratch videos: research + narration (the TTS source)
  script.md                     existing videos: standardized English transcript script
  slides.json                   slide spec for build_slides.py
  plan.json                     assembly plan for assemble.py
  RECORDING_TASK.md             optional: execution mechanics for the capture
```

**Folder name:** `<presenter-first-name>-<topic-slug>` for re-edits of an SE's video
(`isa-fashion`), `<topic-slug>-scratch` for from-scratch videos (`pharmacy-scratch`). Kebab-case, no
date: the folder is the video.

**raw/:** `<descriptive-slug>.mp4`, `audio_original.wav` (44.1 kHz), and service-specific variants
with an explicit suffix (`audio_original_64kbps.mp3` for RunPod).

**transcript/:** `audio_original.json`.

**audio/:**
- Voice swap: `audio_s2s_<voice>.mp3` (+ `.wav`), and `audio_s2s_<voice>_preview30s.mp3` for a new
  voice.
- Per-segment TTS: `<segment-slug>.mp3` + `.wav` + `tts_manifest.json`.

**Segment slug** comes from the `## SEGMENT ...` header: `SEGMENT 0 — Hook` → `seg0_hook`,
`SEGMENT 0.5 — Quick capability map` → `seg0-5_quick-capability-map`, `SEGMENT — Closing / CTA` →
`seg_closing-cta`. Use the same slug for slide ids and demo folders.

**final/:** working clips named in display order (`seg1_intro.mp4`, `seg2_badge.mp4`...) and the
deliverable `<folder-slug>_FINAL_v<N>.mp4`. Bump N for every delivered revision, and delete draft
names before delivering.

**Language:** scripts, slides and deliverables in English unless the video is explicitly for
another market.

**Never** keep a reusable HTML slide only as a Claude artifact. Artifacts are not a backup (one
disappeared for good). Everything lives as local files in the video folder.
