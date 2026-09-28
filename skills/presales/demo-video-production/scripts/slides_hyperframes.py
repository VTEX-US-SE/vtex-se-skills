#!/usr/bin/env python3
"""Animated slide compositions (Method 2: HTML + GSAP -> `npx hyperframes render` -> MP4), on the
real VTEX brand kit from vtex_brand.py.

Duration contract (verified empirically across 30+ production renders): `data-duration` set to the
exact seconds (e.g. "14.566667") renders to exactly that frame count. Pass the ffprobe-measured
duration of the narration this slide sits under.

Every composition shares one motion language: meridian line scales in, brandmark fades in, then
kicker/title/content fade and slide up in a stagger, then hold static for the rest of the clip.

Use through build_slides.py; import directly only for a custom layout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vtex_brand import FONT_FACES, TOKENS_CSS, logo_svg

HEAD = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
{FONT_FACES}
{TOKENS_CSS}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%;overflow:hidden;background:var(--bg);
  font-family:var(--sans);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}}
#root{{width:100%;height:100%;position:relative;background:var(--bg);overflow:hidden}}
.meridian{{position:absolute;top:0;left:150px;width:3px;height:1080px;z-index:2;background:var(--pink);
  transform-origin:top center}}
.brandmark{{position:absolute;top:56px;left:196px;height:36px;z-index:6}}
.kicker{{font-size:20px;font-weight:500;color:var(--pink);
  display:flex;align-items:center;gap:14px;margin:0 0 28px}}
.kicker::before{{content:"";width:32px;height:3px;background:var(--pink);display:inline-block}}
'''


def opening_composition(comp_id, duration, kicker, title, subtitle, fps=30):
    return HEAD + f'''
.content{{position:absolute;left:196px;top:0;width:1400px;height:1080px;
  display:flex;flex-direction:column;justify-content:center}}
.cover-title{{font-weight:400;font-size:88px;line-height:1.05;letter-spacing:-1px;margin:0;color:var(--ink)}}
.subtitle{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:32px;line-height:1.4;
  color:var(--gray);max-width:1100px;margin:32px 0 0}}
</style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-width="1920" data-height="1080" data-fps="{fps}" data-duration="{duration}">
  <div class="meridian" id="meridian"></div>
  <div class="brandmark" id="brandmark">{logo_svg()}</div>
  <div class="content">
    <p class="kicker" id="kicker">{kicker}</p>
    <h1 class="cover-title" id="title">{title}</h1>
    <p class="subtitle" id="subtitle">{subtitle}</p>
  </div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
gsap.set("#meridian", {{ scaleY: 0 }});
gsap.set("#brandmark", {{ opacity: 0, y: -12 }});
tl.to("#meridian", {{ scaleY: 1, duration: 0.5, ease: "power2.out" }}, 0);
tl.to("#brandmark", {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, 0.1);

gsap.set(["#kicker","#title","#subtitle"], {{opacity:0, y:24}});
tl.to("#kicker", {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, 0.3);
tl.to("#title", {{opacity:1, y:0, duration:0.6, ease:"power3.out"}}, 0.5);
tl.to("#subtitle", {{opacity:1, y:0, duration:0.6, ease:"power3.out"}}, 0.85);

window.__timelines["{comp_id}"] = tl;
</script>
</body>
</html>
'''


def closing_composition(comp_id, duration, kicker, title, recap_line,
                         cta="Ready to see it on your own catalog?", fps=30,
                         cta_url="dev.vtex.com/en-us/get-started/"):
    return HEAD + f'''
.content{{position:absolute;left:196px;top:150px;width:1528px;height:780px}}
.map-title{{font-weight:400;font-size:56px;line-height:1.1;letter-spacing:-0.5px;margin:0 0 56px;
  color:var(--ink);max-width:1400px}}
.recap-row{{border-top:1px solid var(--border);padding-top:40px;margin-bottom:56px}}
.recap-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:30px;line-height:1.5;
  color:var(--gray);max-width:1200px}}
.cta-row{{padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:baseline;gap:18px}}
.cta-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:26px;color:var(--gray)}}
.cta-link{{color:var(--pink);font-style:normal;font-weight:500;
  border-bottom:2px solid rgba(247,25,99,.35);padding-bottom:4px}}
</style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-width="1920" data-height="1080" data-fps="{fps}" data-duration="{duration}">
  <div class="meridian" id="meridian"></div>
  <div class="brandmark" id="brandmark">{logo_svg()}</div>
  <div class="content">
    <p class="kicker" id="kicker">{kicker}</p>
    <h1 class="map-title" id="title">{title}</h1>
    <div class="recap-row" id="recap"><p class="recap-line">{recap_line}</p></div>
    <div class="cta-row" id="cta">
      <p class="cta-line">{cta}</p>
      <span class="cta-link">{cta_url}</span>
    </div>
  </div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
gsap.set("#meridian", {{ scaleY: 0 }});
gsap.set("#brandmark", {{ opacity: 0, y: -12 }});
tl.to("#meridian", {{ scaleY: 1, duration: 0.35, ease: "power2.out" }}, 0);
tl.to("#brandmark", {{ opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }}, 0.05);

gsap.set(["#kicker","#title","#recap","#cta"], {{opacity:0, y:20}});
tl.to("#kicker", {{opacity:1, y:0, duration:0.3, ease:"power3.out"}}, 0.15);
tl.to("#title", {{opacity:1, y:0, duration:0.35, ease:"power3.out"}}, 0.3);
tl.to("#recap", {{opacity:1, y:0, duration:0.35, ease:"power2.out"}}, 0.55);
tl.to("#cta", {{opacity:1, y:0, duration:0.35, ease:"power2.out"}}, 0.8);

window.__timelines["{comp_id}"] = tl;
</script>
</body>
</html>
'''


def split_capmap_composition(comp_id, duration, kicker, title, col_a_label, col_a_items,
                              col_b_label, col_b_items, fps=30):
    def col_html(label, items, idx):
        lis = "".join(f'<p class="item" data-i="{idx}-{i}">{it}</p>' for i, it in enumerate(items))
        return f'<div class="col" id="col{idx}"><h3>{label}</h3>{lis}</div>'
    return HEAD + f'''
.content{{position:absolute;left:196px;top:150px;width:1528px;height:780px}}
.map-title{{font-weight:400;font-size:52px;line-height:1.1;letter-spacing:-0.5px;margin:0 0 48px;
  color:var(--ink);max-width:1400px}}
.cols{{display:flex;gap:48px;border-top:1px solid var(--border);padding-top:40px}}
.col{{flex:1;padding:0 8px}}
.col h3{{font-weight:500;font-size:30px;color:var(--pink);margin:0 0 22px}}
.col .item{{font-weight:400;font-size:20px;line-height:1.5;color:var(--ink);
  padding:14px 0;border-top:1px solid var(--border)}}
.col .item:first-of-type{{border-top:none}}
</style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-width="1920" data-height="1080" data-fps="{fps}" data-duration="{duration}">
  <div class="meridian" id="meridian"></div>
  <div class="brandmark" id="brandmark">{logo_svg()}</div>
  <div class="content">
    <p class="kicker" id="kicker">{kicker}</p>
    <h1 class="map-title" id="title">{title}</h1>
    <div class="cols">
      {col_html(col_a_label, col_a_items, 0)}
      {col_html(col_b_label, col_b_items, 1)}
    </div>
  </div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
gsap.set("#meridian", {{ scaleY: 0 }});
gsap.set("#brandmark", {{ opacity: 0, y: -12 }});
tl.to("#meridian", {{ scaleY: 1, duration: 0.35, ease: "power2.out" }}, 0);
tl.to("#brandmark", {{ opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }}, 0.05);

gsap.set(["#kicker","#title"], {{opacity:0, y:20}});
gsap.set("#col0 h3, #col0 .item, #col1 h3, #col1 .item", {{opacity:0, y:18}});
tl.to("#kicker", {{opacity:1, y:0, duration:0.3, ease:"power3.out"}}, 0.15);
tl.to("#title", {{opacity:1, y:0, duration:0.35, ease:"power3.out"}}, 0.3);
tl.to("#col0 h3, #col0 .item", {{opacity:1, y:0, duration:0.3, ease:"power2.out", stagger:0.08}}, 0.6);
tl.to("#col1 h3, #col1 .item", {{opacity:1, y:0, duration:0.3, ease:"power2.out", stagger:0.08}}, 0.75);

window.__timelines["{comp_id}"] = tl;
</script>
</body>
</html>
'''


def block_grid_composition(comp_id, duration, kicker, title, blocks, cta=None, fps=30,
                            proof_line=None):
    """blocks: list of (num, heading, body) tuples, rendered as a row of cards.
    cta: optional (line, url) tuple -> renders a CTA row with a checkmark-free layout.
    proof_line: optional italic one-liner under the grid (used on the capability-map slide,
    mutually exclusive with cta — checkmarks appear automatically when cta is set, matching the
    existing recap-vs-map distinction: map = pitch (no checkmarks), recap = proof (checkmarks)."""
    show_checks = cta is not None

    def block_html(num, heading, body):
        check = ('<div class="check"><svg viewBox="0 0 24 24" fill="none">'
                 '<path d="M4 12.5L9.5 18L20 6" stroke="#2ECC71" stroke-width="2.6" '
                 'stroke-linecap="round" stroke-linejoin="round"/></svg></div>') if show_checks else ""
        return (f'<div class="block">{check}<p class="num">{num}</p>'
                f'<h3>{heading}</h3><p>{body}</p></div>')

    blocks_html = "".join(block_html(n, h, b) for n, h, b in blocks)

    tail_html = ""
    if cta:
        line, url = cta
        tail_html = (f'<div class="cta-row" id="tail"><p class="cta-line">{line}</p>'
                      f'<span class="cta-link">{url}</span></div>')
    elif proof_line:
        tail_html = (f'<div class="proof-row" id="tail"><span class="proof-dash"></span>'
                      f'<p class="proof-line">{proof_line}</p></div>')

    return HEAD + f'''
.content{{position:absolute;left:196px;top:150px;width:1528px;height:780px}}
.map-title{{font-weight:400;font-size:52px;line-height:1.1;letter-spacing:-0.5px;margin:0 0 48px;
  color:var(--ink);max-width:1300px}}
.blocks{{display:flex;gap:26px}}
.block{{flex:1;background:var(--bg-white);border:1px solid var(--border);
  border-radius:18px;padding:32px 26px;position:relative}}
.block .num{{font-weight:500;font-size:20px;color:var(--pink);margin:0 0 16px}}
.block h3{{font-weight:500;font-size:25px;line-height:1.15;color:var(--ink);margin:0 0 12px}}
.block p{{font-size:17px;line-height:1.42;color:var(--gray);margin:0}}
.check{{position:absolute;top:26px;right:26px;width:34px;height:34px;border-radius:50%;
  background:rgba(46,204,113,.12);border:1.5px solid rgba(46,204,113,.55);
  display:flex;align-items:center;justify-content:center}}
.check svg{{width:17px;height:17px}}
.cta-row{{margin-top:56px;display:flex;align-items:baseline;gap:18px}}
.cta-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:26px;color:var(--gray)}}
.cta-link{{color:var(--pink);font-style:normal;font-weight:500;
  border-bottom:2px solid rgba(247,25,99,.35);padding-bottom:4px}}
.proof-row{{margin-top:56px;display:flex;align-items:center;gap:18px}}
.proof-dash{{width:32px;height:3px;background:var(--pink);display:inline-block;flex:none}}
.proof-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:28px;line-height:1.4;
  color:var(--gray);max-width:1100px}}
</style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-width="1920" data-height="1080" data-fps="{fps}" data-duration="{duration}">
  <div class="meridian" id="meridian"></div>
  <div class="brandmark" id="brandmark">{logo_svg()}</div>
  <div class="content">
    <p class="kicker" id="kicker">{kicker}</p>
    <h1 class="map-title" id="title">{title}</h1>
    <div class="blocks" id="blocks">
      {blocks_html}
    </div>
    {tail_html}
  </div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
gsap.set("#meridian", {{ scaleY: 0 }});
gsap.set("#brandmark", {{ opacity: 0, y: -12 }});
tl.to("#meridian", {{ scaleY: 1, duration: 0.35, ease: "power2.out" }}, 0);
tl.to("#brandmark", {{ opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }}, 0.05);

gsap.set(["#kicker","#title"], {{opacity:0, y:20}});
gsap.set("#blocks .block", {{opacity:0, y:24}});
tl.to("#kicker", {{opacity:1, y:0, duration:0.3, ease:"power3.out"}}, 0.15);
tl.to("#title", {{opacity:1, y:0, duration:0.35, ease:"power3.out"}}, 0.3);
tl.to("#blocks .block", {{opacity:1, y:0, duration:0.35, ease:"power2.out", stagger:0.1}}, 0.6);
{f'''gsap.set("#tail", {{opacity:0, y:16}});
tl.to("#tail", {{opacity:1, y:0, duration:0.4, ease:"power2.out"}}, 1.2);''' if tail_html else ""}

window.__timelines["{comp_id}"] = tl;
</script>
</body>
</html>
'''
