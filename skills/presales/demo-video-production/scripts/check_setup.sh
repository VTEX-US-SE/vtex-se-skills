#!/usr/bin/env bash
# check_setup.sh — preflight for the demo-video-production skill. Spends no credits, prints no
# secret values: it only says whether each key is present.
HERE="$(cd "$(dirname "$0")" && pwd)"
ok=0; warn=0
pass() { echo "  ok    $1"; }
fail() { echo "  MISS  $1"; ok=1; }
note() { echo "  warn  $1"; warn=1; }

echo "Tools"
for bin in ffmpeg ffprobe python3; do
  command -v "$bin" >/dev/null && pass "$bin" || fail "$bin (brew install ffmpeg python)"
done
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] || command -v google-chrome >/dev/null || [ -n "${CHROME_BIN:-}" ]; then
  pass "Google Chrome (slide PNG rendering)"
else
  fail "Google Chrome (or set CHROME_BIN)"
fi
if command -v node >/dev/null; then
  major=$(node -p 'process.versions.node.split(".")[0]')
  [ "$major" -ge 22 ] && pass "node $major (Hyperframes)" || note "node $major found, Hyperframes needs 22+"
else
  note "node not found (only needed for Hyperframes animated slides)"
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' && pass "python >= 3.10" || fail "python 3.10+ required"

echo "Keys (values are never printed)"
for var in ELEVENLABS_API_KEY RUNPOD_FASTER_WHISPER_API_KEY RUNPOD_FASTER_WHISPER_ENDPOINT_ID; do
  if python3 -c "import sys; sys.path.insert(0, '$HERE'); from _env import find_env_var; sys.exit(0 if find_env_var('$var') else 1)"; then
    pass "$var"
  else
    fail "$var (add it to ~/.config/vtex-se-skills/.env)"
  fi
done

echo "Brand font (proprietary, never in the repo)"
fontdir="${VTEX_BRAND_FONTS_DIR:-$HOME/.config/vtex-se-skills/fonts}"
missing=""
for w in Regular Medium Italic; do
  [ -f "$fontdir/VTEXTrust-$w.otf" ] || [ -f "$fontdir/VTEXTrust-$w.b64" ] || missing="$missing $w"
done
[ -z "$missing" ] && pass "VTEX Trust in $fontdir" || note "VTEX Trust missing:$missing (slides fall back to Helvetica; see README)"

echo "macOS recording (only for from-scratch videos with live demo stills)"
if [ "$(uname)" = "Darwin" ]; then
  command -v screencapture >/dev/null && pass "screencapture" || fail "screencapture"
  note "Screen Recording + Accessibility permissions can't be checked from here; see README"
else
  note "not macOS: the demo-capture helper won't run, everything else will"
fi

echo
[ $ok -eq 0 ] && echo "Ready." || echo "Fix the MISS lines above first."
exit $ok
