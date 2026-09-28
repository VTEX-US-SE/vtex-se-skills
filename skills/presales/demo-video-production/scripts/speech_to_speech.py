#!/usr/bin/env python3
"""
Swap the voice of an existing narration with ElevenLabs Speech-to-Speech (Voice Changer), keeping
the original rhythm and pauses so the audio stays in sync with the existing screen recording.

New in this skill (2026-09-28). The pilots did this step by hand; this script wraps the same API
call with the pipeline's safety rules. Test it with --preview on your first run.

Usage:
    python3 speech_to_speech.py <audio.wav> --voice roger|sarah --out audio/audio_s2s_roger.mp3
    python3 speech_to_speech.py <audio.wav> --voice roger --preview 30 --out audio/preview30s.mp3 --confirm
    python3 speech_to_speech.py <audio.wav> --voice roger --out audio/audio_s2s_roger.mp3 --confirm

Default is a DRY RUN: prints the source duration, the chunk plan and the estimated credit cost
(~1000 credits per minute of audio), and makes no API call. Pass --confirm to spend credits.

Long audio is split into chunks of at most --max-chunk seconds (default 240), cut at detected
silences so no word is split, converted chunk by chunk, then joined as WAV/PCM (sample-accurate,
no MP3 padding drift). The final file is written as MP3 (or WAV if --out ends in .wav), plus a
.wav sibling for assembly.

Model: eleven_multilingual_sts_v2. Key: ELEVENLABS_API_KEY, loaded by _env.py. Never printed.
Expect ~0.02% duration drift versus the original (e.g. ~0.1s over 8 minutes); absorb it in the
last clip of the edit (see references/video-editing.md).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import load_env_var  # noqa: E402

VOICES = {
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
}
MODEL_ID = "eleven_multilingual_sts_v2"
CREDITS_PER_MINUTE = 1000


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def silence_midpoints(path: Path) -> list[float]:
    """Midpoints of silences >= 0.3s at -35dB — safe places to split without cutting a word."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.3",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", proc.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", proc.stderr)]
    return [(s + e) / 2 for s, e in zip(starts, ends)]


def plan_chunks(total: float, max_chunk: float, cuts: list[float]) -> list[tuple[float, float]]:
    chunks, start = [], 0.0
    while total - start > max_chunk:
        candidates = [c for c in cuts if start + 30 < c <= start + max_chunk]
        end = candidates[-1] if candidates else start + max_chunk  # no silence: hard cut
        chunks.append((start, end))
        start = end
    chunks.append((start, total))
    return chunks


def _is_credits_error(status: int, body: str) -> bool:
    lowered = body.lower()
    return status in (401, 429) and any(
        s in lowered for s in ("quota_exceeded", "insufficient", "credit", "out of credits")
    )


def sts_call(audio_path: Path, voice_id: str, api_key: str) -> bytes:
    boundary = uuid.uuid4().hex
    parts = [
        (f'--{boundary}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\n{MODEL_ID}\r\n').encode(),
        (f'--{boundary}\r\nContent-Disposition: form-data; name="audio"; filename="{audio_path.name}"\r\n'
         "Content-Type: audio/wav\r\n\r\n").encode() + audio_path.read_bytes() + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    req = request.Request(
        f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=b"".join(parts),
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with request.urlopen(req, timeout=600) as resp:
            return resp.read()
    except error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if _is_credits_error(e.code, body):
            sys.exit("=" * 70 + f"\n[CREDITS EXHAUSTED] ElevenLabs (HTTP {e.code}): {body[:300]}\n"
                     "Check BOTH limits: the plan total AND the API key's own credit cap.\n" + "=" * 70)
        sys.exit(f"ElevenLabs Speech-to-Speech failed (HTTP {e.code}): {body[:500]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="source narration (e.g. raw/audio_original.wav)")
    voice = ap.add_mutually_exclusive_group(required=True)
    voice.add_argument("--voice", choices=sorted(VOICES), help="a validated stock voice")
    voice.add_argument("--voice-id", help="any other ElevenLabs voice id (preview it first)")
    ap.add_argument("--out", required=True, help="output path (.mp3 or .wav)")
    ap.add_argument("--preview", type=float, metavar="SECONDS",
                    help="convert only the first N seconds (use ~30 to audition a new voice)")
    ap.add_argument("--max-chunk", type=float, default=240.0, help="max seconds per API call (default 240)")
    ap.add_argument("--confirm", action="store_true", help="actually call the API (default: dry run)")
    args = ap.parse_args()

    src = Path(args.audio).expanduser().resolve()
    if not src.exists():
        sys.exit(f"Audio file not found: {src}")
    out = Path(args.out).expanduser().resolve()
    voice_id = VOICES[args.voice] if args.voice else args.voice_id
    voice_label = args.voice or args.voice_id

    total = ffprobe_duration(src)
    if args.preview:
        total = min(total, args.preview)
    chunks = plan_chunks(total, args.max_chunk, silence_midpoints(src) if not args.preview else [])

    print(f"Source: {src} ({total:.2f}s{' preview' if args.preview else ''}), voice={voice_label}")
    for i, (a, b) in enumerate(chunks):
        print(f"  chunk {i}: {a:8.2f}s -> {b:8.2f}s ({b - a:.2f}s)")
    print(f"Estimated cost: ~{int(total / 60 * CREDITS_PER_MINUTE)} credits")

    if not args.confirm:
        print("[DRY RUN] No API calls made, no credits spent. Re-run with --confirm.")
        return

    api_key = load_env_var("ELEVENLABS_API_KEY")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        wavs = []
        for i, (a, b) in enumerate(chunks):
            piece = tmpdir / f"in_{i:03d}.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a}", "-to", f"{b}", "-i", str(src),
                            "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(piece)], check=True)
            print(f"Converting chunk {i} ({b - a:.1f}s)...", end=" ", flush=True)
            mp3 = tmpdir / f"out_{i:03d}.mp3"
            mp3.write_bytes(sts_call(piece, voice_id, api_key))
            wav = tmpdir / f"out_{i:03d}.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "44100", "-ac", "1",
                            "-c:a", "pcm_s16le", str(wav)], check=True)
            wavs.append(wav)
            print("ok")
        listing = tmpdir / "concat.txt"
        listing.write_text("".join(f"file '{w}'\n" for w in wavs))
        joined = out.with_suffix(".wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", str(joined)], check=True)
    if out.suffix.lower() != ".wav":
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-c:a", "libmp3lame",
                        "-b:a", "192k", str(out)], check=True)
    got = ffprobe_duration(joined)
    print(f"Wrote {out} (+ {joined.name}): {got:.3f}s vs source {total:.3f}s "
          f"(drift {got - total:+.3f}s)")
    (out.parent / f"{out.stem}.json").write_text(json.dumps(
        {"source": str(src), "voice": voice_label, "model": MODEL_ID, "chunks": chunks,
         "source_seconds": round(total, 3), "output_seconds": round(got, 3)}, indent=2))


if __name__ == "__main__":
    main()
