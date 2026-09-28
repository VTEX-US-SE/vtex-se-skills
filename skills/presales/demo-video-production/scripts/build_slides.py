#!/usr/bin/env python3
"""
Build on-brand VTEX slides for a demo video from a JSON spec (see templates/slides.example.json).

Usage:
    python3 build_slides.py <spec.json> --out <video-folder>/slides --render             # static PNG
    python3 build_slides.py <spec.json> --out <video-folder>/hyperframes-project          # Hyperframes

The spec's "mode" picks the method:
    "png"          writes <id>.html and, with --render, <id>.png via headless Chrome at --size.
    "hyperframes"  writes <id>.html compositions sized to each slide's duration, then prints the
                   render + time_base-normalize commands to run (render needs Node 22+ and a
                   one-time `npx --yes hyperframes browser ensure`).

Slide types and fields:
    opening   kicker, title, subtitle
    split     kicker, title, columns: [{label, items: [...]}, {label, items: [...]}]
    grid      kicker, title, blocks: [[num, heading, body], ...], optional cta: {line, url}
              or proof_line (hyperframes only)
    closing   kicker, title, recap, optional cta, cta_url

Duration (hyperframes only): "duration" in seconds, or "audio": a narration file path relative to
the spec file; the script ffprobes it. Always size a slide to its real narration, never a guess.
"""
import argparse
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slides_hyperframes as hf  # noqa: E402
import slides_png as png  # noqa: E402

MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def find_chrome() -> str:
    for candidate in (os.environ.get("CHROME_BIN"), MAC_CHROME,
                      shutil.which("google-chrome"), shutil.which("chromium")):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("Chrome not found. Install Google Chrome or set CHROME_BIN.")


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def slide_duration(slide: dict, base: Path) -> float:
    if "duration" in slide:
        return float(slide["duration"])
    if "audio" in slide:
        return ffprobe_duration(base / slide["audio"])
    sys.exit(f"slide {slide['id']}: hyperframes mode needs 'duration' or 'audio'")


def png_html(slide: dict) -> str:
    t = slide["type"]
    if t == "opening":
        return png.opening_html(slide["kicker"], slide["title"], slide["subtitle"])
    if t == "split":
        a, b = slide["columns"]
        return png.split_capmap_html(slide["kicker"], slide["title"], a["label"], a["items"],
                                     b["label"], b["items"])
    if t == "closing":
        return png.closing_html(slide["kicker"], slide["title"], slide["recap"],
                                cta=slide.get("cta", "Ready to see it on your own catalog?"),
                                cta_url=slide.get("cta_url", "dev.vtex.com/en-us/get-started/"))
    sys.exit(f"slide {slide['id']}: type '{t}' is not available in png mode "
             "(grid is hyperframes only)")


def hf_html(slide: dict, duration: float) -> str:
    t, cid = slide["type"], slide["id"]
    d = f"{duration:.6f}"
    if t == "opening":
        return hf.opening_composition(cid, d, slide["kicker"], slide["title"], slide["subtitle"])
    if t == "split":
        a, b = slide["columns"]
        return hf.split_capmap_composition(cid, d, slide["kicker"], slide["title"], a["label"],
                                           a["items"], b["label"], b["items"])
    if t == "grid":
        cta = slide.get("cta")
        return hf.block_grid_composition(cid, d, slide["kicker"], slide["title"],
                                         [tuple(b) for b in slide["blocks"]],
                                         cta=(cta["line"], cta["url"]) if cta else None,
                                         proof_line=slide.get("proof_line"))
    if t == "closing":
        return hf.closing_composition(cid, d, slide["kicker"], slide["title"], slide["recap"],
                                      cta=slide.get("cta", "Ready to see it on your own catalog?"),
                                      cta_url=slide.get("cta_url", "dev.vtex.com/en-us/get-started/"))
    sys.exit(f"slide {cid}: unknown type '{t}'")


def render_pngs(out_dir: Path, ids: list[str], size: str) -> None:
    """Headless Chrome over a temporary local HTTP server (file:// is unreliable for this)."""
    chrome = find_chrome()
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = partial(QuietHandler, directory=str(out_dir))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        for sid in ids:
            target = out_dir / f"{sid}.png"
            subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={target}", f"--window-size={size.replace('x', ',')}",
                            f"http://127.0.0.1:{port}/{sid}.html"],
                           check=True, capture_output=True)
            print(f"  rendered {target}")
        httpd.shutdown()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="slides JSON spec")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--render", action="store_true", help="png mode: also render PNGs")
    ap.add_argument("--size", default="1920x1080", help="png render size, e.g. 1280x720 (default 1920x1080)")
    args = ap.parse_args()

    spec_path = Path(args.spec).expanduser().resolve()
    spec = json.loads(spec_path.read_text())
    mode = spec.get("mode", "png")
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = []
    for slide in spec["slides"]:
        sid = slide["id"]
        if mode == "png":
            html = png_html(slide)
        elif mode == "hyperframes":
            dur = slide_duration(slide, spec_path.parent)
            html = hf_html(slide, dur)
            print(f"  {sid}: {dur:.3f}s")
        else:
            sys.exit(f"unknown mode '{mode}' (png | hyperframes)")
        (out_dir / f"{sid}.html").write_text(html, encoding="utf-8")
        ids.append(sid)
    print(f"Wrote {len(ids)} slide(s) to {out_dir}")

    if mode == "png" and args.render:
        render_pngs(out_dir, ids, args.size)
    elif mode == "hyperframes":
        print("\nNext, from inside that folder (it should be a project made with `npx --yes hyperframes init`):")
        print("  export HYPERFRAMES_NO_TELEMETRY=1")
        for sid in ids:
            print(f"  npx --yes hyperframes render -c {sid}.html --output renders/{sid}.mp4 && "
                  f"ffmpeg -y -i renders/{sid}.mp4 -c copy -video_track_timescale 90000 renders/{sid}_norm.mp4")


if __name__ == "__main__":
    main()
