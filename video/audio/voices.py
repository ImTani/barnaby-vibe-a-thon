"""Render the film's voice lines from cues.json at a measured pace, and check they fit the frozen timing.

  runtime/voice/.venv/Scripts/python video/audio/voices.py [--only Barnaby] [--takes DIR]
        [--cues FILE] [--out DIR] [--compare DIR]

Barnaby is always TTS (voice/tts.py: misaki phonemes, George 75% + Fable 25%). Other characters use their
placeholder Kokoro voice from cues.json -> voices, unless a recorded take exists in --takes (e.g. Tani as Martin):
a take named like the output file (e.g. 05_Martin.wav) replaces the generated line (measured, never re-timed).

Pace (video/v2/SPEECH.md): every line has a target speaking rate in words per minute, measured over the speech
(leading and trailing silence excluded, pauses inside the line included, "twenty-three" = two words). A cue line
sets it with "wpm"; otherwise it is the character's default x the cue's "pace" (situation) x the short-line factor.
Kokoro's speed for the line is found by measure-and-correct: render, measure, rescale the part of the duration
that scales with speed, until the rate is within 2% (5% is accepted).

Writes <out>/NN_<who>.wav, <out>/manifest.json and <out>/report.md (old vs new rate when --compare has the old
files), prints the measured rate per line, and any line that runs into the next one.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video" / "v2"))

from speech_probe import load, rate, words  # noqa: E402
from voice.tts import BARNABY, BARNABY_SPEED, plan, save, synthesise, syllables  # noqa: E402

OUT = ROOT / "video" / "audio" / "voice"

# SPEECH.md, "Pace table": defaults in wpm for a neutral line of five or more words of average length.
PACE = {"Barnaby": 170, "Theo": 195, "Martin": 180, "Priya": 190}
# SPEECH.md, "Situation": multipliers a cue line can ask for with "pace".
SITUATION = {"neutral": 1.00, "brisk": 1.06, "surprised": 1.08, "tired": 0.92, "wistful": 0.92, "dry": 0.95,
             "explain": 0.95, "closing": 0.90}
REF_SPW = 1.3          # syllables per word of the film's lines (all v1.1 cues + v2 script: 1.28)
REF_WPM = 170          # pauses keep their planned length at this pace, shrink when faster, grow when slower
TOL, ACCEPT = 0.02, 0.05
SPEED_RANGE = (0.6, 1.8)


def short_line(words: int) -> float:
    """Short turns are spoken slower per word (final lengthening; Yuan et al. 2006): 1 word x0.68 ... 5+ words x1."""
    return min(1.0, 0.60 + 0.08 * words)


def density(text: str) -> float:
    """Long words take longer to say, but not in proportion (unstressed syllables are short): a line of
    two-syllable words gets ~0.8x the word rate of an average line, a line of monosyllables ~1.1x."""
    spw = syllables(" ".join(p for p, _, _ in plan(text, 1.0))) / max(words(text), 1)
    return min(1.2, max(0.8, (REF_SPW / spw) ** 0.5))


def target_wpm(line: dict) -> float:
    if "wpm" in line:
        return float(line["wpm"])
    base = PACE.get(line["who"], 180) * SITUATION[line.get("pace", "neutral")]
    return base * short_line(words(line["text"])) * density(line["text"])


def fit(text: str, voice, target: float, speed: float, pause_scale: float = 1.0) -> tuple:
    """Pick Kokoro's speed so the line's measured rate hits the target. Returns (speech, measured, speed, tries).
    Rate is not quite monotonic in speed (Kokoro rounds durations, a comma pause can come and go), so once a try
    lands on each side of the target the next speed is interpolated between the closest two."""
    best, tries = None, []
    for _ in range(7):
        sp = synthesise(text, voice, speed, pause_scale=pause_scale)
        m = rate(sp.audio, sp.sr, text)
        err = m["wpm"] / target - 1
        tries.append((round(speed, 3), round(m["wpm"])))
        if best is None or abs(err) < abs(best[1]["wpm"] / target - 1):
            best = (sp, m, speed)
        if abs(err) <= TOL:
            break
        lo = max(((s, w) for s, w in tries if w < target), default=None, key=lambda t: t[1])
        hi = min(((s, w) for s, w in tries if w > target), default=None, key=lambda t: t[1])
        if lo and hi and lo[0] < hi[0]:
            new = lo[0] + (hi[0] - lo[0]) * (target - lo[1]) / (hi[1] - lo[1])
        else:
            # Inserted pauses are fixed; the rest of the active span scales as 1/speed.
            scaling = m["active"] - sp.inserted
            wanted = m["words"] * 60 / target - sp.inserted
            new = speed * scaling / max(wanted, 0.25 * scaling)
        new = round(min(SPEED_RANGE[1], max(SPEED_RANGE[0], new)), 3)
        if any(abs(new - s) < 2e-3 for s, _ in tries):
            break                                   # nothing new to try (pinned, or the bracket has closed)
        speed = new
    return (*best, tries)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--takes", default=str(ROOT / "video" / "audio" / "takes"))
    ap.add_argument("--cues", default=str(ROOT / "video" / "cues.json"))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--compare", default="", help="folder with the previous NN_<who>.wav, for the old-vs-new report")
    a = ap.parse_args()
    out = Path(a.out)
    cues = json.loads(Path(a.cues).read_text(encoding="utf-8"))
    voices = cues.get("voices", {})
    out.mkdir(parents=True, exist_ok=True)
    manifest, lines = [], cues["voice"]
    print(f"{'#':>2} {'who':8} {'target':>6} {'wpm':>5} {'err':>5} {'speed':>5} {'syl/s':>5} {'artic':>5} {'dur':>5}  text")
    for i, v in enumerate(lines, 1):
        name = f"{i:02d}_{v['who']}.wav"
        dest = out / name
        take = Path(a.takes) / name
        target, spd = None, None
        if take.exists():
            shutil.copy(take, dest)
            src = "take"
        elif a.only and v["who"] != a.only and dest.exists():
            src = "cached"
        else:
            voice = BARNABY if v["who"] == "Barnaby" else voices.get(v["who"], "bm_fable")
            start = BARNABY_SPEED if v["who"] == "Barnaby" else 1.0
            target = target_wpm(v)
            # faster speakers pause less (Murray & Arnott 1993): pauses scale with the character's pace, not the line's
            pace = float(v["wpm"]) if "wpm" in v else PACE.get(v["who"], 180) * SITUATION[v.get("pace", "neutral")]
            sp, _, spd, _ = fit(v["text"], voice, target, start, min(1.2, max(0.8, REF_WPM / pace)))
            save(dest, sp.audio, sp.sr)
            src = "tts"
        x, sr = load(dest)
        m = rate(x, sr, v["text"])
        dur = len(x) / sr
        entry = {**v, "file": f"voice/{name}", "dur": round(dur, 2), "src": src, "wpm": round(m["wpm"]),
                 "sps": round(m["sps"], 2)}
        if target:
            entry.update(target_wpm=round(target), speed=round(spd, 3))
        manifest.append(entry)
        miss = ""
        if target and abs(m["wpm"] / target - 1) > ACCEPT:
            miss = "  <-- outside +-5%" + (" (speed limit)" if spd in SPEED_RANGE else "")
            entry["off_target"] = True
        err = f"{(m['wpm'] / target - 1) * 100:+4.0f}%" if target else "   - "
        print(f"{i:2d} {v['who']:8} {target or 0:6.0f} {m['wpm']:5.0f} {err:>5} {spd or 0:5.2f} {m['sps']:5.2f} "
              f"{m['artic_sps']:5.2f} {dur:5.2f}  {v['text'][:56]}{miss}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    print(f"\n{'t':>6} {'dur':>5}  who      end    next   text")
    clashes = 0
    for i, m in enumerate(manifest):
        end = m["t"] + m["dur"]
        nxt = manifest[i + 1]["t"] if i + 1 < len(manifest) else cues["duration"]
        flag = "  <-- runs into the next line" if end > nxt - 0.15 else ""
        clashes += bool(flag)
        print(f"{m['t']:6.1f} {m['dur']:5.1f}  {m['who']:8} {end:6.1f} {nxt:6.1f}  {m['text'][:60]}{flag}")
    print(f"\n{len(manifest)} lines, {clashes} clash(es). Manifest: {out / 'manifest.json'}")

    rows = ["| # | who | line | pace | target wpm | speed | old wpm | new wpm | syl/s | old dur (s) | new dur (s) |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, m in enumerate(manifest, 1):
        old = Path(a.compare) / Path(m["file"]).name if a.compare else None
        if old and old.exists():
            ox, osr = load(old)
            ow, od = f"{rate(ox, osr, m['text'])['wpm']:.0f}", f"{len(ox) / osr:.2f}"
        else:
            ow = od = "-"
        rows.append(f"| {i} | {m['who']} | {m['text']} | {m.get('pace', 'neutral')} | {m.get('target_wpm', '-')} | "
                    f"{m.get('speed', '-')} | {ow} | {m['wpm']}{' (off target)' if m.get('off_target') else ''} | "
                    f"{m['sps']} | {od} | {m['dur']:.2f} |")
    (out / "report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
