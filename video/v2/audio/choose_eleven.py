"""Keep the better of each line's two ElevenLabs takes, and record Barnaby's word timings from ElevenLabs' alignment.

  PYTHONDONTWRITEBYTECODE=1 "X:/Tools/DubMate Studio/resources/python-runtime/python.exe" video/v2/audio/choose_eleven.py

For every .demo/review/eleven/takes/NN_s<seed>.wav: Whisper (base, CPU, from DubMate Studio's runtime; NO script as a
prompt, so it can't paper over a misread) transcribes it, then:
  score = 10 x word error rate vs the cue text  + 10 x (audio-tag words spoken aloud)  + |pace - 185 wpm| / 185
The lower score wins -> video/v2/audio/takes/NN_Barnaby.wav (voices.py --takes copies it in). Its ElevenLabs character
alignment (tags dropped) becomes that line's word timings in video/v2/audio/voice/words.json (src "eleven").
Writes .demo/review/eleven/choice.md (both takes per line: transcript, errors, pace, the pick).
"""
from __future__ import annotations

import difflib
import json
import re
import shutil
import sys
import wave
from pathlib import Path

sys.path.insert(0, "X:/Tools/DubMate Studio/ai-packages")
import numpy as np  # noqa: E402
import whisper  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CUES = json.loads((HERE.parent / "cues.json").read_text(encoding="utf-8"))
TAGGED = json.loads((HERE / "barnaby_v3.json").read_text(encoding="utf-8"))
CAND = ROOT / ".demo" / "review" / "eleven" / "takes"
TAKES = HERE / "takes"
WORDS = HERE / "voice" / "words.json"
TARGET = 185.0
SPLIT = re.compile(r"[\s—–-]+")


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def words_of(text: str) -> list[str]:
    return [w for w in (norm(t) for t in SPLIT.split(text)) if w]


def number_words(ws: list[str]) -> list[str]:
    """Whisper writes numbers as digits; the script spells them. Compare in words."""
    out = []
    table = {"23": ["twenty", "three"], "31": ["thirty", "one"], "13": ["thirteen"], "28": ["twenty", "eight"],
             "10": ["ten"], "6": ["six"], "650": ["six", "fifty"], "2": ["two"], "4": ["four"], "3": ["three"],
             "5": ["five"], "20": ["twenty"], "1": ["one"]}
    for w in ws:
        out.extend(table.get(w.strip("£$"), [w]))
    return out


def load_wav(p: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(p)) as w:
        sr, n, sw = w.getframerate(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        x = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        x = np.where(x >= 1 << 23, x - (1 << 24), x).astype(np.float32) / (1 << 23)
    else:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def active_span(x: np.ndarray, sr: int) -> float:
    hop = int(0.01 * sr)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-12))
    on = np.where(db > -40)[0]
    return (on[-1] - on[0] + 1) * hop / sr if len(on) else 0.0


def word_times(align: dict, tagged: str) -> list:
    """ElevenLabs character alignment -> [[word, start, end], ...] for the spoken words (tags in [] dropped)."""
    chars, st, en = align["characters"], align["character_start_times_seconds"], align["character_end_times_seconds"]
    out, cur, t0, t1, in_tag = [], "", None, None, False
    for c, a, b in zip(chars, st, en):
        if c == "[":
            in_tag = True
        if in_tag:
            if c == "]":
                in_tag = False
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


def main() -> int:
    model = whisper.load_model("base")
    words = json.loads(WORDS.read_text(encoding="utf-8")) if WORDS.exists() else {}
    TAKES.mkdir(parents=True, exist_ok=True)
    report = ["# Barnaby on ElevenLabs: the takes and the pick\n", "| # | take | transcript | WER | tags spoken | wpm | pick |",
              "|---|---|---|---|---|---|---|"]
    for k in sorted(x for x in TAGGED if not x.startswith("_")):
        cue = CUES["voice"][int(k) - 1]
        want = words_of(cue["text"])
        tags = {norm(t) for t in re.findall(r"\[([^\]]+)\]", TAGGED[k]) for t in t.split()}
        scored = []
        for f in sorted(CAND.glob(f"{k}_s*.wav")):
            got = number_words(words_of(model.transcribe(str(f), language="en", fp16=False)["text"]))
            sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
            wer = 1 - sm.ratio()
            leak = sum(1 for w in got if w in tags and w not in want)
            x, sr = load_wav(f)
            span = active_span(x, sr)
            wpm = len(want) / span * 60 if span else 0
            score = 10 * wer + 10 * leak + abs(wpm - TARGET) / TARGET
            scored.append((score, f, " ".join(got), wer, leak, wpm))
        if not scored:
            print(k, "no takes")
            continue
        scored.sort(key=lambda s: s[0])
        best = scored[0]
        shutil.copy(best[1], TAKES / f"{k}_Barnaby.wav")
        al = best[1].with_suffix(".align.json")
        if al.exists():
            words[k] = word_times(json.loads(al.read_text(encoding="utf-8")), TAGGED[k]) + [["_src", "eleven", 0]]
        for s in scored:
            report.append(f"| {k} | {s[1].stem.split('_')[1]} | {s[2][:70]} | {s[3]:.2f} | {s[4]} | {s[5]:.0f} | "
                          f"{'**yes**' if s is best else ''} |")
        print(f"{k} pick {best[1].stem}  wer {best[3]:.2f} leak {best[4]} wpm {best[5]:.0f}"
              + ("   <- CHECK" if best[3] > 0.15 or best[4] else ""))
    WORDS.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (CAND.parent / "choice.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("wrote", TAKES, "and", CAND.parent / "choice.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
