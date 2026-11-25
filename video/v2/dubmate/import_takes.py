"""Bring takes recorded in DubMate back into the film, exactly where the actors synced them.

  runtime/voice/.venv/Scripts/python video/v2/dubmate/import_takes.py <DubMate project .zip or its folder> [--dry-run]

DubMate's "Project files" export (audio_processor.build_project_zip) holds project_manifest.json, with one entry per
line: start (s), offset_ms, character, is_recorded, take_file (Raw_Takes/Line_NN_<Character>_<Actor> [..].mp3, the
take as DubMate renders it: trimmed, fitted, levelled, with the actor's chosen sound). DubMate plays a take at
start + offset_ms.

Each recorded line is matched to its film line by start time and character (the pack's clips are named with the film
time, make_pack.py), then written to video/v2/audio/takes/NN_<Who>.wav (48 kHz mono) so that sample 0 is the line's
cue time t in video/v2/cues.json: the film's mix places a voice file at t, so the take lands where DubMate played it.
Barnaby is never imported (he stays generated). Nothing is re-timed: don't re-run layout.py after importing.

Then:  runtime/voice/.venv/Scripts/python video/audio/voices.py --cues video/v2/cues.json \
           --out video/v2/audio/voice --takes video/v2/audio/takes --only none
and re-run the sound mix.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
CUES = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))
TAKES = V2 / "audio" / "takes"
SR = 48000
PRE = 0.03                       # make_pack.py starts each clip this long before the speech onset


def decode(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

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
        man = json.loads(mans[0].read_text(encoding="utf-8"))
        lines = man.get("lines") or man.get("timeline") or []

        # the pack's clip starts (cue onset - PRE), per film line
        film = [(n, v, round(v["t"] + max(0.0, v["speech"][0] - v["t"] - PRE), 3))   # as make_pack.py cuts
                for n, v in enumerate(CUES["voice"], 1)]
        TAKES.mkdir(parents=True, exist_ok=True)
        done, skipped = [], []
        for e in lines:
            if not e.get("is_recorded") or not e.get("take_file"):
                continue
            who = e.get("character", "")
            if who == "Barnaby":
                skipped.append(f"line {e.get('line_number')}: Barnaby stays generated")
                continue
            start = float(e["start"])
            match = [(n, v) for n, v, s in film if v["who"] == who and abs(s - start) < 0.06]
            if len(match) != 1:
                skipped.append(f"line {e.get('line_number')} ({who} at {start:.3f} s): no unique film line")
                continue
            n, v = match[0]
            x = decode(root / e["take_file"])
            at = start + float(e.get("offset_ms", 0)) / 1000.0          # where DubMate plays it (film time)
            lead = at - float(v["t"])                                   # seconds after the cue's file start
            if lead >= 0:
                x = np.concatenate([np.zeros(int(round(lead * SR)), np.float32), x])
            else:
                x = x[int(round(-lead * SR)):]
            name = f"{n:02d}_{who}.wav"
            if not a.dry_run:
                sf.write(str(TAKES / name), x, SR, subtype="PCM_24")
            done.append(f"{name}  {e.get('actor_name', '?')}  offset {int(e.get('offset_ms', 0)):+d} ms  "
                        f"stretch {float(e.get('stretch', 1.0)):.2f}  {len(x) / SR:.2f} s")

    print(("would write" if a.dry_run else f"wrote to {TAKES}") + f": {len(done)} take(s)")
    for d in done:
        print("  " + d)
    for s in skipped:
        print("  skipped " + s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
