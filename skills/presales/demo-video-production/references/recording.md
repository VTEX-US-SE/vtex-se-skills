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
- **Navigation/clicks:** `claude-in-chrome` (DOM-level) by default; GPT computer-use (OS-level
  clicks) for the screens that ignore DOM clicks. See "Driving the browser" below.
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

## Driving the browser

Two automation surfaces, and they are **not interchangeable**:

| Surface | What it is | Use it for |
|---|---|---|
| **`claude-in-chrome`** (default) | Claude's Chrome extension, DOM-level: navigate, find elements, click, type, read the page | Storefronts, checkout, most Admin screens |
| **GPT computer-use** (OpenAI's computer-use tool, e.g. in Codex) | Real OS-level mouse/keyboard input through macOS accessibility | Screens that silently ignore DOM clicks |

### Before the first action

1. Write the segment's action list into `RECORDING_TASK.md` (`templates/recording-task-template.md`)
   **before** touching the browser: start URL, each click/type with the exact label, the stop
   point, and which still to capture after which step.
2. Walk it once **without capturing** (an exploration pass) and correct the list with what the
   real screen shows: labels, how many clicks a tree needs, what data already exists. Screens drift
   from the script more often than not.
3. Park the browser on a neutral start state (e.g. `<account>.myvtex.com/admin` home, or the
   storefront home) so every take starts from the same place.

### With `claude-in-chrome`

- Load all the tools you'll need in **one** tool search: `tabs_context_mcp`, `tabs_create_mcp`,
  `navigate`, `find`, `computer`, `read_page`, plus `form_input` / `get_page_text` if needed.
- Call `tabs_context_mcp` first, then **open a new tab** with `tabs_create_mcp`. Never drive a tab
  the user already had open, and never reuse tab ids from another session.
- Locate elements with `find` / `read_page` by their visible label, then click the element found.
  Don't click at guessed coordinates; a coordinate click can "succeed" and miss.
- After each action, **verify the screen changed** (new URL, new element, updated cart), not just
  that the call returned. Wait for hydration (skeleton loaders gone) before the next step.
- **Never trigger a browser dialog** (`alert`/`confirm`, "are you sure?" delete buttons): it blocks
  the extension until a human dismisses it. If a step needs one, stop and ask.
- Typing into plain inputs (search boxes, chat inputs) works reliably. Failures are specific to
  some custom buttons and table rows.

### Switch to GPT computer-use when a click doesn't register

Known cases: `contracts-management`'s Styleguide table rows and expand chevrons, and the Contract
Manager Agent's suggestion buttons. The click "succeeds" but nothing changes: the component
rejects the synthetic event. Rule of thumb: **try `claude-in-chrome` first; if nothing visibly
changed after 2 tries, do that step with computer-use.**

- Hand the computer-use agent the exact step from `RECORDING_TASK.md` (URL, visible label, what
  the screen should show afterwards), plus the hard rule: never click
  Save/Confirm/Execute/Place order.
- It clicks through macOS accessibility, so the same Screen Recording + Accessibility permissions
  apply to the app running it. The Chrome window must be visible (not minimized).
- Let it do **only the clicks**. The coordinating session keeps ownership of any capture process
  and of `capture_chrome_window.sh` (worker sandboxes kill their child processes).
- Proven case: computer-use drove the Contract Manager Agent end to end (opened the contract,
  clicked "Add assortments", answered the agent's two clarifying questions, and stopped at "shall I
  proceed?") after DOM clicks had failed on the same buttons.

### Last resort: a human click

If neither surface can do it, give the person the exact URL and element label, then wait for a
confirmed DOM condition (e.g. `find` returns the next screen's element) instead of polling
screenshots. Record that stretch continuously and cut the wait out afterwards.

### Demo data

- Check live which data is already in the account before choosing values. Pick a combination that
  isn't there yet (e.g. an assortment not yet linked to the contract), and note the "already used"
  values in `RECORDING_TASK.md` so re-takes don't collide.
- Don't touch another segment's login session or cart unless that segment's instructions say so.
- Intermittently blank Admin screens (sidebar only) are usually a flaky demo account: reload once
  or twice, wait a few seconds, then escalate.

## Tools evaluated and not adopted

- **Playwright MCP recording:** never needed once the stills approach worked.
- **browser-use / browser-harness / macos-harness / video-use:** none records a deterministic demo
  end to end. `browser-harness` is useful to map Admin selectors once.
- **Guidde / Arcade** (human clicks, AI narrates): a different category, not integrated here.
