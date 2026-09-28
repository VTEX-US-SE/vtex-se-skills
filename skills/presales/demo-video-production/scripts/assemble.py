#!/usr/bin/env python3
"""
Assemble a from-scratch (audio-first) demo video: mux each segment's video with its narration,
verify every piece shares the same codec parameters and time_base, then concatenate losslessly.

Usage:
    python3 assemble.py <plan.json> --out final/<folder-slug>_FINAL_v1.mp4

plan.json (paths relative to the plan file):
    {"segments": [
        {"video": "hyperframes-project/renders/seg0_hook_norm.mp4", "audio": "audio/seg0_hook.wav"},
        {"video": "final/seg1_stills.mp4",                          "audio": "audio/seg1_demo.wav"},
        {"video": "final/seg_closing_norm.mp4",                     "audio": "audio/seg_closing-cta.wav"}
    ]}

Every video must already be normalized (1920x1080, 30fps, yuv420p, H.264 High, time_base 1/90000):
build_slide_clip.sh / build_footage_clip.sh do this, and Hyperframes renders need the
`-video_track_timescale 90000` remux that build_slides.py prints. This script refuses to
concatenate mismatched pieces instead of producing a file that plays but can't be seeked.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KEYS = ("codec_name", "profile", "width", "height", "pix_fmt", "r_frame_rate", "time_base")


def probe_video(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=" + ",".join(KEYS), "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    streams = json.loads(out.stdout).get("streams", [])
    if not streams:
        sys.exit(f"no video stream in {path}")
    return {k: streams[0].get(k) for k in KEYS}


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    plan_path = Path(args.plan).expanduser().resolve()
    base = plan_path.parent
    segments = json.loads(plan_path.read_text())["segments"]
    out = Path(args.out).expanduser().resolve()

    reference, problems = None, []
    for seg in segments:
        v = base / seg["video"]
        info = probe_video(v)
        reference = reference or info
        diff = {k: (reference[k], info[k]) for k in KEYS if info[k] != reference[k]}
        if diff:
            problems.append(f"  {seg['video']}: {diff}")
    if problems:
        sys.exit("Video parameters differ from the first segment — normalize before assembling:\n"
                 + "\n".join(problems))
    print(f"All {len(segments)} video pieces match: {reference}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        muxed = []
        for i, seg in enumerate(segments):
            v, a = base / seg["video"], base / seg["audio"]
            m = Path(tmp) / f"seg_{i:03d}.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(v), "-i", str(a),
                            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                            "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest", str(m)],
                           check=True)
            vd, ad = duration(v), duration(a)
            flag = "  <-- video shorter than narration, audio was cut" if vd + 0.05 < ad else ""
            print(f"  seg {i}: video {vd:.2f}s, narration {ad:.2f}s{flag}")
            muxed.append(m)
        listing = Path(tmp) / "concat.txt"
        listing.write_text("".join(f"file '{m}'\n" for m in muxed))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    print(f"Wrote {out} ({duration(out):.2f}s). Now watch it: sample frames at the start, the middle, "
          "the end and every segment boundary before calling it done.")


if __name__ == "__main__":
    main()
