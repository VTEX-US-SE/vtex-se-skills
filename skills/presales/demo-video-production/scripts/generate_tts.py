#!/usr/bin/env python3
"""
Generate per-segment TTS narration with ElevenLabs from a video's production-script.md
(templates/production-script-template.md).

Usage:
    python3 generate_tts.py <video-folder> --voice roger|sarah [--segments slug1,slug2] [--confirm]
    python3 generate_tts.py <video-folder> --voice-id <elevenlabs-voice-id> [--confirm]
    python3 generate_tts.py --check-credits

<video-folder> is a path (absolute or relative to where you run it) containing
production-script.md. Narration is read MECHANICALLY: the ">" blockquote right after each
"**Narration:**" line under each "## SEGMENT ..." header. Never retype narration by hand.

Default is a DRY RUN: prints every segment's text and character count, makes no API call, spends
no credits. Pass --confirm to generate audio.

Output, inside <video-folder>/audio/:
    <segment-slug>.mp3   raw ElevenLabs output
    <segment-slug>.wav   pcm_s16le mono 44.1kHz — use these for assembly; never concat MP3s with
                         -c copy (encoder padding accumulates)
    tts_manifest.json    voice, model and ffprobe-measured duration per segment (merged across runs)

Segment slug = the "## SEGMENT ..." header, number + label, lowercased/hyphenated:
    "SEGMENT 0 — Hook (0:00-0:20)"                  -> seg0_hook
    "SEGMENT 0.5 — Quick capability map"             -> seg0-5_quick-capability-map
    "SEGMENT — Closing / CTA"                        -> seg_closing-cta

Voices already validated (ElevenLabs stock voices, available on every account):
    roger -> CwhRBWXzGAHq8TQ4Fs17  (male, american, conversational)
    sarah -> EXAVITQu4vr4xnSDxMaL  (female, american, confident)
A voice that isn't one of these needs a short preview approved before a full run.

Model: eleven_turbo_v2_5. Key: ELEVENLABS_API_KEY, loaded by _env.py. Never printed.

If ElevenLabs reports out-of-credits mid-batch, the batch stops loudly; finished segments stay in
the manifest and re-running the same command picks up the rest. --check-credits needs the
`user_read` permission, which a TTS-only scoped key doesn't have — a 401 there is expected and
harmless.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import load_env_var  # noqa: E402

VOICES = {
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
}
MODEL_ID = "eleven_turbo_v2_5"


def load_api_key() -> str:
    return load_env_var("ELEVENLABS_API_KEY")


def slugify_header(header: str) -> str:
    header = re.sub(r"\(.*?\)\s*$", "", header).strip()  # drop trailing "(0:00-0:20)"
    header = header.replace("—", "-").replace("–", "-")
    m = re.match(r"SEGMENT\s*([\d.]*)\s*-?\s*(.*)", header)
    if not m:
        return re.sub(r"[^a-z0-9]+", "-", header.lower()).strip("-")
    num, label = m.group(1).strip(), m.group(2).strip()
    label_slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if num:
        return f"seg{num.replace('.', '-')}_{label_slug}"
    return f"seg_{label_slug}"


def extract_segments(script_path: Path) -> list[dict]:
    text = script_path.read_text(encoding="utf-8")
    header_re = re.compile(r"^## (SEGMENT[^\n]*)\n", re.MULTILINE)
    headers = [(m.group(1), m.end()) for m in header_re.finditer(text)]
    starts = [pos for _, pos in headers] + [len(text)]
    segments = []
    for i, (header, _) in enumerate(headers):
        block = text[starts[i] : starts[i + 1]]
        nmatch = re.search(r"\*\*Narration:\*\*\n((?:>.*\n?)+)", block)
        if not nmatch:
            continue
        lines = nmatch.group(1).splitlines()
        clean = " ".join(l.lstrip("> ").strip() for l in lines if l.strip() and l.strip() != ">")
        if "{{" in clean:  # unfilled template placeholder — skip
            continue
        segments.append({"header": header.strip(), "slug": slugify_header(header), "text": clean})
    return segments


class CreditsExhaustedError(RuntimeError):
    """Raised when ElevenLabs reports the account/key is out of credits — distinct from a
    generic API error so callers can stop the batch instead of burning more failed requests."""


def _is_credits_error(status: int, body: str) -> bool:
    lowered = body.lower()
    if status in (401, 429) and any(
        s in lowered for s in ("quota_exceeded", "insufficient", "credit", "out of credits")
    ):
        return True
    return False


def check_remaining_credits(api_key: str) -> dict | None:
    """Advisory GET of the subscription's remaining credits. Never raises; prints a warning and
    returns None if the check fails (a TTS-only scoped key returns 401 missing_permissions here)."""
    req = request.Request(
        "https://api.elevenlabs.io/v1/user/subscription",
        headers={"xi-api-key": api_key},
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except error.HTTPError as e:
        if e.code == 401:
            print("[info] Credit balance not readable with this key (it has no user_read permission, "
                  "by design). Skipping the pre-check; real calls still stop loudly if credits run out.")
        else:
            print(f"[WARN] Could not check ElevenLabs remaining credits: {e}")
        return None
    except Exception as e:  # noqa: BLE001 - advisory check, never fatal
        print(f"[WARN] Could not check ElevenLabs remaining credits: {e}")
        return None
    used = data.get("character_count", 0)
    limit = data.get("character_limit", 0)
    remaining = limit - used
    print(f"ElevenLabs credits: {remaining}/{limit} remaining ({used} used this period).")
    if limit and remaining / limit < 0.1:
        print(f"[WARN] Under 10% of ElevenLabs credits remaining ({remaining}/{limit}).")
    return data


def tts_call(text: str, voice_id: str, api_key: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with request.urlopen(req, timeout=90) as resp:
            return resp.read()
    except error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if _is_credits_error(e.code, body):
            raise CreditsExhaustedError(
                f"ElevenLabs reports out of credits (HTTP {e.code}): {body[:300]}"
            ) from e
        raise


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("video_folder", nargs="?", help="path to the video folder holding production-script.md")
    voice = ap.add_mutually_exclusive_group()
    voice.add_argument("--voice", choices=sorted(VOICES), help="a validated stock voice")
    voice.add_argument("--voice-id", help="any other ElevenLabs voice id (preview it first)")
    ap.add_argument("--segments", help="comma-separated slugs to limit to (default: all)")
    ap.add_argument(
        "--confirm", action="store_true",
        help="actually call the API (default: dry run, prints only, no cost)",
    )
    ap.add_argument(
        "--check-credits", action="store_true",
        help="print remaining ElevenLabs credits and exit (no TTS calls, no narration parsing needed)",
    )
    args = ap.parse_args()

    if args.check_credits:
        check_remaining_credits(load_api_key())
        return

    if not args.video_folder:
        sys.exit("video folder required (or pass --check-credits on its own)")
    if not (args.voice or args.voice_id):
        sys.exit("pass --voice roger|sarah or --voice-id <id>")
    base = Path(args.video_folder).expanduser().resolve()
    script_path = base / "production-script.md"
    if not script_path.exists():
        sys.exit(f"No production-script.md at {script_path}")

    segments = extract_segments(script_path)
    if args.segments:
        wanted = set(args.segments.split(","))
        segments = [s for s in segments if s["slug"] in wanted]
    if not segments:
        sys.exit("No segments matched (check --segments slugs, or that the script has filled-in narration).")

    print(f"Parsed {len(segments)} segment(s) from {script_path}:\n")
    for s in segments:
        print(f"--- {s['slug']} ({s['header']}) — {len(s['text'])} chars ---")
        print(s["text"])
        print()

    if not args.confirm:
        print("[DRY RUN] No API calls made, no credits spent. Re-run with --confirm to generate audio.")
        return

    api_key = load_api_key()
    voice_id = VOICES[args.voice] if args.voice else args.voice_id
    voice_label = args.voice or args.voice_id
    audio_dir = base / "audio"
    audio_dir.mkdir(exist_ok=True)

    check_remaining_credits(api_key)  # advisory, never blocks the run

    results = []
    for s in segments:
        mp3_path = audio_dir / f"{s['slug']}.mp3"
        wav_path = audio_dir / f"{s['slug']}.wav"
        print(f"Generating {s['slug']} (voice={voice_label})...", end=" ", flush=True)
        try:
            audio_bytes = tts_call(s["text"], voice_id, api_key)
        except CreditsExhaustedError as e:
            print("FAILED — OUT OF CREDITS")
            print("=" * 70)
            print(f"[CREDITS EXHAUSTED] {e}")
            print(
                f"Stopping batch — {len(results)}/{len(segments)} segment(s) completed before this "
                "point. Re-run the same command later (once credits refresh) to pick up the rest; "
                "already-generated segments are safe in the manifest below and won't be re-billed "
                "unless you re-run them by slug."
            )
            print("=" * 70)
            break
        except error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            print(f"FAILED ({e.code}): {body}")
            continue
        mp3_path.write_bytes(audio_bytes)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(mp3_path),
                "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path),
            ],
            capture_output=True, check=True,
        )
        dur = ffprobe_duration(wav_path)
        print(f"ok ({dur:.2f}s)")
        results.append({"slug": s["slug"], "header": s["header"], "seconds": round(dur, 2), "chars": len(s["text"])})

    manifest_path = audio_dir / "tts_manifest.json"
    existing_segments = []
    if manifest_path.exists():
        try:
            existing_segments = json.loads(manifest_path.read_text()).get("segments", [])
        except (json.JSONDecodeError, OSError):
            existing_segments = []
    merged = {s["slug"]: s for s in existing_segments}
    merged.update({s["slug"]: s for s in results})  # this run's results win on overlap
    manifest_path.write_text(
        json.dumps({"voice": voice_label, "model": MODEL_ID, "segments": list(merged.values())}, indent=2)
    )
    print(f"\nWrote {manifest_path}")
    total = sum(r["seconds"] for r in results)
    print(f"Total narration duration (this run): {total:.1f}s ({total/60:.2f} min)")


if __name__ == "__main__":
    main()
