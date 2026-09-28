#!/usr/bin/env bash
# build_footage_clip.sh SRC START AVAIL TARGET OUT
# Extracts SRC[START, START+min(AVAIL,TARGET)] (video only, silent), then pads with a frozen
# clone of the last frame if AVAIL < TARGET, so the output is exactly TARGET seconds of video,
# no audio. Established technique for footage-first pilots where reused screen recording runs
# shorter than the new TTS narration (see references/assembly.md).
set -e
SRC="$1"; START="$2"; AVAIL="$3"; TARGET="$4"; OUT="$5"
TAKE=$(python3 -c "print(min(float('$AVAIL'), float('$TARGET')))")
PAD=$(python3 -c "print(max(0.0, float('$TARGET') - float('$AVAIL')))")
if python3 -c "exit(0 if $PAD > 0.05 else 1)"; then
  ffmpeg -y -v error -ss "$START" -i "$SRC" -t "$TAKE" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=$PAD" \
    -an -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -video_track_timescale 90000 -t "$TARGET" "$OUT"
else
  ffmpeg -y -v error -ss "$START" -i "$SRC" -t "$TARGET" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30" \
    -an -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -video_track_timescale 90000 "$OUT"
fi
