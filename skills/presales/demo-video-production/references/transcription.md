# Transcription — RunPod Faster Whisper

## Why RunPod, not local

Whisper-family models run CPU-only on a Mac (`ctranslate2` has no Metal backend). The "small" model
takes ~2 min for 8 min of audio, but "medium"/"large" take 15-40 min. A serverless RunPod endpoint
bills per second of execution, so there's no idle server to forget about.

## Endpoint

- Worker: `runpod-workers/worker-faster_whisper` (official RunPod org, MIT), deployed from the
  RunPod Hub. The team endpoint uses a 24GB GPU tier.
- Credentials: `RUNPOD_FASTER_WHISPER_API_KEY` + `RUNPOD_FASTER_WHISPER_ENDPOINT_ID`. The key is
  endpoint-scoped ("Restricted"), so `--check-balance` returns 401/403. That's expected and never
  blocks a run.
- Do **not** use the older WhisperX worker (`kodxana/whisperx-worker_v2`). It's unmaintained and
  RunPod rejects its job results with `400 Bad Request` at every audio size.

## Running it

```bash
# 1. Extract audio small enough for the 10MiB request cap (64kbps mono MP3 ≈ 10-11 min per request)
ffmpeg -i raw/<video>.mp4 -vn -ac 1 -ar 44100 raw/audio_original.wav
ffmpeg -i raw/audio_original.wav -ac 1 -b:a 64k raw/audio_original_64kbps.mp3

# 2. Transcribe
python3 scripts/transcribe_runpod.py raw/audio_original_64kbps.mp3 --out transcript/audio_original.json
```

Real timings: a 10-minute chunk takes ~7-14 s of execution.

**Longer than ~10 minutes:** split into chunks (`ffmpeg -ss <start> -t 600 ...`), transcribe each,
then add each chunk's start offset to every `start`/`end` when merging. RunPod returns a clear
`exceeded max body size of 10MiB` if a chunk is too big.

## Output shape

```json
{
  "segments": [{"id": 0, "start": 0.0, "end": 4.2, "text": "..."}],
  "word_timestamps": [{"word": "Hello", "start": 0.12, "end": 0.40}],
  "transcription": "plain concatenated text",
  "detected_language": "en"
}
```

There are no nested `segments[].words[]`, no per-word `score` and no diarization. Demos are
single-presenter, so diarization was never needed.

## Lessons

- **Check word-level timestamps before deciding a boundary has no room.** A segment's own
  `start`/`end` can hide long silences inside it. One segment read `351.8s→378.8s` with no gap, but
  the words showed a 17.4 s silence in the middle. Filter `word_timestamps` by time range to find
  real gaps before reaching for a freeze-frame.
- **Build a compact phrase view for review.** Group words into phrases on ≥0.5 s silences
  (`[start-end] text`), which is much easier to read than the raw word list.
- **`Vitex` → `VTEX` only when the sentence still makes sense.** It's the most common ASR brand
  slip, but not every "Vitex's" is the company. "Either their own or VTEX's. their favorite
  players." was really garbled speech about someone's favorite player. When the substitution
  doesn't make the sentence read right, flag it as garbled and infer the meaning explicitly
  instead of auto-replacing.
- **The transcript standardizes into `script.md`.** Write it in English: a metadata header (video,
  duration, voice, language), then the narration with a timestamp per segment
  (`**[mm:ss]** text`). Never overwrite a richer pre-production script; keep it as a separate file.
