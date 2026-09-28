#!/usr/bin/env python3
"""
Transcribe an audio file with the RunPod Faster Whisper serverless endpoint
(`runpod-workers/worker-faster_whisper`, the official RunPod worker).

Credentials: `RUNPOD_FASTER_WHISPER_API_KEY` and `RUNPOD_FASTER_WHISPER_ENDPOINT_ID`, loaded by
`_env.py` (environment -> ~/.config/vtex-se-skills/.env -> ./.env). Never printed, never logged.

Usage:
    python3 transcribe_runpod.py <audio.wav|mp3> --out transcript/audio_original.json
    python3 transcribe_runpod.py --check-balance   # advisory balance check, no job submitted

Input: any ffmpeg-readable audio, sent as plain base64 (no data-URI prefix). RunPod caps the whole
request body at 10MiB, so export 64kbps mono MP3 and keep each chunk under ~10 minutes. For longer
sources, split the audio, transcribe each chunk, and add each chunk's start offset to its
timestamps when merging (see references/transcription.md).

Output: the worker's JSON — `segments` (id/start/end/text, no nested words), a flat top-level
`word_timestamps` list of {word, start, end}, `transcription` (plain text), `detected_language`.
No diarization and no per-word score (this is Faster Whisper, not WhisperX).

If RunPod reports insufficient balance, the script stops with a `[CREDITS EXHAUSTED]` message
instead of a generic HTTP dump. `--check-balance` returns 401/403 on an endpoint-scoped
("Restricted") key; that is expected and never blocks a real run.
"""
import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import load_env_var  # noqa: E402

POLL_INTERVAL_S = 3
POLL_TIMEOUT_S = 600  # 10min ceiling — real jobs finish in ~10-60s

DEFAULT_MODEL = "turbo"  # fast + good accuracy; other options range tiny..large-v3 per the Hub listing


class CreditsExhaustedError(RuntimeError):
    """Raised when RunPod reports the account is out of balance/credits — distinct from a generic
    API error so callers can stop cleanly instead of retrying into more failures."""


def _is_credits_error(status: int, body: str) -> bool:
    lowered = body.lower()
    if status in (401, 402, 403) and any(
        s in lowered
        for s in ("insufficient", "balance", "out of credit", "quota", "payment required")
    ):
        return True
    return False


def check_balance(api_key: str) -> dict | None:
    """Advisory check via RunPod's GraphQL API — prints current account balance. Never raises;
    prints a warning and returns None if the check itself fails (e.g. API shape changed, or this
    key is endpoint-scoped rather than account-scoped — confirmed 2026-09-01 that a "Restricted"
    key returns 401 here even though job submission/polling on its own endpoint works fine)."""
    payload = json.dumps({"query": "query { myself { clientBalance } }"}).encode("utf-8")
    req = request.Request(
        "https://api.runpod.io/graphql",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:  # noqa: BLE001 - advisory check, never fatal
        print(f"[WARN] Could not check RunPod balance: {e} (may just mean this key is "
              "endpoint-restricted, not account-scoped — not necessarily a problem)")
        return None
    balance = data.get("data", {}).get("myself", {}).get("clientBalance")
    if balance is None:
        print(f"[WARN] Unexpected RunPod balance response shape: {data}")
        return None
    print(f"RunPod account balance: ${balance:.2f}")
    if balance < 1.0:
        print(f"[WARN] RunPod balance under $1.00 (${balance:.2f}) — top up before a big job.")
    return data


def submit_job(audio_path: Path, endpoint_id: str, api_key: str, model: str, word_timestamps: bool) -> str:
    audio_bytes = audio_path.read_bytes()
    b64 = base64.b64encode(audio_bytes).decode()
    payload = json.dumps(
        {
            "input": {
                "audio_base64": b64,
                "model": model,
                "transcription": "plain_text",
                "word_timestamps": word_timestamps,
            }
        }
    ).encode("utf-8")
    req = request.Request(
        f"https://api.runpod.ai/v2/{endpoint_id}/run",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if _is_credits_error(e.code, body):
            raise CreditsExhaustedError(
                f"RunPod reports insufficient balance (HTTP {e.code}): {body[:300]}"
            ) from e
        sys.exit(
            f"RunPod job submission failed (HTTP {e.code}): {body[:500]}\n"
            f"Audio was {len(audio_bytes) / 1024 / 1024:.1f}MiB raw / "
            f"{len(b64) / 1024 / 1024:.1f}MiB base64 — if this looks size-related, "
            "compress/chunk and retry (see references/transcription.md)."
        )
    job_id = data.get("id")
    if not job_id:
        sys.exit(f"RunPod job submission returned no job id: {data}")
    return job_id


def poll_job(job_id: str, endpoint_id: str, api_key: str) -> dict:
    req_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    start = time.monotonic()
    while time.monotonic() - start < POLL_TIMEOUT_S:
        req = request.Request(req_url, headers={"Authorization": f"Bearer {api_key}"})
        try:
            with request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if _is_credits_error(e.code, body):
                raise CreditsExhaustedError(
                    f"RunPod reports insufficient balance while polling (HTTP {e.code}): {body[:300]}"
                ) from e
            raise
        status = data.get("status")
        if status == "COMPLETED":
            return data
        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            sys.exit(f"RunPod job {job_id} ended with status={status}: {data}")
        print(f"  job {job_id}: {status}...", flush=True)
        time.sleep(POLL_INTERVAL_S)
    sys.exit(f"RunPod job {job_id} did not complete within {POLL_TIMEOUT_S}s (polling timeout).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?", help="path to the audio file to transcribe")
    ap.add_argument("--out", help="output JSON path (default: alongside input, same stem + .json)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Whisper model, tiny..large-v3 (default: {DEFAULT_MODEL})")
    ap.add_argument(
        "--no-word-timestamps", action="store_true",
        help="disable per-word timestamps (on by default — needed to find precise cut points)",
    )
    ap.add_argument(
        "--check-balance", action="store_true",
        help="print RunPod account balance and exit (no job submitted)",
    )
    args = ap.parse_args()

    api_key = load_env_var("RUNPOD_FASTER_WHISPER_API_KEY")

    if args.check_balance:
        check_balance(api_key)
        return

    if not args.audio:
        sys.exit("audio file required (or pass --check-balance on its own)")

    endpoint_id = load_env_var("RUNPOD_FASTER_WHISPER_ENDPOINT_ID")
    audio_path = Path(args.audio)
    if not audio_path.exists():
        sys.exit(f"Audio file not found: {audio_path}")
    out_path = Path(args.out) if args.out else audio_path.with_suffix(".json")

    check_balance(api_key)  # advisory, never blocks the run

    print(f"Submitting {audio_path} to RunPod endpoint {endpoint_id} (model={args.model})...")
    try:
        job_id = submit_job(audio_path, endpoint_id, api_key, args.model, not args.no_word_timestamps)
    except CreditsExhaustedError as e:
        print("=" * 70)
        print(f"[CREDITS EXHAUSTED] {e}")
        print("Job was not submitted. Top up the RunPod account balance and re-run.")
        print("=" * 70)
        sys.exit(1)

    print(f"Job {job_id} submitted, polling for completion (timeout {POLL_TIMEOUT_S}s)...")
    try:
        result = poll_job(job_id, endpoint_id, api_key)
    except CreditsExhaustedError as e:
        print("=" * 70)
        print(f"[CREDITS EXHAUSTED] {e}")
        print(f"Job {job_id} was submitted but polling failed due to balance. Check the RunPod")
        print("dashboard directly for this job's outcome before re-running.")
        print("=" * 70)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result.get("output", result), indent=2))
    exec_ms = result.get("executionTime")
    print(f"Wrote {out_path}" + (f" (execution: {exec_ms}ms)" if exec_ms else ""))


if __name__ == "__main__":
    main()
