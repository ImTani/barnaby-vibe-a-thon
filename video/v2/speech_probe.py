"""Speech forensics for the film's voice lines: speaking rate, gaps, energy steps and pitch resets.

  runtime/voice/.venv/Scripts/python video/v2/speech_probe.py FILE.wav [--text "the line"] [--table]

Measures (see video/v2/SPEECH.md, "How to measure"):
- active duration: first to last frame above -40 dB re the line's loudest 10 ms frame (leading and trailing
  silence excluded), and the speaking rate over it in words/min and syllables/s;
- every internal silence of 60 ms or more (a pause or a stitched join), with the level step and F0 step across it;
- an autocorrelation F0 track (40 ms window, 10 ms hop, 60-400 Hz), summarised per voiced run.
numpy only, so it runs in the voice venv.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

HOP = 0.010
WIN = 0.040
QUIET_DB = -40.0


def load(path: str | Path) -> tuple[np.ndarray, int]:
    import soundfile as sf
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return x.mean(1), sr


def frames_db(x: np.ndarray, sr: int) -> np.ndarray:
    hop = int(HOP * sr)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms / (rms.max() + 1e-12))


def active_span(x: np.ndarray, sr: int, quiet_db: float = QUIET_DB) -> tuple[float, float]:
    """(start, end) seconds of the speech, without leading/trailing silence."""
    db = frames_db(x, sr)
    on = np.flatnonzero(db > quiet_db)
    if not on.size:
        return 0.0, 0.0
    return on[0] * HOP, (on[-1] + 1) * HOP


def f0_track(x: np.ndarray, sr: int, fmin: float = 60.0, fmax: float = 400.0) -> np.ndarray:
    """F0 per 10 ms frame by normalised autocorrelation; 0 where unvoiced."""
    hop, win = int(HOP * sr), int(WIN * sr)
    lo, hi = int(sr / fmax), int(sr / fmin)
    db = frames_db(x, sr)
    out = np.zeros(len(db))
    w = np.hanning(win)
    # Boersma (1993): divide by the window's own autocorrelation, so a periodic frame scores near 1 at its period
    acw = np.fft.irfft(np.abs(np.fft.rfft(w, 2 * win)) ** 2)[: hi + 2]
    acw = acw / acw[0]
    for i in range(len(db)):
        c = i * hop + hop // 2
        seg = x[max(0, c - win // 2): c + win // 2]
        if len(seg) < win or db[i] < -35:
            continue
        seg = (seg - seg.mean()) * w
        ac = np.fft.irfft(np.abs(np.fft.rfft(seg, 2 * win)) ** 2)[: hi + 2]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0] / np.maximum(acw, 1e-3)
        lag = lo + int(np.argmax(ac[lo: hi + 1]))
        if ac[lag] < 0.5:
            continue
        # parabolic interpolation around the peak
        if 0 < lag < len(ac) - 1:
            a, b, g = ac[lag - 1], ac[lag], ac[lag + 1]
            den = a - 2 * b + g
            lag = lag + (0.5 * (a - g) / den if den else 0)
        out[i] = sr / lag
    # octave-jump cleanup against the running median of voiced frames
    v = out > 0
    if v.sum() > 5:
        med = np.median(out[v])
        for i in np.flatnonzero(v):
            if out[i] > 1.7 * med:
                out[i] /= 2
            elif out[i] < 0.6 * med:
                out[i] *= 2
    return out


def gaps(x: np.ndarray, sr: int, min_gap: float = 0.06, quiet_db: float = QUIET_DB) -> list[tuple[float, float]]:
    """Internal silences (start, length) inside the active span."""
    db = frames_db(x, sr)
    a, b = active_span(x, sr, quiet_db)
    q = db <= quiet_db
    out, i = [], int(a / HOP)
    end = int(b / HOP)
    while i < end:
        if q[i]:
            j = i
            while j < end and q[j]:
                j += 1
            if (j - i) * HOP >= min_gap:
                out.append((i * HOP, (j - i) * HOP))
            i = j
        else:
            i += 1
    return out


def syllables(text: str) -> int:
    """Orthographic syllable estimate (vowel groups, silent final e, numbers spelled already)."""
    n = 0
    for w in re.findall(r"[A-Za-z']+", text):
        w = w.lower().replace("'", "")
        groups = re.findall(r"[aeiouy]+", w)
        k = len(groups)
        if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and k > 1:
            k -= 1
        n += max(1, k)
    return n


def words(text: str) -> int:
    """Spoken words: "twenty-three" and "say-so" are two, "Anika's" and "I've" are one (SPEECH.md, How to measure)."""
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", text))


def syllables_ph(phonemes: str) -> int:
    """Syllables from the phoneme string Kokoro is given (one per vowel nucleus): the same count voice/tts.py uses."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from voice.tts import syllables as count
    return count(phonemes)


def rate(x: np.ndarray, sr: int, text: str, phonemes: str = "") -> dict:
    """Speaking rate over the active span (edge silence excluded, internal pauses included), and articulation rate
    (pauses of 100 ms or more also excluded). Syllables come from the phonemes when given, else from spelling."""
    a, b = active_span(x, sr)
    dur = max(b - a, 1e-6)
    paused = sum(g for _, g in gaps(x, sr, 0.10))
    syl = syllables_ph(phonemes) if phonemes else syllables(text)
    return {"active": dur, "words": words(text), "syl": syl, "wpm": words(text) / dur * 60, "sps": syl / dur,
            "artic_sps": syl / max(dur - paused, 1e-6), "pauses": paused}


def runs(f0: np.ndarray, db: np.ndarray, min_len: int = 4) -> list[dict]:
    """Voiced runs: start, end, mean/first/last F0, mean level."""
    out, i = [], 0
    while i < len(f0):
        if f0[i] > 0:
            j = i
            while j < len(f0) and (f0[j] > 0 or (j + 1 < len(f0) and f0[j + 1] > 0 and f0[j - 1] > 0)):
                j += 1
            if j - i >= min_len:
                seg = f0[i:j][f0[i:j] > 0]
                out.append({"t0": i * HOP, "t1": j * HOP, "f0": float(np.median(seg)),
                            "f0_first": float(np.median(seg[:3])), "f0_last": float(np.median(seg[-3:])),
                            "db": float(db[i:j].mean())})
            i = j
        else:
            i += 1
    return out


def report(path: str | Path, text: str = "", table: bool = False) -> dict:
    x, sr = load(path)
    db = frames_db(x, sr)
    f0 = f0_track(x, sr)
    a, b = active_span(x, sr)
    print(f"{path}: total {len(x) / sr:.2f}s, speech {a:.2f}-{b:.2f}s")
    if text:
        r = rate(x, sr, text)
        print(f"  rate: {r['wpm']:.0f} wpm, {r['sps']:.2f} syl/s overall, {r['artic_sps']:.2f} syl/s articulation, "
              f"pauses {r['pauses']:.2f}s ({words(text)} words, {syllables(text)} syllables)")
    for t, g in gaps(x, sr):
        i0, i1 = int(t / HOP), int((t + g) / HOP)
        before = db[max(0, i0 - 15):i0]
        after = db[i1:i1 + 15]
        fb = f0[max(0, i0 - 20):i0]
        fa = f0[i1:i1 + 20]
        fb, fa = fb[fb > 0], fa[fa > 0]
        print(f"  gap {t:5.2f}s +{g * 1000:4.0f} ms | level {before.mean():6.1f} -> {after.mean():6.1f} dB"
              f" | F0 {np.median(fb[-5:]) if fb.size else 0:5.0f} -> {np.median(fa[:5]) if fa.size else 0:5.0f} Hz")
    rs = runs(f0, db)
    print("  voiced runs (t0-t1  median F0  first->last  level):")
    for r in rs:
        print(f"    {r['t0']:5.2f}-{r['t1']:5.2f}  {r['f0']:5.0f} Hz  {r['f0_first']:4.0f}->{r['f0_last']:4.0f}  {r['db']:6.1f} dB")
    if table:
        for i in range(0, len(f0), 2):
            print(f"    {i * HOP:5.2f} {db[i]:6.1f} {f0[i]:5.0f}")
    return {"x": x, "sr": sr, "db": db, "f0": f0, "runs": rs}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="+")
    ap.add_argument("--text", default="")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    for w in a.wav:
        report(w, a.text, a.table)
    sys.exit(0)
