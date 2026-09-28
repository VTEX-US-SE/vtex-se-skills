# Video editing — keyframe cuts and lossless concat

Everything here is plain `ffmpeg`/`ffprobe`. The core idea: **re-encode only the stretch whose
pixels change; stream-copy everything else.** A whole-video overlay filter took 35+ minutes of CPU
on an 8-minute 3600x2110 video and never finished. The cut-and-concat method below takes under a
second.

## First: what is the source, really?

Sample real frames across the runtime before choosing a technique:

```bash
for t in 5 60 120 240 400; do ffmpeg -v error -ss $t -i raw/source.mp4 -frames:v 1 -y /tmp/f_$t.png; done
# or a contact sheet in one call:
ffmpeg -v error -i raw/source.mp4 -vf "fps=1/10,scale=240:135,tile=8x8" -frames:v 1 -y /tmp/sheet.png
```

A video whose narration says "let's look at this live on the website" can turn out to be a
narrated slide deck of static mockups. The risk profile differs: a slide held a moment longer is
invisible, while a frozen frame mid-click is not.

Also read the specs you'll need to match: `ffprobe -show_entries stream=width,height,r_frame_rate,time_base,profile,pix_fmt`.
Never assume resolution. Real sources ranged from 1280x720 to 3600x2110.

## The silent killer: `time_base`

`concat` with `-c copy` **accepts clips with different `time_base` without any error and reports
the correct total duration**, but seeking into the mismatched segment breaks (`No filtered frames
for output stream`, and players hang or skip). A fresh `libx264` clip usually gets `1/15360`,
Hyperframes renders get `1/15360`, and screen recordings are often `1/90000`, though one source was
`1/60000`.

**Always** check every piece with `ffprobe -show_entries stream=time_base` before concatenating,
and render new clips with `-video_track_timescale <the body's value>`. `assemble.py` refuses to
join mismatched pieces.

## Technique 1 — Swap the visual, keep the original audio (duration unchanged)

Use it to replace an intro/outro, or any stretch, with a slide while the original narration keeps
playing underneath.

1. Find real keyframes near the cut points (fast; without `-skip_frame nokey` this can hang):
   ```bash
   ffprobe -v error -skip_frame nokey -select_streams v:0 -show_entries frame=pts_time -of csv body.mp4
   ```
2. Extract the untouched middle by pure copy, between two keyframes:
   ```bash
   ffmpeg -ss <kf_start> -to <kf_end> -i body.mp4 -an -c:v copy middle.mp4
   ```
3. Render the replacement slides at the **exact** missing durations, matching the body's fps,
   pix_fmt, profile/level and time_base:
   ```bash
   ffmpeg -loop 1 -i slides/intro.png -t <kf_start> -c:v libx264 -profile:v high -pix_fmt yuv420p \
     -r 30 -video_track_timescale 90000 -an intro.mp4
   ```
4. Concat the video only, then remux the full original (or voice-swapped) audio:
   ```bash
   printf "file 'intro.mp4'\nfile 'middle.mp4'\nfile 'outro.mp4'\n" > concat.txt
   ffmpeg -f concat -safe 0 -i concat.txt -i audio/audio_s2s_roger.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4
   ```

**When a stretch can be covered:** read the transcript for those seconds. If the narration
references something specific on screen ("as you can see here..."), don't cover it; move the cut
to a later keyframe where the narration is generic. A cut landing mid-sentence is fine, because
the audio underneath is untouched.

**Finding an existing opening card's real end:** sample frames every 1-2 s from t=0 until the image
changes, binary-search to the second, then take the next keyframe.

**The same cut works mid-video.** Split into as many pieces as needed, for example:

```
[0 → kf_a]     intro slide                 (light re-encode, static)
[kf_a → kf_b]  original + corner badge     (re-encode only this stretch)
[kf_b → kf_c]  pure copy                   (zero re-encode)
[kf_c → end]   outro slide                 (light re-encode, static)
```

**Duration drift after S2S:** the voice-swapped audio runs ~0.02% off the original. Size the
**last** slide as `s2s_audio_duration - kf_c`, not `original_duration - kf_c`. Middle stretches stay
anchored to the video.

## Technique 2 — Insert new content (duration grows)

New scene with its own narration: cut the body at a keyframe and concat video **and** audio on both
sides:

```bash
printf "file 'intro.mp4'\nfile 'body.mp4'\nfile 'new_scene.mp4'\nfile 'outro.mp4'\n" > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy out.mp4
```

This only works if every file has identical codec parameters (h264 profile/level/pix_fmt/
resolution/time_base, and the same AAC sample rate and channels). Re-encode only the odd piece
to match, never the whole video.

**Appending a silent closing slide:** render the slide with a silent audio track, concat, then pad
the narration to the new total with `apad=whole_dur` (don't hand-compute the silence):

```bash
ffmpeg -loop 1 -i outro.png -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" -t 7 \
  -r 30 -pix_fmt yuv420p -c:v libx264 -profile:v high -level 4.0 -video_track_timescale 90000 \
  -c:a aac -b:a 128k -shortest outro_clip.mp4
printf "file 'body.mp4'\nfile 'outro_clip.mp4'\n" > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy video_track.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 video_track.mp4)
ffmpeg -i audio/audio_s2s_roger.mp3 -af "apad=whole_dur=${DUR}" -ar 44100 -ac 2 -c:a aac audio_full.m4a
ffmpeg -i video_track.mp4 -i audio_full.m4a -map 0:v -map 1:a -c copy -shortest out.mp4
```

## Burned-in third-party watermarks (e.g. Descript)

- `delogo` looks fine on flat backgrounds but smears over detailed content. Discarded.
- **What works:** replace static stretches (title cards) with a new slide, and for real-content
  stretches overlay an **opaque VTEX corner badge** exactly over the watermark, on only the
  affected stretch:
  ```bash
  ffmpeg -i body.mp4 -i badge.png -ss <kf_a> -to <kf_b> -filter_complex "overlay=X:Y" \
    -an -r 30 -pix_fmt yuv420p -c:v libx264 -profile:v high -crf 18 -video_track_timescale 90000 seg_badge.mp4
  ```
  Build the badge from the brand kit (`vtex_brand.py`: Serious Black field, pink accent, the real
  logo). 57 s of 720p re-encoded in 6.5 s.

## Other filters

- `fade`/`afade` work as expected.
- `zoompan` on video input and `crop` with time-varying `w`/`h` don't work on ffmpeg 7.1 (no
  effect, or "Failed to configure input pad"). For a zoom, extract frames (`-vsync 0`),
  crop/resize per frame in Python/PIL, and reassemble with `-framerate N -i frame_%05d.png`.
- Retina captures (e.g. 3024x1964) need pillarbox/letterbox to 16:9, never a stretch. Fill the
  border with the page's background color, not pure black.
- A final two-pass `loudnorm` (-14 LUFS / -1 dBTP / LRA 11) is worth adding as a mastering step.
