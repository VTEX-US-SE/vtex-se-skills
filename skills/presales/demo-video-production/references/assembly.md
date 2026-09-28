# Assembly

## Normalization target (decide before generating any asset)

Every video piece (slide, still clip, footage clip, Hyperframes render) must share:

| Parameter | Value |
|---|---|
| Resolution | 1920x1080 (pad, never stretch) |
| Frame rate | 30 fps |
| Codec / profile / level | H.264 High @ 4.0 |
| Pixel format | yuv420p |
| time_base | 1/90000 (`-video_track_timescale 90000`) |

`build_slide_clip.sh`, `build_footage_clip.sh` and the still recipe in recording.md already produce
this. Hyperframes renders need the remux that `build_slides.py` prints. `assemble.py` verifies all
of it before joining anything.

When re-editing an existing video (mode A), the target is **the source video's own parameters**
instead. Read them with `ffprobe` and match them.

## From-scratch assembly (mode B)

1. Narration first: `generate_tts.py` → `audio/<slug>.wav` + `audio/tts_manifest.json` with real
   durations.
2. Visual per segment, sized to that segment's real narration:
   - slide: Hyperframes render (normalized) or `build_slide_clip.sh <png> <seconds>`
   - live demo: still clips (recording.md) concatenated per segment
   - reused footage shorter than the narration: `build_footage_clip.sh SRC START AVAIL TARGET OUT`
     (pads with a frozen last frame)
3. Write `plan.json` (see `templates/assembly-plan.example.json`) and run:
   ```bash
   python3 scripts/assemble.py plan.json --out final/<folder-slug>_FINAL_v1.mp4
   ```
   It muxes each segment's video with its WAV (AAC 192k), refuses mismatched pieces, flags any
   segment whose video is shorter than its narration, and concatenates losslessly.

Harmless: occasional "Non-monotonic DTS" warnings at audio join points (ffmpeg self-corrects).

## QA before calling it done

- **Watch it.** Extract frames at the start, middle, end and every segment boundary. A black
  or wrong-tab frame still exits 0.
- Seek into each segment in a player. A `time_base` mismatch only shows up on seek.
- Grep the script for leftover persona names and bracketed stage directions. A "Bob" from an
  early draft once survived into the final narration.
- Every segment transition has a bridging line ("Now let's see how X behaves once Y is running").
  A hard topic cut without one feels abrupt.
- When a premise changes (e.g. "feature X lives in the storefront, not the Admin"), strike the old
  note in the script. Don't just add a new one beside it.
- Self-review up to 3 rounds, then escalate to the human reviewer.

## Delivery

- Final name: `<folder-slug>_FINAL_v<N>.mp4`. Delete draft names (`_TEST`, `video_only`...) before
  delivering.
- Copy it somewhere watchable (e.g. `~/Downloads/`) and upload to the team's shared Drive folder for
  videos by vertical.
- Anonymize third-party brands you don't have approval to show. Replacing a wordmark with a
  generic `demostore_` label looks better than a blur. Keep the un-anonymized version internal.
