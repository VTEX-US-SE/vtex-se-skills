#!/usr/bin/env bash
# build_slide_clip.sh PNG DURATION OUT  -> silent video-only clip, PNG held for DURATION seconds,
# normalized to the pipeline target (1920x1080, 30fps, yuv420p, High@4.0, time_base 1/90000).
set -e
PNG="$1"; DURATION="$2"; OUT="$3"
ffmpeg -y -v error -loop 1 -i "$PNG" -t "$DURATION" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xF8F7FC,setsar=1,fps=30" \
  -an -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -video_track_timescale 90000 "$OUT"
