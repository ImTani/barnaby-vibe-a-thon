"""Build the look book: one self-contained HTML page with the latest of everything, for review on any device.

  .venv/Scripts/python scripts/dev/build_lookbook.py [--out .demo/lookbook.html] [--width 1400]

Images are re-encoded as JPEG (ffmpeg, already on this machine) and embedded as data URIs, so the page opens
anywhere with no other files. Sections and captions live in SECTIONS below; missing images are listed, not fatal.
"""
from __future__ import annotations

import argparse
import base64
import html
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2 = "video/v2"

# (title, intro, [(path, caption), ...])
SECTIONS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("The shop desk (Blender diorama)",
     "Theo's desk in the back office: Thursday night, Martin's Monday, Priya's Tuesday. Props tell who's at the desk.",
     [(f"{V2}/world/out/01_wide_night.png", "Wide · Thursday 19 Nov, 21:47"),
      (f"{V2}/world/out/02_medium_night.png", "The desk · night"),
      (f"{V2}/world/out/03_keys_night.png", "The key Theo leaves · the one sticky note"),
      (f"{V2}/world/out/04_medium_monday.png", "Monday 23 Nov · Martin's things"),
      (f"{V2}/world/out/05_medium_tuesday.png", "Tuesday 24 Nov · Priya's first day"),
      (f"{V2}/world/out/x_board_night.png", "The corkboard"),
      (f"{V2}/world/out/x_shelf_monday.png", "The shelf · drawer 1, one pair of pads"),
      (f"{V2}/world/out/x_bell.png", "The bell (Barnaby's emblem)")]),
    ("The shop PC (Windows 7 era)",
     "Theo's 2009 machine and his back office, with the shop's real data.",
     [(f"{V2}/look/frames/shop-pc-01-desktop.png", "Monday 08:52 · the desktop"),
      (f"{V2}/look/frames/shop-pc-02-start.png", "The Start menu"),
      (f"{V2}/look/frames/shop-pc-03-tabs.png", "Thursday night · nine tabs"),
      (f"{V2}/look/frames/shop-pc-03b-tabs-parts.png", "Tab five · the parts list"),
      (f"{V2}/look/frames/shop-pc-05-shop-po.png", "Purchase order 3"),
      (f"{V2}/look/frames/shop-pc-06-shop-reports-soon.png", "Reports, as Theo left them"),
      (f"{V2}/look/frames/shop-pc-07-shop-reports.png", "Reports, built by Barnaby (16:16)"),
      (f"{V2}/look/frames/shop-pc-08-shop-jobs-after.png", "Wheel builds moved to Priya")]),
    ("Theo's Lisbon desk",
     "Two monitors, Linux, a tiling setup; the docked laptop runs Quorum. Staged: Quorum and ComfyUI (counts are real scans).",
     [(f"{V2}/world/out/lisbon_01_wide_day.png", "The set · Monday 23 Nov"),
      (f"{V2}/world/out/lisbon_02_medium_day.png", "The desk · day"),
      (f"{V2}/world/out/lisbon_03_medium_night.png", "The desk · Tuesday night"),
      (f"{V2}/look/frames/lisbon-00-sheet-01-rest.png", "Screens · 09:15, at rest"),
      (f"{V2}/look/frames/lisbon-02-realapp-main-1080.png", "Main monitor · 09:39, the real Barnaby app: Point Barnaby at a repo"),
      (f"{V2}/look/frames/lisbon-00-sheet-03-quorum.png", "Screens · 09:41, Quorum: thirteen endpoints, two deadlines in dispute"),
      (f"{V2}/look/frames/lisbon-00-sheet-04-comfy.png", "Screens · 09:43, ComfyUI: twenty-eight endpoints, three jobs queued"),
      (f"{V2}/look/frames/lisbon-00-sheet-05-night.png", "Screens · Tuesday night")]),
    ("The close",
     "Both desks at night: Every system deserves a butler. Even the old ones.",
     [(f"{V2}/world/out/close_two_desks.png", "Two desks")]),
    ("Barnaby's worlds (parked: pick one per person)",
     "Dealt by impeccable's dice from each person's own world. The same butler underneath.",
     [(f"{V2}/look/worlds/frames/theo-hologram.png", "Theo · workshop hologram (dealt, recommended)"),
      (f"{V2}/look/worlds/frames/theo-console.png", "Theo · elbow console"),
      (f"{V2}/look/worlds/frames/theo-multiplane.png", "Theo · multiplane stand"),
      (f"{V2}/look/worlds/frames/martin-manual.png", "Martin · dealer-manual floor plan (dealt, recommended)"),
      (f"{V2}/look/worlds/frames/martin-evac.png", "Martin · evacuation plan"),
      (f"{V2}/look/worlds/frames/martin-album.png", "Martin · sticker album"),
      (f"{V2}/look/worlds/frames/priya-toolroll.png", "Priya · toolroll (dealt, recommended)"),
      (f"{V2}/look/worlds/frames/priya-lacing.png", "Priya · lacing chart"),
      (f"{V2}/look/worlds/frames/same-butler.png", "The Build, through all three")]),
]


def jpeg_data_uri(path: Path, width: int) -> str | None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "x.jpg"
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-vf", f"scale='min({width},iw)':-2",
                            "-q:v", "4", str(out)], capture_output=True)
        if r.returncode != 0 or not out.exists():
            return None
        return "data:image/jpeg;base64," + base64.b64encode(out.read_bytes()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / ".demo" / "lookbook.html"))
    ap.add_argument("--width", type=int, default=1400)
    a = ap.parse_args()
    missing, parts = [], []
    for title, intro, items in SECTIONS:
        figs = []
        for rel, cap in items:
            p = ROOT / rel
            uri = jpeg_data_uri(p, a.width) if p.exists() else None
            if not uri:
                missing.append(rel)
                continue
            figs.append(f'<figure><img src="{uri}" alt="{html.escape(cap)}" loading="lazy"><figcaption>{html.escape(cap)}</figcaption></figure>')
        if figs:
            parts.append(f'<section><h2>{html.escape(title)}</h2><p class="intro">{html.escape(intro)}</p>{"".join(figs)}</section>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Barnaby · look book (gate 2)</title><style>
body{{margin:0;background:#1d1b18;color:#efe9dc;font:16px/1.5 "Segoe UI",system-ui,sans-serif}}
main{{max-width:1440px;margin:0 auto;padding:40px 28px 80px}}
h1{{font:normal 44px/1.1 "Palatino Linotype",Palatino,Georgia,serif;margin:0 0 6px}}
h2{{font:normal 28px/1.2 "Palatino Linotype",Palatino,Georgia,serif;margin:48px 0 6px;padding-top:24px;border-top:1px solid #3a352d}}
.intro{{color:#b8ae9c;margin:0 0 18px}} .lede{{color:#b8ae9c;max-width:70ch}}
figure{{margin:0 0 26px}} img{{width:100%;height:auto;display:block;border-radius:6px;background:#000}}
figcaption{{color:#b8ae9c;font-size:14px;margin-top:6px}}
</style></head><body><main><h1>Barnaby · look book</h1>
<p class="lede">The latest iteration of everything for the film, for one review. Script: <code>docs/script.html</code> (v2.1).</p>
{"".join(parts)}</main></body></html>"""
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    if missing:
        print("missing (not rendered yet):\n  " + "\n  ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
