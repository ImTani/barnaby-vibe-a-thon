"""Render the film's voice lines from cues.json and check they fit the frozen timing.

  runtime/voice/.venv/Scripts/python video/audio/voices.py [--only Barnaby] [--takes DIR]

Barnaby is always TTS (voice/tts.py: misaki phonemes, George 75% + Fable 25%). Other characters use their
placeholder Kokoro voice from cues.json -> voices, unless a recorded take exists in --takes (e.g. Tani as Martin):
a take named like the output file (e.g. 05_Martin.wav) replaces the generated line.
Writes video/audio/voice/NN_<who>.wav and voice/manifest.json, and prints any line that runs into the next one.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voice.tts import BARNABY, BARNABY_SPEED, save, speak  # noqa: E402

OUT = ROOT / "video" / "audio" / "voice"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--takes", default=str(ROOT / "video" / "audio" / "takes"))
    a = ap.parse_args()
    cues = json.loads((ROOT / "video" / "cues.json").read_text(encoding="utf-8"))
    voices = cues.get("voices", {})
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, lines = [], cues["voice"]
    for i, v in enumerate(lines, 1):
        name = f"{i:02d}_{v['who']}.wav"
        dest = OUT / name
        take = Path(a.takes) / name
        if take.exists():
            shutil.copy(take, dest)
            import soundfile as sf
            dur = sf.info(str(dest)).duration
            src = "take"
        elif a.only and v["who"] != a.only and dest.exists():
            import soundfile as sf
            dur, src = sf.info(str(dest)).duration, "cached"
        else:
            if v["who"] == "Barnaby":
                s, sr = speak(v["text"], BARNABY, BARNABY_SPEED)
            else:
                s, sr = speak(v["text"], voices.get(v["who"], "bm_fable"), 1.0)
            save(dest, s, sr)
            dur, src = len(s) / sr, "tts"
        manifest.append({**v, "file": f"voice/{name}", "dur": round(dur, 2), "src": src})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{'t':>6} {'dur':>5}  who      end    next   text")
    clashes = 0
    for i, m in enumerate(manifest):
        end = m["t"] + m["dur"]
        nxt = manifest[i + 1]["t"] if i + 1 < len(manifest) else cues["duration"]
        flag = "  <-- runs into the next line" if end > nxt - 0.15 else ""
        clashes += bool(flag)
        print(f"{m['t']:6.1f} {m['dur']:5.1f}  {m['who']:8} {end:6.1f} {nxt:6.1f}  {m['text'][:60]}{flag}")
    print(f"\n{len(manifest)} lines, {clashes} clash(es). Manifest: {OUT / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
