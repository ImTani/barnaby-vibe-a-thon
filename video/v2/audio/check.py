"""Measure the soundtrack written by score_v2.py: loudness and true peak, the stems, every effect against its cue, the
dialogue against everything under it, and short excerpts around the key moments (written to .cache/audio/excerpts/).

  runtime/audio/.venv/Scripts/python video/v2/audio/check.py [--json out.json] [--sound-md]

--sound-md rewrites the generated part of SOUND.md (between its markers) from foley.py and these measurements.
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
STEMS = ("music", "effects", "ambience", "voice")        # sfx.wav = effects + ambience
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
    """For each one-shot cue: the first rise in the effects stem within -30..+250 ms of the cue (9 dB, or 5 dB within 0.25 s of the previous cue, over the 50 ms
    before it, and above -60 dBFS); and the effect's peak and loudiest 400 ms (momentary loudness) in the next 0.6 s."""
    e, hop = env_db(fx, sr)
    meter = pyln.Meter(sr, block_size=.4)
    import sys
    sys.path.insert(0, str(HERE))
    import foley
    rows, prev = [], -9.0
    for s in sorted(CUES["sfx"] + foley.extra_cues(CUES), key=lambda s: s["t"]):
        if "until" in s or s["type"] in SWELLS:
            continue
        t = float(s["t"])
        rise = 9 if t - prev > .25 else 5           # in a quick run (the fastest hand-back walk) a note lands on the last one's ring
        prev = t
        i0, i1 = int((t - .03) / hop), int((t + .25) / hop)
        found = None
        for i in range(i0, i1):
            base = np.median(e[max(0, i - 25): max(1, i - 2)])
            if e[i] > max(base + rise, -60):
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
        bed = st["music"][sl] + st["effects"][sl] + st["ambience"][sl]
        rows.append({"line": i, "who": line["who"], "t": a, "voice_db": round(db(rms(v)), 1),
                     "under_db": round(db(rms(bed)), 1), "clear_db": round(db(rms(v)) - db(rms(bed)), 1),
                     "under": {k: round(db(rms(st[k][sl])), 1) for k in ("music", "effects", "ambience")}})
    return rows


def kw_power(x, sr):
    """K-weighted power summed over channels (BS.1770), per sample."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cq_check", ROOT / "video" / "audio" / "compose.quorum.py")
    cq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cq)
    return (cq.k_weight(x.T.astype(np.float64)) ** 2).sum(0)


def window_lufs(p, sr, win):
    from scipy.ndimage import uniform_filter1d
    ms = np.maximum(uniform_filter1d(p, int(win * sr))[:: int(.1 * sr)], 0.0)
    return -0.691 + 10 * np.log10(ms + 1e-20)


def levels(st, sr):
    """Each category alone (re-rendered with the same ducking and master gain curve as the mix), against the dialogue:
    peak, the loudest 3 s (short-term max), the loudest 400 ms (momentary max) and the integrated level over the time it
    plays. The dialogue's reference is the median short-term level of the voice stem while someone speaks."""
    import sys
    sys.path.insert(0, str(HERE))
    import foley
    n = len(st["voice"])
    k = np.load(ROOT / ".cache" / "audio" / "master_gain.npy")
    venv = np.load(ROOT / ".cache" / "audio" / "voice_env.npy")
    duck_fx = (10 ** (-2.0 * venv / 20)).astype(np.float32)
    duck_amb = (10 ** (-4.0 * venv / 20)).astype(np.float32)
    meter = pyln.Meter(sr)
    vp = kw_power(st["voice"], sr)
    vst = window_lufs(vp, sr, 3.0)
    vmo = window_lufs(vp, sr, .4)
    d_st = float(np.median(vst[vst > -40]))
    d_mo = float(np.median(vmo[vmo > -40]))
    rows = [{"category": "dialogue (reference)", "peak": round(db(np.abs(st["voice"]).max()), 1),
             "st_max": round(float(vst.max()), 1), "mom_max": round(float(vmo.max()), 1),
             "integrated": round(meter.integrated_loudness(st["voice"]), 1), "st_typ": round(d_st, 1), "mom_typ": round(d_mo, 1)}]
    for name, types in foley.CATEGORIES.items():
        fx, amb, _ = foley.render(CUES, n, venv, only=types)
        x = ((fx * duck_fx + amb * duck_amb) * k).T
        if np.abs(x).max() < 1e-6:
            continue
        p = kw_power(x, sr)
        stl, mol = window_lufs(p, sr, 3.0), window_lufs(p, sr, .4)
        act = np.abs(x).max(1) > 10 ** (-70 / 20)
        idx = np.where(act)[0]
        seg = x[idx[0]: idx[-1] + 1]
        integ = meter.integrated_loudness(seg) if len(seg) > sr * .5 else float(mol.max())
        rows.append({"category": name, "peak": round(db(np.abs(x).max()), 1), "st_max": round(float(stl.max()), 1),
                     "mom_max": round(float(mol.max()), 1), "integrated": round(float(integ), 1),
                     "st_max_vs_dialogue": round(float(stl.max()) - d_st, 1),
                     "integrated_vs_dialogue": round(float(integ) - d_st, 1),
                     "mom_max_vs_dialogue": round(float(mol.max()) - d_mo, 1)})
        del fx, amb, x
    print(f"levels (dialogue short-term typical {d_st:.1f} LUFS, momentary typical {d_mo:.1f} LUFS):")
    for r in rows[1:]:
        print(f"  {r['category'][:44]:44} peak {r['peak']:6.1f}  st max {r['st_max']:6.1f} ({r['st_max_vs_dialogue']:+5.1f} LU)"
              f"  mom max {r['mom_max']:6.1f} ({r['mom_max_vs_dialogue']:+5.1f})  integrated {r['integrated']:6.1f} "
              f"({r['integrated_vs_dialogue']:+5.1f})")
    return rows


BEGIN, END = "<!-- generated by check.py --sound-md: begin -->", "<!-- generated by check.py --sound-md: end -->"


def write_sound_md(res: dict) -> None:
    import sys
    sys.path.insert(0, str(HERE))
    import foley
    L = [BEGIN, "", "## Mix: targets and measured", "",
         "| | target | measured |", "|---|---|---|",
         f"| integrated loudness | -16 LUFS | {res['ffmpeg']['I']} LUFS (ffmpeg ebur128), {res['pyloudnorm_I']} (pyloudnorm) |",
         f"| true peak | <= -1 dBTP | {res['ffmpeg']['TP']} dBTP (ffmpeg, 4x), {res['true_peak_dbtp_4x']} dBTP (4x polyphase) |",
         f"| loudness range | - | {res['ffmpeg']['LRA']} LU |",
         f"| format | 48 kHz stereo | {res['file']['sr']} Hz, {res['file']['channels']} ch, {res['file']['subtype']}, "
         f"{res['file']['dur']} s (film {res['file']['film']} s) |",
         f"| music + effects + ambience + voice = soundtrack | exact | max difference {res['stems_sum_err_db']} dBFS (dither) |",
         f"| sfx.wav = effects + ambience | exact | max difference {res['sfx_is_effects_plus_ambience_db']} dBFS (dither) |",
         f"| stems, integrated | - | " + ", ".join(f"{k} {v} LUFS" for k, v in res["stems_I"].items()) + " |"]
    dl = res["dialogue"]
    cl = sorted(dl, key=lambda r: r["clear_db"])
    L += [f"| dialogue over everything under it | always clear | min {cl[0]['clear_db']} dB (line {cl[0]['line']}), median "
          f"{float(np.median([r['clear_db'] for r in dl])):.1f} dB over {len(dl)} lines (RMS in each line's speech window) |"]
    if "speakers" in res:
        L += ["| voices, level per speaker | consistent | " + "; ".join(
            f"{k} {v['median_lufs']} LUFS ({v['min']}..{v['max']}, {v['lines']} lines, {'/'.join(v['src'])})"
            for k, v in res["speakers"].items()) + " |"]
    devs = [abs(r["dev_ms"]) for r in res["cues"] if r["dev_ms"] is not None]
    L += [f"| effects on their cues | on the cue | {len(devs)} one-shots: median {np.median(devs):.0f} ms, max {max(devs)} ms "
          f"from cue to the first rise in the effects stem |", ""]
    if "levels" in res:
        lv = res["levels"]
        d = lv[0]
        L += ["## Levels by category, against the dialogue", "",
              f"Each category re-rendered alone with the mix's ducking and master gain. The dialogue's reference: its typical "
              f"short-term (3 s) level {d['st_typ']} LUFS and typical momentary (400 ms) level {d['mom_typ']} LUFS while someone "
              f"speaks (voice stem: peak {d['peak']} dBFS, integrated {d['integrated']} LUFS). Targets: beds -14 to -20 LU under "
              "the dialogue (short-term max), the opening's rain and fan at the quiet end; foley and UI never louder than a "
              "voice (momentary max under the dialogue's typical momentary level).", "",
              "| category | peak dBFS | short-term max LUFS (vs dialogue) | momentary max LUFS (vs dialogue) | integrated while playing LUFS (vs dialogue) |",
              "|---|---|---|---|---|"]
        for r in lv[1:]:
            L.append(f"| {r['category']} | {r['peak']} | {r['st_max']} ({r['st_max_vs_dialogue']:+.1f} LU) | {r['mom_max']} "
                     f"({r['mom_max_vs_dialogue']:+.1f} LU) | {r['integrated']} ({r['integrated_vs_dialogue']:+.1f} LU) |")
        L.append("")
    L += ["## Key moments (excerpts in .cache/audio/excerpts/)", "",
          "| moment | excerpt | excerpt loudness | at the event: peak / loudest 400 ms | stems RMS at the event (dBFS) |",
          "|---|---|---|---|---|"]
    for name, m in res["moments"].items():
        L.append(f"| {name} | {m['from']}-{m['to']} s | {m['short_term_lufs']} LUFS | {m['event_peak_dbfs']} dBFS / "
                 f"{m['event_momentary_lufs']} LUFS | " + ", ".join(f"{k} {v}" for k, v in m["event_stems_rms_db"].items()) + " |")
    L += ["", "## Effect cues: source and processing", "",
          "Core Library paths are under `C:/ProgramData/Ableton/Live 12 Suite/Resources/Core Library/Samples/`. "
          "Measured: onset = cue to the first rise in the effects stem; peak and loudest 400 ms of the effects stem alone "
          "(0-0.6 s after the cue; overlapping sounds count).", ""]
    meas = {(round(r["t"], 3), r["type"]): r for r in res["cues"]}
    items = sorted(CUES["sfx"] + foley.extra_cues(CUES), key=lambda s: s["t"])
    order = []
    for s_ in items:
        if s_["type"] not in order:
            order.append(s_["type"])
    for typ in order:
        srcs = foley.SOURCES.get(typ, [])
        L += [f"### {typ}", "", "Source: " + "; ".join(f"`{x}`" if not x.startswith(("synth", "modal")) else x for x in srcs),
              "", "Processing: " + foley.PROCESS.get(typ, "?"), ""]
        rows = [s_ for s_ in items if s_["type"] == typ]
        if "until" in rows[0]:
            L += ["| from | to | level | label |", "|---|---|---|---|"]
            for s_ in rows:
                L.append(f"| {s_['t']:.2f} | {float(s_['until']):.2f} | {s_.get('level', 1.0)} x {foley.BED_GAIN[typ]} RMS | "
                         f"{s_.get('label', '')} |")
        else:
            L += ["| cue (s) | label | onset | peak dBFS | loudest 400 ms |", "|---|---|---|---|---|"]
            for s_ in rows:
                r = meas.get((round(float(s_["t"]), 3), typ))
                if r:
                    L.append(f"| {s_['t']:.2f} | {s_.get('label', '')} | {r['dev_ms']:+d} ms | {r['peak_dbfs']} | {r['mom_lufs']} LUFS |"
                             if r["dev_ms"] is not None else f"| {s_['t']:.2f} | {s_.get('label', '')} | (masked) | {r['peak_dbfs']} | {r['mom_lufs']} LUFS |")
                else:
                    L.append(f"| {s_['t']:.2f} | {s_.get('label', '')} | (swell or derived: not timed) | | |")
        L.append("")
    L.append(END)
    md = HERE / "SOUND.md"
    text = md.read_text(encoding="utf-8") if md.exists() else f"# Sound\n\n{BEGIN}\n{END}\n"
    a_, b_ = text.index(BEGIN), text.index(END) + len(END)
    md.write_text(text[:a_] + "\n".join(L) + text[b_:], encoding="utf-8")
    print(f"wrote the generated part of {md}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None)
    ap.add_argument("--sound-md", action="store_true", help="rewrite the generated part of SOUND.md")
    ap.add_argument("--levels", action="store_true", help="the per-category level audit (re-renders each category alone)")
    a = ap.parse_args()
    path = HERE / "soundtrack.wav"
    mix, sr = sf.read(str(path), always_2d=True)
    info = sf.info(str(path))
    st = {k: sf.read(str(HERE / f"{k}.wav"), always_2d=True)[0] for k in STEMS}
    meter = pyln.Meter(sr)
    res = {"file": {"sr": sr, "channels": info.channels, "subtype": info.subtype, "dur": round(len(mix) / sr, 3),
                    "film": CUES["duration"]}}
    if abs(len(mix) / sr - float(CUES["duration"])) > .01:
        print(f"soundtrack.wav is {len(mix) / sr:.2f} s but the cue sheet is {CUES['duration']} s: re-run score_v2.py first")
        return 2
    res["pyloudnorm_I"] = round(meter.integrated_loudness(mix), 2)
    res["true_peak_dbtp_4x"] = round(db(true_peak(mix, sr)), 2)
    res["sample_peak_dbfs"] = round(db(np.abs(mix).max()), 2)
    res["ffmpeg"] = ffmpeg_ebur128(path)
    res["stems_sum_err_db"] = round(db(np.abs(sum(st.values()) - mix).max()), 1)
    sfx_wav = sf.read(str(HERE / "sfx.wav"), always_2d=True)[0]
    res["sfx_is_effects_plus_ambience_db"] = round(db(np.abs(sfx_wav - st["effects"] - st["ambience"]).max()), 1)
    res["stems_I"] = {k: (round(meter.integrated_loudness(x), 1) if rms(x) > 1e-6 else None) for k, x in st.items()}
    print(f"soundtrack: {res['file']}")
    print(f"  integrated {res['pyloudnorm_I']} LUFS (pyloudnorm), ffmpeg ebur128 {res['ffmpeg']}")
    print(f"  true peak {res['true_peak_dbtp_4x']} dBTP (4x), sample peak {res['sample_peak_dbfs']} dBFS")
    print(f"  stems sum to the mix within {res['stems_sum_err_db']} dBFS; stems integrated: {res['stems_I']}")

    rows = cue_onsets(st["effects"], sr)
    res["cues"] = rows
    bad = [r for r in rows if r["onset"] is None or abs(r["dev_ms"]) > 40]
    devs = [abs(r["dev_ms"]) for r in rows if r["dev_ms"] is not None]
    print(f"effect cues: {len(rows)} one-shots; onset vs cue: median {np.median(devs):.0f} ms, max {max(devs)} ms")
    for r in bad:
        print(f"  ! {r['type']} at {r['t']:.2f} ({r['label']}): onset {r['onset']}, {r['dev_ms']} ms")
    by = {}
    for r in rows:
        by.setdefault(r["type"], []).append(r)
    print("  per type: peak dBFS / loudest 400 ms (LUFS), effects stem alone")
    for k, v in by.items():
        print(f"    {k:12} n={len(v):2d}  peak {max(r['peak_dbfs'] for r in v):6.1f}  momentary {max(r['mom_lufs'] for r in v):6.1f}")

    dl = dialogue_clearance(st, sr)
    res["dialogue"] = dl
    man = json.loads((HERE / "voice" / "manifest.json").read_text(encoding="utf-8"))
    per = {}
    for r, line in zip(dl, man):
        a_, b_ = line.get("speech", [line["t"], line["t"] + line["dur"]])
        w = st["voice"][int(a_ * sr): int(b_ * sr)]
        if len(w) > .5 * sr:
            per.setdefault(line["who"], []).append(meter.integrated_loudness(w))
    res["speakers"] = {k: {"lines": len(v), "median_lufs": round(float(np.median(v)), 1),
                           "min": round(float(min(v)), 1), "max": round(float(max(v)), 1),
                           "src": sorted({str(l.get("src")) for l in man if l["who"] == k})} for k, v in per.items()}
    print("speakers (each line's loudness over its speech, in the voice stem):")
    for k, v in res["speakers"].items():
        print(f"  {k:8} {v['lines']:2d} lines  median {v['median_lufs']} LUFS  range {v['min']}..{v['max']}  ({', '.join(v['src'])})")
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
    if a.levels:
        res["levels"] = levels(st, sr)
    if a.sound_md:
        write_sound_md(res)
    ok = (res["ffmpeg"]["TP"] is not None and res["ffmpeg"]["TP"] <= -1.0 and abs(res["ffmpeg"]["I"] + 16) <= .5
          and sr == 48000 and info.channels == 2 and not bad)
    print("PASS" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
