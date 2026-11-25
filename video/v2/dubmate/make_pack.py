"""Build a DubMate scene pack of the film, so friends can voice Martin, Theo and Priya against the picture.

  runtime/voice/.venv/Scripts/python video/v2/dubmate/make_pack.py [--video FILE] [--out DIR] [--install DIR]

DubMate standard format (see DubMate's README, "Scene Packs Guide", and pack_loader.load_pack):
  dub_video.mp4        the film, silent (default: the animatic at the locked timing; later the final film)
  _backing_track.wav   music + sound effects, no voices (from video/v2/audio/{music,sfx}.wav, only if they are
                       the film's length; otherwise left out and the pack still works)
  NN_Who_S-mmm.wav     one reference clip per line: the generated voice, cut to its speech, named with the film
                       time (s.mmm) where the clip starts. All 54 lines; Barnaby's 23 stay generated (nobody casts
                       him), so he plays and shows as captions while friends record.
  _captions.json       clip -> "[Character] line"
  _TIMESTAMPS.txt      the same, human-readable
  pack.json            title, subtitle, cover
  cover.png            the two-desk close
  README.txt           casting notes

Times come from video/v2/cues.json (the locked clock); clips from video/v2/audio/voice/manifest.json.
Writes the folder to --out (default .demo/dubmate/Barnaby), a zip beside it for DubMate's Import .ZIP, and copies the
folder into --install (default X:/DevProjects/Dubmate/Packs, gitignored there) if that folder exists.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = V2.parents[1]
AUDIO = V2 / "audio"
CUES = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((AUDIO / "voice" / "manifest.json").read_text(encoding="utf-8"))

PRE, POST = 0.03, 0.15          # seconds kept before the speech onset and after the speech end
SUBTITLE = "Every system deserves a butler. Cast Martin, Theo and Priya; Barnaby stays generated."
README = """Barnaby: a DubMate pack of the short film (3:38)

Cast: Martin (18 lines), Theo (10), Priya (3).
Barnaby (23 lines) is the AI butler and stays generated: please leave him uncast,
so his lines play in his own voice while you record.

Characters, delivery notes and target lengths: see the voice-acting pack the film's
director shared with you. The film's timing is locked, so stay close to the original
line's length; DubMate lines each take up with it.

When the cast is done, export the room's Project files (.zip) and send it back.
"""


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def clip_name(n: int, who: str, start: float) -> str:
    ms = int(round(start * 1000))
    return f"{n:02d}_{who}_{ms // 1000}-{ms % 1000:03d}.wav"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=str(V2 / "animatic" / "out" / "animatic-silent.mp4"))
    ap.add_argument("--out", default=str(ROOT / ".demo" / "dubmate" / "Barnaby"))
    ap.add_argument("--install", default=r"X:\DevProjects\Dubmate\Packs")
    ap.add_argument("--cover", default=str(V2 / "world" / "out" / "close_two_desks.png"))
    a = ap.parse_args()

    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    dur = float(CUES["duration"])

    # the picture, silent (DubMate plays the backing and the lines over it)
    ffmpeg("-i", a.video, "-an", "-c:v", "copy", "-movflags", "+faststart", str(out / "dub_video.mp4"))
    vdur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(out / "dub_video.mp4")], capture_output=True, text=True).stdout.strip())
    if abs(vdur - dur) > 0.5:
        print(f"WARNING: video is {vdur:.2f} s, the locked film is {dur:.2f} s: wrong cut?", file=sys.stderr)

    # music + effects, only if they are this cut's length
    music, sfx = AUDIO / "music.wav", AUDIO / "sfx.wav"
    backing = None
    if music.exists() and sfx.exists():
        m, sr = sf.read(str(music), dtype="float32", always_2d=True)
        s, sr2 = sf.read(str(sfx), dtype="float32", always_2d=True)
        if sr == sr2 and abs(len(m) / sr - dur) < 0.25 and abs(len(s) / sr - dur) < 0.25:
            n = min(len(m), len(s))
            mix = m[:n] + s[:n]
            peak = float(np.abs(mix).max()) or 1.0
            mix *= min(1.0, 0.89 / peak)
            sf.write(str(out / "_backing_track.wav"), mix, sr, subtype="PCM_16")
            backing = f"{len(mix) / sr:.2f} s at {sr} Hz"
    print("backing:", backing or "left out (music/sfx stems are not this cut's length yet)")

    # one clip per line, cut to its speech, named with its film time
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for n, (v, mm) in enumerate(zip(CUES["voice"], MANIFEST), 1):
            assert v["text"] == mm["text"], f"manifest out of date at line {n}"
            x, sr = sf.read(str(AUDIO / mm["file"]), dtype="float32", always_2d=True)
            x = x.mean(1)
            t, (on, off) = float(v["t"]), v["speech"]
            a0 = max(0.0, on - t - PRE)
            a1 = min(len(x) / sr, off - t + POST)
            seg = x[int(a0 * sr):int(a1 * sr)]
            start = t + a0
            name = clip_name(n, v["who"], start)
            tmp = Path(td) / name
            sf.write(str(tmp), seg, sr, subtype="FLOAT")
            ffmpeg("-i", str(tmp), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out / name))
            rows.append({"n": n, "filename": name, "start": round(start, 3), "character": v["who"],
                         "caption": v["text"], "len": round(len(seg) / sr, 2)})

    caps = {r["filename"]: f"[{r['character']}] {r['caption']}" for r in rows}
    (out / "_captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=2), encoding="utf-8")
    ts = ["# Barnaby (3:38)", "# Cast Martin, Theo and Priya; Barnaby stays generated.",
          "# File | start time (s) | subtitle\n"]
    ts += [f"{r['filename']:<40} {r['start']:>10.3f}s   | [{r['character']}] {r['caption']}" for r in rows]
    (out / "_TIMESTAMPS.txt").write_text("\n".join(ts) + "\n", encoding="utf-8")

    if Path(a.cover).exists():
        ffmpeg("-i", a.cover, "-vf", "scale=1280:-2", str(out / "cover.png"))
    (out / "pack.json").write_text(json.dumps({"title": "Barnaby", "subtitle": SUBTITLE, "icon": "cover.png"},
                                              ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "README.txt").write_text(README, encoding="utf-8")

    # a zip for DubMate's Import .ZIP (the pack folder at its root)
    zpath = out.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.iterdir()):
            z.write(f, f"Barnaby/{f.name}",
                    compress_type=zipfile.ZIP_STORED if f.suffix in (".mp4", ".png") else zipfile.ZIP_DEFLATED)

    inst = Path(a.install) if a.install else None          # --install "" skips the copy
    if inst and inst.is_dir():
        dest = inst / "Barnaby"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(out, dest)
        print("installed:", dest)

    who = {}
    for r in rows:
        who[r["character"]] = who.get(r["character"], 0) + 1
    print(f"wrote {out} ({len(rows)} lines: {who}); zip {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
