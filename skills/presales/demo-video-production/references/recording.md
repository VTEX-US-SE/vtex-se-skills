# Recording the live demo

## Hard rule: interact freely, never confirm or save

Opening forms, typing into fields, walking through checkout and clicking menus are all allowed.
**Clicking Save / Publish / Confirm order / Complete purchase, or any button that persists a
change, is never allowed.** The demo shows the capability up to the decision point and stops. This
applies to every tool and every account, sandbox included: a saved edit on a shared demo account
can break another SE's script.

Related lessons:
- **One "real" click can hide a second execution click.** AI admin agents often open a review
  panel with its own "Start update" button. If a real execution is ever authorized, authorize that
  exact button, not "the flow".
- **"Roll back" buttons are not a guarantee.** One was tested and did not revert. Treat any real
  execution as permanent.
- **Real customer production accounts** are public storefront only: never open their Admin, never
  place an order. Re-check that the site is live and still on VTEX on the recording day.
- Use the team's demo/sandbox accounts (e.g. `*.b2cdemostore.com`). Never put account passwords in
  any tracked file; ask the account owner.

## Default method: stills, not continuous video

For audio-first videos, capture a **still per meaningful state** ("cart with 2 items", "after
switching to LTL") and hold each for its share of the segment's real narration. Continuous
bot-driven recording looks wrong on camera (no cursor dwell, no reading pauses) and hits the
gotchas below.

Tools:
- **Navigation/clicks:** `claude-in-chrome` (DOM-level) on the real site.
- **Capture:** `scripts/capture_chrome_window.sh <url-substring> demos/<segment>/<nn>_<state>.png`.
  It brings the matching tab to the front and runs `screencapture -R` on **that window's region
  only**.

Why not `claude-in-chrome`'s own screenshot: with `save_to_disk` it attaches the image to the chat
and doesn't give the agent a file path for ffmpeg.

## macOS setup (once per machine)

Grant **both** to the app that runs your agent (Claude desktop, Terminal, iTerm... find it by
walking up `ps -p $$ -o pid,ppid,comm`):
1. Privacy & Security → **Screen Recording** (lets `screencapture` read pixels)
2. Privacy & Security → **Accessibility** (lets System Events raise the right window)

Then **fully quit and reopen that app**. A permission granted while the process is running doesn't
apply, and the same error on every retry is the tell.

Before capturing: turn on **Focus / Do Not Disturb**. A full-screen capture once grabbed a private
Slack DM preview. The helper never captures full screen; keep it that way.

## Capture checklist

- Wait for the page to hydrate (2-4 s on VTEX storefronts). An early capture shows skeleton
  loaders.
- For a genuinely logged-out state, open an **incognito** window
  (`tell application "Google Chrome" to make new window with properties {mode:"incognito"}`)
  instead of fighting a session cookie that the in-app "Logout" doesn't clear.
- Close system dialogs (sleep warnings, update prompts) before the shot.
- Crop out browser chrome per still (tab strip, address bar, and the
  `"Claude" started debugging this browser` infobar when present). The crop offset varies still
  to still, so inspect each image. Keep the site's own promo banners; they're real page content.
- Save every still under `demos/<segment-slug>/`, never only in a tool's temp or attachment state.

## Turning stills into a segment clip

For each still: crop the browser chrome, scale and pad to 16:9 (border color matching the page),
hold for its duration, normalize:

```bash
ffmpeg -y -loop 1 -i demos/seg1/01_pdp.png -t 15.6 \
  -vf "crop=iw:ih-<chrome_px>:0:<chrome_px>,scale=1920:-2,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" \
  -r 30 -pix_fmt yuv420p -c:v libx264 -profile:v high -level:v 4.0 -video_track_timescale 90000 final/seg1_01.mp4
```

Split a segment's real narration across its stills by which part of the narration describes which
state (roughly proportional to words). Concat the stills of one segment with `-c copy`, then hand
the segment clip to `assemble.py`.

## When you need continuous capture

Use `ffmpeg -f avfoundation` (list devices with `ffmpeg -f avfoundation -list_devices true -i ""`,
and target the display Chrome actually sits on).

- OS capture shows whatever tab is **frontmost**, not the tab the automation drives. Raise it
  first (the AppleScript in `capture_chrome_window.sh`).
- The coordinating session must own the `ffmpeg` process. Sub-agent/worker sandboxes kill their
  process group at the end of each command, even `nohup`/`disown`ed children. Stop with
  `kill -INT <pid>`, never `SIGKILL`, which corrupts the MP4 ("moov atom not found").
- Trim the operator's own latency (checking state, deciding the next click) with keyframe cuts
  **before** writing narration to the take. Never stretch narration over the raw take.
- Takes from different sessions can differ in content, not just codec: verify it's the same
  data before joining them.

## When a click doesn't register

Some VTEX Admin components (Styleguide tables, some agent chat buttons) ignore CDP/DOM-dispatched
clicks. An OS-level accessibility click works (for example Orca's `orca computer click`, or any
computer-use tool). Otherwise, ask the human to click that one element, give them the exact
URL + element, and wait for a DOM condition.

## Tools evaluated and not adopted

- **Playwright MCP recording:** never needed once the stills approach worked.
- **browser-use / browser-harness / macos-harness / video-use:** none records a deterministic demo
  end to end. `browser-harness` is useful to map Admin selectors once.
- **Guidde / Arcade** (human clicks, AI narrates): a different category, not integrated here.
