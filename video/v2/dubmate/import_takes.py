"""Bring takes recorded in DubMate back into the film. The takes drive the timing: the film is re-laid around them.

  runtime/voice/.venv/Scripts/python video/v2/dubmate/import_takes.py <DubMate "Project files" .zip or folder> [--dry-run]

DubMate's Project files export (audio_processor.build_project_zip) has project_manifest.json -> "lines": per line
the text, character, is_recorded, take_file (Raw_Takes/*.mp3: the take as DubMate renders it, trimmed and levelled
with the actor's chosen sound), offset_ms and stretch (DubMate fits a take to the pack's reference line by up to
+/-8%; 1.0 = as recorded).

For each recorded line (never Barnaby: his voice is ElevenLabs/generated):
  - matched to its film line by character + text (normalised), so the pack's old timing doesn't matter;
  - DubMate's stretch undone (ffmpeg atempo 1/stretch), so the read keeps the actor's own pace;
  - written to video/v2/audio/takes/NN_<Who>.wav (48 kHz mono, 24-bit).
The offset is ignored: the film is re-timed to the takes.

Then re-time everything (in order):
  runtime/voice/.venv/Scripts/python video/audio/voices.py --cues video/v2/cues.json --out video/v2/audio/voice \
      --takes video/v2/audio/takes --only none            # copies takes in, refreshes the manifest
  PYTHONDONTWRITEBYTECODE=1 "X:/Tools/DubMate Studio/resources/python-runtime/python.exe" video/v2/audio/align.py
  runtime/voice/.venv/Scripts/python video/v2/audio/layout.py   # re-lays the film around the real reads
  (voices.py --only none again to refresh the manifest's times), then the sound mix, then the film render.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
CUES = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))
TAKES = V2 / "audio" / "takes"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("’", "'").replace("'", "")).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    film = {(v["who"], norm(v["text"])): n for n, v in enumerate(CUES["voice"], 1)}

    with tempfile.TemporaryDirectory() as td:
        src = Path(a.project)
        if src.suffix.lower() == ".zip":
            with zipfile.ZipFile(src) as z:
                z.extractall(td)
            src = Path(td)
        mans = list(src.rglob("project_manifest.json"))
        if not mans:
            print("no project_manifest.json found: is this DubMate's Project files export?", file=sys.stderr)
            return 1
        root = mans[0].parent
        lines = json.loads(mans[0].read_text(encoding="utf-8")).get("lines", [])
        TAKES.mkdir(parents=True, exist_ok=True)
        done, skipped = [], []
        for e in lines:
            if not e.get("is_recorded") or not e.get("take_file"):
                continue
            who, text = e.get("character", ""), e.get("text", "")
            if who == "Barnaby":
                skipped.append(f"line {e.get('line_number')}: Barnaby stays ElevenLabs/generated")
                continue
            n = film.get((who, norm(text)))
            if n is None:
                skipped.append(f"line {e.get('line_number')} ({who}: {text[:40]!r}): no film line with that text")
                continue
            stretch = float(e.get("stretch", 1.0) or 1.0)
            name = f"{n:02d}_{who}.wav"
            filt = ["-af", f"atempo={1 / stretch:.5f}"] if abs(stretch - 1.0) > 1e-3 else []
            if not a.dry_run:
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(root / e["take_file"]), *filt,
                                "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(TAKES / name)], check=True)
            done.append(f"{name}  {e.get('actor_name', '?')}" + (f"  (DubMate stretch {stretch:.3f} undone)" if filt else ""))

    print(("would write" if a.dry_run else f"wrote to {TAKES}") + f": {len(done)} take(s)")
    for d in done:
        print("  " + d)
    for s in skipped:
        print("  skipped " + s)
    missing = sorted({v["who"] for v in CUES["voice"]} - {"Barnaby"})
    have = {p.stem.split("_", 1)[1] for p in TAKES.glob("*_*.wav")} if TAKES.exists() else set()
    print("characters with takes so far:", sorted(have & set(missing)) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
