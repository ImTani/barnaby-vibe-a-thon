"""Measure the soundtrack written by score_v2.py: loudness and true peak, the stems, every effect against its cue, the
dialogue against everything under it, and short excerpts around the key moments (written to .cache/audio/excerpts/).

  runtime/audio/.venv/Scripts/python video/v2/audio/check.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = V2.parents[1]
CUES = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))
MARK = CUES["marks"]
OUT = ROOT / ".cache" / "audio" / "excerpts"
STEMS = ("music", "sfx", "ambience", "voice")
SWELLS = {"timelapse", "compressor"}                 # these rise slowly by design: no single transient to time
MOMENTS = {                                          # name: (from, to, the event's time)
    "s2_bell_arrival": (MARK["bell_arrive"] - 1.5, MARK["bell_arrive"] + 4.5, MARK["bell_arrive"]),
    "s4_key_turn": (MARK["click_unlock"] - .5, MARK["unlock"] + 2.5, MARK["unlock"]),
    "s6_click_tab_change": (MARK["click_build"] - 1.0, MARK["tab_change"] + 2.5, MARK["click_build"]),
    "s9_final_bell": (MARK["bell_final"] - 1.5, MARK["bell_final"] + 4.5, MARK["bell_final"]),
}


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def rms(x):
    return float(np.sqrt((x.astype(np.float64) ** 2).mean() + 1e-20))


def true_peak(x, sr):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return float(np.abs(up).max())


def ffmpeg_ebur128(path: Path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null",
                        "-"], capture_output=True, text=True, timeout=600)
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, txt).group(1)) if re.search(pat, txt) else None
    return {"I": g(r"I:\s+(-?[\d.]+) LUFS"), "LRA": g(r"LRA:\s+(-?[\d.]+) LU"), "TP": g(r"Peak:\s+(-?[\d.]+) dBFS")}


def env_db(x, sr, hop=.002):
    m = np.abs(x).max(1) if x.ndim == 2 else np.abs(x)
    h = int(hop * sr)
    b = m[: len(m) // h * h].reshape(-1, h).max(1)
    return 20 * np.log10(b + 1e-9), hop


def cue_onsets(fx, sr):
    """For each one-shot cue: the first rise in the sfx stem within -30..+250 ms of the cue (12 dB over the 50 ms
    before it, and above -60 dBFS); and the effect's peak and loudiest 400 ms (momentary loudness) in the next 0.6 s."""
    e, hop = env_db(fx, sr)
    meter = pyln.Meter(sr, block_size=.4)
    rows = []
    for s in CUES["sfx"]:
        if "until" in s or s["type"] in SWELLS:
            continue
        t = float(s["t"])
        i0, i1 = int((t - .03) / hop), int((t + .25) / hop)
        found = None
        for i in range(i0, i1):
            base = np.median(e[max(0, i - 25): max(1, i - 2)])
            if e[i] > max(base + 12, -60):
                found = i * hop
                break
        seg = fx[int(t * sr): int((t + .6) * sr)]
        rows.append({"t": t, "type": s["type"], "label": s.get("label", ""), "onset": found,
                     "dev_ms": None if found is None else round((found - t) * 1000),
                     "peak_dbfs": round(db(np.abs(seg).max()), 1), "mom_lufs": round(momentary_max(seg, sr), 1)})
    return rows


def momentary_max(x, sr):
    """The loudest 400 ms window (K-weighted, as momentary loudness)."""
    m = pyln.Meter(sr, block_size=.4)
    best = -99.0
    for i in range(0, max(1, len(x) - int(.4 * sr)), int(.05 * sr)):
        w = x[i:i + int(.4 * sr)]
        if len(w) < int(.4 * sr):
            break
        with np.errstate(divide="ignore"):
            v = m.integrated_loudness(w)
        best = max(best, v if np.isfinite(v) else -99.0)
    return best


def dialogue_clearance(st, sr):
    man = json.loads((HERE / "voice" / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for i, line in enumerate(man, 1):
        a, b = line.get("speech", [line["t"], line["t"] + line["dur"]])
        sl = slice(int(a * sr), int(b * sr))
        v = st["voice"][sl]
        bed = st["music"][sl] + st["sfx"][sl] + st["ambience"][sl]
        rows.append({"line": i, "who": line["who"], "t": a, "voice_db": round(db(rms(v)), 1),
                     "under_db": round(db(rms(bed)), 1), "clear_db": round(db(rms(v)) - db(rms(bed)), 1),
                     "under": {k: round(db(rms(st[k][sl])), 1) for k in ("music", "sfx", "ambience")}})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    path = HERE / "soundtrack.wav"
    mix, sr = sf.read(str(path), always_2d=True)
    info = sf.info(str(path))
    st = {k: sf.read(str(HERE / f"{k}.wav"), always_2d=True)[0] for k in STEMS}
    meter = pyln.Meter(sr)
    res = {"file": {"sr": sr, "channels": info.channels, "subtype": info.subtype, "dur": round(len(mix) / sr, 3),
                    "film": CUES["duration"]}}
    res["pyloudnorm_I"] = round(meter.integrated_loudness(mix), 2)
    res["true_peak_dbtp_4x"] = round(db(true_peak(mix, sr)), 2)
    res["sample_peak_dbfs"] = round(db(np.abs(mix).max()), 2)
    res["ffmpeg"] = ffmpeg_ebur128(path)
    res["stems_sum_err_db"] = round(db(np.abs(sum(st.values()) - mix).max()), 1)
    res["stems_I"] = {k: (round(meter.integrated_loudness(x), 1) if rms(x) > 1e-6 else None) for k, x in st.items()}
    print(f"soundtrack: {res['file']}")
    print(f"  integrated {res['pyloudnorm_I']} LUFS (pyloudnorm), ffmpeg ebur128 {res['ffmpeg']}")
    print(f"  true peak {res['true_peak_dbtp_4x']} dBTP (4x), sample peak {res['sample_peak_dbfs']} dBFS")
    print(f"  stems sum to the mix within {res['stems_sum_err_db']} dBFS; stems integrated: {res['stems_I']}")

    rows = cue_onsets(st["sfx"], sr)
    res["cues"] = rows
    bad = [r for r in rows if r["onset"] is None or abs(r["dev_ms"]) > 40]
    devs = [abs(r["dev_ms"]) for r in rows if r["dev_ms"] is not None]
    print(f"effect cues: {len(rows)} one-shots; onset vs cue: median {np.median(devs):.0f} ms, max {max(devs)} ms")
    for r in bad:
        print(f"  ! {r['type']} at {r['t']:.2f} ({r['label']}): onset {r['onset']}, {r['dev_ms']} ms")
    by = {}
    for r in rows:
        by.setdefault(r["type"], []).append(r)
    print("  per type: peak dBFS / loudest 400 ms (LUFS), sfx stem alone")
    for k, v in by.items():
        print(f"    {k:12} n={len(v):2d}  peak {max(r['peak_dbfs'] for r in v):6.1f}  momentary {max(r['mom_lufs'] for r in v):6.1f}")

    dl = dialogue_clearance(st, sr)
    res["dialogue"] = dl
    cl = np.array([r["clear_db"] for r in dl])
    vm = [momentary_max(mix[int(r["t"] * sr): int((r["t"] + 2) * sr)], sr) for r in dl]
    res["dialogue_momentary_median"] = round(float(np.median(vm)), 1)
    print(f"dialogue over everything under it (speech windows): min {cl.min():.1f} dB, median {np.median(cl):.1f} dB; "
          f"lines' loudest 400 ms in the mix: median {np.median(vm):.1f} LUFS")
    for r in sorted(dl, key=lambda r: r["clear_db"])[:5]:
        print(f"  line {r['line']:2d} {r['who']:8} at {r['t']:7.2f}: voice {r['voice_db']} dBFS, under it {r['under_db']} dBFS"
              f" -> {r['clear_db']} dB  {r['under']}")

    OUT.mkdir(parents=True, exist_ok=True)
    res["moments"] = {}
    for name, (t0, t1, te) in MOMENTS.items():
        sl = slice(int(t0 * sr), int(t1 * sr))
        x = mix[sl]
        sf.write(str(OUT / f"{name}.wav"), x, sr, subtype="PCM_16")
        ev = slice(int((te - .05) * sr), int((te + .6) * sr))
        m = {"excerpt": f".cache/audio/excerpts/{name}.wav", "from": round(t0, 2), "to": round(t1, 2),
             "short_term_lufs": round(meter.integrated_loudness(x) if len(x) > sr * .5 else -99, 1),
             "event_peak_dbfs": round(db(np.abs(mix[ev]).max()), 1),
             "event_momentary_lufs": round(momentary_max(mix[ev], sr), 1),
             "event_stems_peak_db": {k: round(db(np.abs(st[k][ev]).max()), 1) for k in STEMS},
             "event_tp_dbtp": round(db(true_peak(mix[ev], sr)), 1),
             "event_stems_rms_db": {k: round(db(rms(st[k][ev])), 1) for k in STEMS}}
        res["moments"][name] = m
        print(f"{name}: {t0:.2f}-{t1:.2f} s, {m['short_term_lufs']} LUFS over the excerpt; at the event ({te:.2f} s) "
              f"peak {m['event_peak_dbfs']} dBFS / {m['event_tp_dbtp']} dBTP, momentary {m['event_momentary_lufs']} LUFS;\n"
              f"    stems RMS {m['event_stems_rms_db']}\n    stems peak {m['event_stems_peak_db']}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1), encoding="utf-8")
    ok = (res["ffmpeg"]["TP"] is not None and res["ffmpeg"]["TP"] <= -1.0 and abs(res["ffmpeg"]["I"] + 16) <= .5
          and sr == 48000 and info.channels == 2 and not bad)
    print("PASS" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
