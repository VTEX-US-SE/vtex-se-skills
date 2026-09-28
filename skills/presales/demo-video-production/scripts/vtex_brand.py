"""Canonical VTEX brand kit for demo-video slides, taken from VTEX's official Design System
(`tokens.css`, brand README and type rules). Every slide generator imports from here — never
hand-write the palette, font or logo again.

Rules this module enforces (brand type rules: "Regular only · never ALL CAPS · never bold titles"):
  - Background: White Ice #F8F7FC, the preferred light background.
  - Font: the real VTEX Trust, embedded as base64 @font-face so HTML renders the same anywhere
    (loaded from the user's machine: the font is proprietary and not in this repo).
  - Titles: font-weight 400 always. Hierarchy comes from size and color, not weight.
  - Labels/kickers: sentence case, no letter-spacing, weight 500 at most, pink for emphasis.
  - Rebel Pink is a small accent (meridian line, one label, one CTA); Serious Black carries text.
  - Logo: the official glyph+wordmark as one monochrome path (fill=currentColor).

Fonts are loaded from the user's local font folder (see FONT_DIRS); they are never committed.
"""
from pathlib import Path

import base64
import os
import sys

_HERE = Path(__file__).parent
_LOGO_PATH = _HERE.parent / "assets" / "vtex-brand" / "logo" / "vtex-logo-mark.svg"

# VTEX Trust is a proprietary font and is NOT in this (public) repo. Each user drops the official
# files (VTEXTrust-Regular/Medium/Italic, .otf or pre-encoded .b64) into one of these folders.
FONT_DIRS = [
    Path(os.environ["VTEX_BRAND_FONTS_DIR"]) if os.environ.get("VTEX_BRAND_FONTS_DIR") else None,
    Path.home() / ".config" / "vtex-se-skills" / "fonts",
    _HERE.parent / "assets" / "vtex-brand" / "fonts",  # git-ignored local copy
]


def _b64(weight: str) -> str | None:
    for d in filter(None, FONT_DIRS):
        b64_file, otf_file = d / f"VTEXTrust-{weight}.b64", d / f"VTEXTrust-{weight}.otf"
        if b64_file.is_file():
            return b64_file.read_text().strip()
        if otf_file.is_file():
            return base64.b64encode(otf_file.read_bytes()).decode()
    return None


def _font_faces() -> str:
    faces = []
    for weight, css_weight, style in (("Regular", 400, "normal"), ("Medium", 500, "normal"),
                                      ("Italic", 400, "italic")):
        data = _b64(weight)
        if data is None:
            print(f"[WARN] VTEX Trust {weight} not found in ~/.config/vtex-se-skills/fonts/ — slides "
                  "fall back to Helvetica. Not brand-compliant; get the font files (see README).",
                  file=sys.stderr)
            continue
        faces.append(f'''  @font-face {{ font-family:"VTEX Trust"; font-weight:{css_weight}; font-style:{style};
    src:url(data:font/otf;base64,{data}) format("opentype"); }}''')
    return "\n".join(faces)


LOGO_SVG_RAW = _LOGO_PATH.read_text().strip()

FONT_FACES = _font_faces()

# Real tokens (project/tokens.css). --gray/--border kept close to but not identical to the
# non-brand names used in v1; these are the real hex values, not renamed placeholders.
TOKENS_CSS = '''
  :root{
    --bg:#F8F7FC;            /* vtex-white-ice — README: preferred light background */
    --bg-white:#FFFFFF;      /* vtex-plain-white — for cards/panels sitting on --bg */
    --pink:#F71963;          /* vtex-rebel-pink */
    --ink:#142032;           /* vtex-serious-black */
    --gray:#4A596B;          /* vtex-mid-gray */
    --border:#E4E6EA;        /* vtex-light-silver */
    --sans:"VTEX Trust","Helvetica Neue",Helvetica,Arial,ui-sans-serif,system-ui,sans-serif;
    --voice:"VTEX Trust","Helvetica Neue",Helvetica,Arial,sans-serif; /* italic, real font — replaces the old unofficial Georgia serif */
  }
'''

def logo_svg(height_css: str = "36px", color_var: str = "var(--pink)") -> str:
    """Real VTEX glyph+wordmark, single-tone (matches the source asset). Caller sets height/color."""
    svg = LOGO_SVG_RAW.replace(
        '<svg viewBox="493 178 467 179" xmlns="http://www.w3.org/2000/svg" aria-label="VTEX">',
        f'<svg class="vtex-mark" viewBox="493 178 467 179" xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="VTEX" style="display:block;height:{height_css};width:auto;color:{color_var}">',
    )
    return svg
