#!/usr/bin/env python3
"""Static slide HTML (Method 1: HTML -> headless Chrome -> PNG -> ffmpeg clip), on the real VTEX
brand kit from vtex_brand.py. Fixed 1920x1080 canvas scaled by JS to whatever window size Chrome
renders at, so the same HTML works at any output resolution.

Use through build_slides.py; import directly only for a custom layout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vtex_brand import FONT_FACES, TOKENS_CSS, logo_svg

BASE_CSS = f'''
  {FONT_FACES}
  {TOKENS_CSS}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{width:100vw;height:100vh;overflow:hidden;background:var(--bg);
    font-family:var(--sans);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}}
  .stage{{width:1920px;height:1080px;position:relative;background:var(--bg);overflow:hidden}}
  .meridian{{position:absolute;top:0;left:150px;width:3px;height:1080px;z-index:2;background:var(--pink)}}
  .brandmark{{position:absolute;top:56px;left:196px;height:36px;z-index:6}}
  .kicker{{font-family:var(--sans);font-size:20px;font-weight:500;
    color:var(--pink);display:flex;align-items:center;gap:14px;margin:0 0 28px}}
  .kicker::before{{content:"";width:32px;height:3px;background:var(--pink);display:inline-block}}
'''

FIT_SCRIPT = '''<script>
  (function(){
    var s=document.querySelector(".stage");
    function fit(){
      var sx=window.innerWidth/1920, sy=window.innerHeight/1080;
      s.style.transform="scale("+sx+","+sy+")";
      s.style.transformOrigin="top left";
    }
    fit(); window.addEventListener("resize",fit);
  })();
  </script>'''


def opening_html(kicker, title, subtitle):
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>{BASE_CSS}
  .content{{position:absolute;left:196px;top:0;width:1240px;height:1080px;
    display:flex;flex-direction:column;justify-content:center}}
  .cover-title{{font-family:var(--sans);font-weight:400;font-size:88px;line-height:1.05;
    letter-spacing:-1px;margin:0;color:var(--ink)}}
  .subtitle{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:32px;line-height:1.35;
    color:var(--gray);max-width:960px;margin:32px 0 0}}
</style></head><body>
  <div class="stage">
    <div class="meridian"></div>
    <div class="brandmark">{logo_svg()}</div>
    <div class="content">
      <p class="kicker">{kicker}</p>
      <h1 class="cover-title">{title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>
  </div>
{FIT_SCRIPT}
</body></html>
'''


def closing_html(kicker, title, recap_line, cta="Ready to see it on your own catalog?",
                 cta_url="dev.vtex.com/en-us/get-started/"):
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>{BASE_CSS}
  .content{{position:absolute;left:196px;top:150px;width:1528px;height:780px}}
  .map-title{{font-family:var(--sans);font-weight:400;font-size:56px;line-height:1.1;
    letter-spacing:-0.5px;margin:0 0 56px;color:var(--ink);max-width:1400px}}
  .recap-row{{border-top:1px solid var(--border);padding-top:40px;margin-bottom:56px}}
  .recap-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:30px;line-height:1.5;
    color:var(--gray);max-width:1200px}}
  .cta-row{{padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:baseline;gap:18px}}
  .cta-line{{font-family:var(--voice);font-style:italic;font-weight:400;font-size:26px;color:var(--gray)}}
  .cta-link{{color:var(--pink);font-style:normal;font-family:var(--sans);font-weight:500;
    border-bottom:2px solid rgba(247,25,99,.35);padding-bottom:4px}}
</style></head><body>
  <div class="stage">
    <div class="meridian"></div>
    <div class="brandmark">{logo_svg()}</div>
    <div class="content">
      <p class="kicker">{kicker}</p>
      <h1 class="map-title">{title}</h1>
      <div class="recap-row"><p class="recap-line">{recap_line}</p></div>
      <div class="cta-row">
        <p class="cta-line">{cta}</p>
        <span class="cta-link">{cta_url}</span>
      </div>
    </div>
  </div>
{FIT_SCRIPT}
</body></html>
'''


def split_capmap_html(kicker, title, col_a_label, col_a_items, col_b_label, col_b_items):
    def col(label, items):
        lis = "".join(f'<p class="item">{it}</p>' for it in items)
        return f'<div class="col"><h3>{label}</h3>{lis}</div>'
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>{BASE_CSS}
  .content{{position:absolute;left:196px;top:150px;width:1528px;height:780px}}
  .map-title{{font-family:var(--sans);font-weight:400;font-size:52px;line-height:1.1;
    letter-spacing:-0.5px;margin:0 0 48px;color:var(--ink);max-width:1400px}}
  .cols{{display:flex;gap:48px;border-top:1px solid var(--border);padding-top:40px}}
  .col{{flex:1;padding:0 8px}}
  .col h3{{font-family:var(--sans);font-weight:500;font-size:30px;color:var(--pink);margin:0 0 22px}}
  .col .item{{font-family:var(--sans);font-weight:400;font-size:20px;line-height:1.5;color:var(--ink);
    padding:14px 0;border-top:1px solid var(--border)}}
  .col .item:first-of-type{{border-top:none}}
</style></head><body>
  <div class="stage">
    <div class="meridian"></div>
    <div class="brandmark">{logo_svg()}</div>
    <div class="content">
      <p class="kicker">{kicker}</p>
      <h1 class="map-title">{title}</h1>
      <div class="cols">
        {col(col_a_label, col_a_items)}
        {col(col_b_label, col_b_items)}
      </div>
    </div>
  </div>
{FIT_SCRIPT}
</body></html>
'''
