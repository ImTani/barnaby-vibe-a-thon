"""Put Barnaby's ElevenLabs v4 lines into the film: the newest passage take of each line, paced, with word timings.

  runtime/voice/.venv/Scripts/python video/v2/audio/adopt_v4.py

Source per line: .demo/review/eleven/v4/NN_s<seed>.wav from the most recent re-render (the seeds in PREFER, newest
first), else NN.wav (the first pass). The cut lines come from eleven.py passages (one request per scene).
Pace (the director: brisk, never rushed): a line of 4+ words under 175 wpm is brought toward 180 (at most +10%);
over 200 wpm, eased toward 190 (at most -8%); pitch-preserving (ffmpeg atempo). Word timings come from the
ElevenLabs character alignment (tags dropped), scaled by the same factor -> voice/words.json (src "eleven_v4").
Writes video/v2/audio/takes/NN_Barnaby.wav; then voices.py --takes and layout.py re-time the film.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V4DIR = ROOT / ".demo" / "review" / "eleven" / "v4"
TAKES = HERE / "takes"
WORDS = HERE / "voice" / "words.json"
PREFER = ("_s6606", "_s5505", "_s4404", "")                     # newest re-render first
SPLIT = re.compile(r"[\s—–-]+")


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def span(x: np.ndarray, sr: int) -> float:
    hop = int(.01 * sr)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    on = np.where(20 * np.log10(rms / (rms.max() + 1e-12)) > -40)[0]
    return (on[-1] - on[0] + 1) * hop / sr if len(on) else 0.0


def word_times(al: dict) -> list:
    out, cur, t0, t1, tag = [], "", None, None, False
    for c, a, b in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if c == "[":
            tag = True
        if tag:
            if c == "]":
                tag = False
            continue
        if SPLIT.match(c):
            if norm(cur):
                out.append([norm(cur), round(t0, 3), round(t1, 3)])
            cur, t0 = "", None
            continue
        cur += c
        t0 = a if t0 is None else t0
        t1 = b
    if norm(cur):
        out.append([norm(cur), round(t0, 3), round(t1, 3)])
    return out


def main() -> None:
    cues = json.loads((HERE.parent / "cues.json").read_text(encoding="utf-8"))
    v4 = json.loads((HERE / "barnaby_v4.json").read_text(encoding="utf-8"))
    words = json.loads(WORDS.read_text(encoding="utf-8")) if WORDS.exists() else {}
    TAKES.mkdir(parents=True, exist_ok=True)
    for k in [x for x in v4 if not x.startswith("_")]:
        src = next(V4DIR / f"{k}{p}.wav" for p in PREFER if (V4DIR / f"{k}{p}.wav").exists())
        x, sr = sf.read(str(src), dtype="float32")
        x = x if x.ndim == 1 else x.mean(1)
        n = len([w for w in (norm(t) for t in SPLIT.split(cues["voice"][int(k) - 1]["text"])) if w])
        wpm = n / span(x, sr) * 60
        tempo = 1.0
        if n >= 4 and wpm < 175:
            tempo = min(1.10, 180 / wpm)
        elif n >= 4 and wpm > 200:
            tempo = max(0.92, 190 / wpm)
        af = ["-af", f"atempo={tempo:.4f}"] if abs(tempo - 1) > 1e-3 else []
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), *af, "-ar", "48000", "-ac", "1",
                        "-c:a", "pcm_s24le", str(TAKES / f"{k}_Barnaby.wav")], check=True)
        al = json.loads(src.with_suffix(".align.json").read_text(encoding="utf-8"))
        words[k] = [[w, round(a / tempo, 3), round(b / tempo, 3)] for w, a, b in word_times(al)] + \
                   [["_src", "eleven_v4", round(tempo, 4)]]
        print(f"{k} {src.stem:10} {wpm:4.0f} wpm x{tempo:.3f} -> {wpm * tempo:4.0f}")
    WORDS.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
