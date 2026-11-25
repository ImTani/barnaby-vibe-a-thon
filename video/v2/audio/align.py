"""Word timings for every voice line (generated or a recorded take), so the film's marks can sit on the words.

  runtime/voice/.venv/Scripts/python video/v2/audio/align.py [--model small.en] [--only Martin]

Transcribes each file in video/v2/audio/voice/manifest.json with faster-whisper (word timestamps), matches the
recognised words to the script's words for that line (difflib, normalised), and writes
video/v2/audio/voice/words.json:  { "NN": [[word, start_s, end_s], ...] }  times relative to the file's start.
Script words that weren't recognised get times interpolated from their neighbours (flagged "~").

layout.py reads words.json through Timeline.word(n, "five") (falls back to its own offsets when a line has no
timings), so a click lands on "five" and the tab-five page appears with it, whoever reads the line.

Backends (no downloads): OpenAI Whisper from DubMate Studio's own runtime and its cached model (~/.cache/whisper/
base.pt), the default on this machine:
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="X:/Tools/DubMate Studio/ai-packages"       "X:/Tools/DubMate Studio/resources/python-runtime/python.exe" video/v2/audio/align.py
or faster-whisper (runtime/voice/.venv) with a model in models/hf: --backend faster --model small.en.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VOICE = HERE / "voice"
MODELS = ROOT / "models" / "hf"


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def script_words(text: str) -> list[str]:
    return [w for w in (norm(t) for t in re.split(r"[\s—–-]+", text)) if w]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openai", choices=["openai", "faster"])
    ap.add_argument("--model", default="base")
    ap.add_argument("--site", default="X:/Tools/DubMate Studio/ai-packages", help="where OpenAI Whisper is installed")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    man = json.loads((VOICE / "manifest.json").read_text(encoding="utf-8"))
    out_path = VOICE / "words.json"
    words = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    if a.backend == "openai":
        if a.site and a.site not in sys.path:
            sys.path.insert(0, a.site)
        import whisper  # DubMate Studio's ai-packages; loads ~/.cache/whisper/<model>.pt, no download
        cache = Path.home() / ".cache" / "whisper" / f"{a.model}.pt"
        if not cache.exists():
            print(f"no cached model {cache}", file=sys.stderr)
            return 2
        omodel = whisper.load_model(a.model)

        def recognise(path, prompt):
            r = omodel.transcribe(str(path), language="en", word_timestamps=True, initial_prompt=prompt, fp16=False)
            return [(norm(w["word"]), w["start"], w["end"]) for s in r["segments"] for w in s.get("words", [])
                    if norm(w["word"])]
    else:
        from faster_whisper import WhisperModel  # runtime/voice/.venv
        model_dir = MODELS / f"faster-whisper-{a.model}"
        if not (model_dir / "model.bin").exists():
            print(f"no model at {model_dir}", file=sys.stderr)
            return 2
        fmodel = WhisperModel(str(model_dir), device="cpu", compute_type="int8")

        def recognise(path, prompt):
            segs, _ = fmodel.transcribe(str(path), language="en", word_timestamps=True, beam_size=5,
                                        initial_prompt=prompt, vad_filter=False)
            return [(norm(w.word), w.start, w.end) for s in segs for w in (s.words or []) if norm(w.word)]

    for i, m in enumerate(man, 1):
        if a.only and m["who"] != a.only:
            continue
        path = HERE / m["file"]
        want = script_words(m["text"])
        got = recognise(path, m["text"])
        sm = difflib.SequenceMatcher(a=want, b=[g[0] for g in got], autojunk=False)
        times: list = [None] * len(want)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = (got[blk.b + k][1], got[blk.b + k][2])
        # fill gaps by interpolation between known neighbours
        known = [k for k, t in enumerate(times) if t]
        row = []
        for k, w in enumerate(want):
            if times[k]:
                row.append([w, round(times[k][0], 3), round(times[k][1], 3)])
                continue
            lo = max((j for j in known if j < k), default=None)
            hi = min((j for j in known if j > k), default=None)
            t0 = times[lo][1] if lo is not None else (got[0][1] if got else 0.0)
            t1 = times[hi][0] if hi is not None else (got[-1][2] if got else t0 + 0.3)
            n_gap = (hi if hi is not None else len(want)) - (lo if lo is not None else -1) - 1
            pos = k - (lo if lo is not None else -1) - 1
            s = t0 + (t1 - t0) * pos / max(n_gap, 1)
            row.append([w + "~", round(s, 3), round(s + (t1 - t0) / max(n_gap, 1), 3)])
        words[f"{i:02d}"] = row
        miss = sum(1 for r in row if r[0].endswith("~"))
        print(f"{i:02d} {m['who']:8} {len(want):2d} words, {miss} interpolated  | {m['text'][:60]}")
    out_path.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
