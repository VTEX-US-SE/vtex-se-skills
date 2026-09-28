# Voice — ElevenLabs Speech-to-Speech and TTS

## Pick the method

| Situation | Method | Script |
|---|---|---|
| Existing video, same words, just a new voice | **Speech-to-Speech** (keeps rhythm and pauses, so the existing screen recording stays in sync) | `speech_to_speech.py` |
| Existing video, a handful of lines need different words | **Hybrid**: one S2S pass for the whole track + short TTS patches spliced into those lines' time windows | both |
| Existing video, nearly every line's wording changes | **Per-block TTS**, each block placed at its original timestamp with silence filling the gaps | `generate_tts.py` |
| From-scratch video | **Per-segment TTS** from `production-script.md` | `generate_tts.py` |

How to classify each script edit:
- **Transcript-only fixes** (brand slips like `Vitex`→`VTEX`, obvious ASR typos) are errors in
  the transcript, not in the speech. The speaker said it right, so S2S already produces the
  correct audio.
- **Content changes** (rewording "I'm going to show you" → "we're going to show you", completing a
  garbled phrase) change the actual words. S2S can't do that, so those lines need TTS.

Cost matters too. S2S bills ~1000 credits per minute of audio regardless of how much changed, and
TTS bills per character. When most lines are unchanged, the hybrid is both more faithful to the
original timing and cheaper.

## Voices

| Name | Voice ID | Register | Status |
|---|---|---|---|
| Roger | `CwhRBWXzGAHq8TQ4Fs17` | male, american, classy, conversational | validated |
| Sarah | `EXAVITQu4vr4xnSDxMaL` | female, american, mature, confident | validated |

Both are ElevenLabs stock voices (not clones of real people) and available on every account.
Other stock female voices worth auditioning: Bella, Laura, Alice (british), Matilda, Jessica, Lily.

**Preview rule:** a ~30 s preview, approved by the requester, is required only the first time a
voice enters the pipeline. Roger and Sarah are already validated, so go straight to the full run.

```bash
python3 scripts/speech_to_speech.py raw/audio_original.wav --voice-id <id> --preview 30 \
  --out audio/audio_s2s_<name>_preview30s.mp3 --confirm
```

## Models and settings

- S2S: `eleven_multilingual_sts_v2`. Measured drift is ~0.02% (≈0.1 s over 8 min 17 s). The last
  re-encoded clip in the edit absorbs it (see video-editing.md).
- TTS: `eleven_turbo_v2_5`, stability 0.5, similarity 0.75.
- `speech_to_speech.py` sends at most 240 s per request by default (`--max-chunk`), split at
  detected silences. ElevenLabs' API reference documents no duration limit for this endpoint, so
  240 s is a conservative choice. Raise it only after a real test.

## Credits and the key

- A paid plan is required for commercial use (Free requires attribution). The per-minute price is
  the same on every paid tier.
- Cost reference: an 8 min video ≈ 8300 credits of S2S.
- **Check both ceilings before a big job:** the plan total *and* the API key's own "credit refresh
  period" cap (Developers → API Keys → Edit). They're independent and have drifted out of sync
  twice. A run that dies mid-way leaves a confusing partial audio set.
- The team key is scoped to TTS / Speech-to-Speech / Audio Isolation / Voice Generation only, so
  `generate_tts.py --check-credits` returns `401 missing_permissions: user_read`. That's expected.
  Don't widen the key's scope. The reactive out-of-credits check during a real call is the one
  that matters.

## Gotchas

- **Never concat MP3 pieces with `-c copy`.** Each MP3 carries encoder padding that accumulates:
  ~49 pieces came out 1.9 s longer than their sum. Convert every piece to WAV (`pcm_s16le`),
  concat the WAVs, and encode to AAC only at the final mux. Both scripts already write WAV
  siblings.
- **Bracketed stage directions get read aloud.** `[CTA link]` in a narration blockquote became
  spoken words. Strip every bracket from narration before running TTS, and keep URLs as on-screen
  text only.
- **If a TTS block runs longer than its original slot,** the fix is a freeze-frame: hold the last
  frame while the narration finishes (`build_footage_clip.sh` pads with a cloned last frame). Check
  the word-level timestamps first, though. Real slack is usually bigger than segment boundaries
  suggest.
- **Don't reach for RVC (local voice conversion) as a free alternative.** Public `.pth` voice
  models are unverified pickles (they can execute code), and most clone real people. Shelved.
