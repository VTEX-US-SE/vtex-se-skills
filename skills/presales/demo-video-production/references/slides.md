# Slides — VTEX brand kit, static PNG or Hyperframes

## Brand rules (official VTEX Design System)

Brand type rules: *"Regular only · never ALL CAPS · never bold titles."*

- Light background is **White Ice `#F8F7FC`**.
- Font is the real **VTEX Trust**, embedded as base64 by `vtex_brand.py`, never Helvetica as the
  primary. It's proprietary, so it's loaded from `~/.config/vtex-se-skills/fonts/` (or
  `$VTEX_BRAND_FONTS_DIR`) and never committed to this public repo.
- Titles are `font-weight: 400`. Hierarchy comes from size and color.
- Kickers/labels: sentence case, weight 500 at most, no `text-transform: uppercase`, no
  `letter-spacing`, no right-aligned text.
- Rebel Pink `#F71963` is a small accent (meridian line, one label, one CTA). Serious Black
  `#142032` carries text. Never use the two as equal-weight primaries.
- The logo is the official one-path monochrome glyph+wordmark (`assets/vtex-brand/logo/`).

Tokens are in `assets/vtex-brand/tokens.css`. Every generator imports `vtex_brand.py`, so never
hand-write a palette, font stack or logo SVG. For other brand questions (decks, docs, diagrams),
use the `vtex-brand-guidelines` skill in this repo.

## Describing slides

Write `<video-folder>/slides.json` (start from `templates/slides.example.json`):

| type | fields | PNG | Hyperframes |
|---|---|---|---|
| `opening` | kicker, title, subtitle | ✓ | ✓ |
| `split` | kicker, title, columns: two `{label, items[]}` | ✓ | ✓ |
| `grid` | kicker, title, blocks: `[num, heading, body][]`, optional `cta {line,url}` or `proof_line` | — | ✓ |
| `closing` | kicker, title, recap, optional `cta`, `cta_url` | ✓ | ✓ |

The structure that tested well across 8 real team videos: an opening slide, an optional capability
map (numbered agenda, pain-point or numbered flow, always with one social-proof element), the
demo, then a closing slide with a recap and a CTA. A `grid` with `cta` shows green checkmarks,
which makes it a "proof" recap, while a `grid` with `proof_line` is a "pitch" map. The default CTA
URL is `dev.vtex.com/en-us/get-started/`.

## Method 1 — Static PNG

```bash
python3 scripts/build_slides.py slides.json --out slides --render            # 1920x1080
python3 scripts/build_slides.py slides.json --out slides --render --size 1280x720
scripts/build_slide_clip.sh slides/seg0_hook.png <narration_seconds> final/seg0_hook.mp4
```

- Rendering uses headless Chrome over a temporary local HTTP server (`file://` is unreliable).
  Don't use `claude-in-chrome` screenshots for slides: they're limited to the physical screen and
  lossy.
- The HTML uses a fixed 1920x1080 canvas scaled by JS to the window, so it renders correctly at any
  output resolution. Never use `vw`/`vh`/`clamp()` tuned on a small preview.
- No new dependencies and no motion. Fine for simple slides.

## Method 2 — Hyperframes (default for new videos)

Animated HTML + GSAP rendered to a real MP4: the meridian line and logo enter, then the text and
cards stagger in, then everything holds. Apache 2.0, no per-render fee.

One-time setup per machine (Node 22+):
```bash
export HYPERFRAMES_NO_TELEMETRY=1        # telemetry is ON by default; always disable it
npx --yes hyperframes browser ensure     # downloads Chrome Headless Shell (~93MB), first run only
```

Per video:
```bash
cd <video-folder> && npx --yes hyperframes init hyperframes-project
python3 <skill>/scripts/build_slides.py slides.json --out hyperframes-project
cd hyperframes-project
npx --yes hyperframes render -c seg0_hook.html --output renders/seg0_hook.mp4
ffmpeg -y -i renders/seg0_hook.mp4 -c copy -video_track_timescale 90000 renders/seg0_hook_norm.mp4
```

`build_slides.py` prints the exact render + normalize commands for every slide. Durations come from
each slide's `audio` (ffprobed) or `duration`. `data-duration` renders to exactly that frame count
(verified on 30+ renders).

- Each slide is a **standalone** composition and becomes its own MP4, muxed with its own narration
  and concatenated externally. Don't build one long sub-composition video.
- **Always normalize the render's `time_base`** (the `-video_track_timescale 90000` remux above)
  before concatenating with anything else.
- Renders are 1920x1080. If the delivery resolution differs, apply `scale=WxH` in the final pass.
- ~330 s of slides rendered in ~143 s on first production use, with no iteration round.

To use a custom layout, import `slides_hyperframes.py` / `slides_png.py` from Python and follow the
same pattern. For deeper Hyperframes work (new motion, transitions), use the `hyperframes` skill.

## Retrofitting a delivered video

Swap a slide's look without touching narration or footage:
1. Extract its audio: `ffmpeg -i old_clip.mp4 -vn -c:a copy audio.m4a`.
2. Re-render the slide at the exact original duration.
3. Mux the two with `-map 0:v -map 1:a -c copy -shortest`.
4. Re-concatenate.

If the video is one monolithic file, find the slide's window with a contact sheet plus an extracted
frame. Never guess timestamps.
