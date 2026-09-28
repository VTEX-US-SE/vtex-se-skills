#!/usr/bin/env bash
# capture_chrome_window.sh URL_SUBSTRING OUT.png
# Brings the Chrome tab whose URL contains URL_SUBSTRING to the front and screenshots ONLY that
# window's region (never the full screen — a full-screen grab once caught a private Slack DM).
# Navigation/clicks are done separately (e.g. claude-in-chrome); this only captures a still.
#
# macOS only. Needs Screen Recording AND Accessibility permission for the app running your agent
# (Claude desktop, Terminal, iTerm...), then a full quit + reopen of that app.
# Turn on Focus / Do Not Disturb before capturing so no notification lands in the shot.
set -euo pipefail
MATCH="$1"; OUT="$2"

osascript - "$MATCH" <<'APPLESCRIPT'
on run argv
  set needle to item 1 of argv
  tell application "Google Chrome"
    set targetWin to missing value
    set targetTabIdx to 0
    repeat with w in windows
      set tIdx to 0
      repeat with t in tabs of w
        set tIdx to tIdx + 1
        if (URL of t) contains needle then
          set targetWin to w
          set targetTabIdx to tIdx
        end if
      end repeat
    end repeat
    if targetWin is missing value then error "No Chrome tab URL contains: " & needle
    set active tab index of targetWin to targetTabIdx
    set index of targetWin to 1
    activate
  end tell
  tell application "System Events" to tell process "Google Chrome" to set frontmost to true
end run
APPLESCRIPT

sleep 1
read -r X Y W H < <(osascript -e 'tell application "System Events" to tell process "Google Chrome" to get {position, size} of window 1' | tr -d ',' )
mkdir -p "$(dirname "$OUT")"
screencapture -x -R"$X,$Y,$W,$H" "$OUT"
echo "captured $OUT (${W}x${H} at ${X},${Y})"
