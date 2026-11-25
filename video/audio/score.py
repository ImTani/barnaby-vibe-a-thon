"""The Barnaby film's soundtrack: a score composed in code but PLAYED by real instruments, plus UI sound effects and
the voice lines, mixed and mastered to audio/soundtrack.wav (160 s, 48 kHz, -16 LUFS). render.js muxes it in.

  runtime/audio/.venv/Scripts/python video/audio/score.py            (about a minute; Ample needs ~8 s to load)
  ... score.py --no-vst      quick structural check with a plain synth stand-in (never ship this)

- Music: fingerpicked/strummed acoustic guitar on Ample Guitar M Lite II (VST2) and electric bass on MODO BASS 2
  (VST3), both hosted offline by DawDreamer, with Valhalla VintageVerb as a reverb send. D major, 80 BPM
  (bar = 3 s), on a grid that puts the "lift" downbeat exactly on 105.8 s, the moment the new endpoint appears.
- Sections and moods follow cues.json -> music; sound effects follow cues.json -> sfx (synthesised UI sounds,
  helpers from compose.quorum.py); voice lines come from audio/voice/manifest.json (rendered by voices.py, or
  Tani's recorded takes in audio/takes/).
- The music ducks under speech (-6 dB, 80 ms attack, 450 ms release).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
VIDEO = HERE.parent
SR, BLOCK = 48000, 512
DUR = 160.0
N = int(SR * DUR)

# DSP helpers from Quorum's compose script (bus/place/fx_*/render_sfx/convolve/limiter...), re-sized to 160 s
_spec = importlib.util.spec_from_file_location("cq", HERE / "compose.quorum.py")
cq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cq)
cq.DUR, cq.N = DUR, N
cq.T = np.arange(N, dtype=np.float64) / SR

PLUGINS = Path(r"X:\VST Plugins")
GUITAR = PLUGINS / "VST2" / "AGML2.dll"                    # Ample Guitar M Lite II (acoustic)
BASS = PLUGINS / "VST3" / "MODO BASS 2.vst3"
VERB = PLUGINS / "VST3" / "ValhallaVintageVerb.vst3"

BPM = 80
BEAT = 60 / BPM                                            # 0.75 s
BAR = 4 * BEAT                                             # 3.0 s
GRID0 = 0.8                                                # bar k starts at GRID0 + k*BAR; bar 35 = 105.8 s


def bar(k: float) -> float:
    return GRID0 + k * BAR


# ── harmony: guitar voicings (low -> high, all within E2..E5) and the bass root ──
CH = {
    "D":     ([50, 57, 62, 66, 69], 38),
    "Dadd9": ([50, 57, 62, 64, 66, 69], 38),
    "A/C#":  ([49, 52, 57, 64, 69], 37),
    "A":     ([45, 52, 57, 61, 64], 33),
    "Asus4": ([45, 52, 57, 62, 64], 33),
    "Bm":    ([47, 54, 59, 62, 66], 35),
    "Bm7":   ([47, 54, 57, 62, 66], 35),
    "Bm/A":  ([45, 54, 59, 62, 66], 33),
    "G":     ([43, 47, 50, 55, 59, 67], 31),
    "Gmaj7": ([43, 50, 54, 59, 62], 31),
    "G/F#":  ([42, 50, 55, 59, 62], 30),
    "D/F#":  ([42, 50, 57, 62, 66], 30),
    "Em7":   ([40, 47, 50, 55, 62], 28),
    "Em/D":  ([50, 55, 59, 64, 67], 38),
}

# section plan: (first bar, chords one per bar, style)
PLAN = [
    (0,  ["Bm", "Bm", "G"], "tick"),                                     # 0.8-9.8   intro: thin, clock-like
    (3,  ["D"], "breath"),                                               # 9.8-12.8  relief as the tabs fade
    (4,  ["D", "A/C#", "Bm7", "Gmaj7", "D/F#", "Asus4"], "pick_soft"),   # 12.8-30.8 handover: warm, wistful
    (10, ["D", "G", "Bm", "A"] * 4 + ["D"], "pick"),                     # 30.8-81.8 work: light, confident
    (27, ["Bm", "Bm/A", "G", "G/F#", "Em7", "Em/D", "Asus4", "A"], "build"),  # 81.8-105.8 build: rising
    (35, ["D", "A/C#", "Bm", "G", "D", "A", "G", "A"], "strum"),          # 105.8-129.8 lift: brighter
    (43, ["D", "A/C#", "Bm", "G", "A"], "strum_full"),                   # 129.8-144.8 montage: fullest
]
FINAL_AT = 147.0                                                         # last chord, with the wordmark


class Score:
    def __init__(self, seed: int = 7):
        self.rng = np.random.default_rng(seed)
        self.guitar: list[tuple[int, int, float, float]] = []            # (note, velocity, start, duration)
        self.bass: list[tuple[int, int, float, float]] = []

    def _h(self, t: float, ms: float = 7) -> float:                       # humanise timing
        return max(0.0, t + self.rng.normal(0, ms / 1000))

    def _v(self, v: float, spread: float = 6) -> int:
        return int(np.clip(v + self.rng.normal(0, spread), 1, 127))

    def g(self, note: int, vel: float, t: float, dur: float, ms: float = 7) -> None:
        self.guitar.append((note, self._v(vel), self._h(t, ms), dur))

    def b(self, note: int, vel: float, t: float, dur: float) -> None:
        self.bass.append((note, self._v(vel, 4), self._h(t, 5), dur))

    def strum(self, notes: list[int], vel: float, t: float, dur: float, up: bool = False, spread: float = .014) -> None:
        seq = notes[::-1][:4] if up else notes
        for i, n in enumerate(seq):
            self.g(n, vel * (0.78 if up else 1.0) * (0.92 + 0.08 * (i == 0)), t + i * spread, dur, ms=3)

    # ── styles: one bar each ──
    def bar_tick(self, k: int, ch: str) -> None:
        v, root = CH[ch]
        t0 = bar(k)
        for e in range(8):                                                # muted eighths on the 5th, like a clock
            self.g(v[2], 44 + 8 * (e % 2 == 0) + 3 * k, t0 + e * BEAT / 2, .1)
        self.g(v[0], 40, t0, 2.6)                                         # a low root, barely there
        if k == 2:
            self.g(v[-1] + 12 if v[-1] + 12 <= 76 else v[-1], 30, t0 + 2.25, 1.4)

    def bar_breath(self, k: int, ch: str) -> None:
        v, root = CH[ch]
        t0 = bar(k) + .6                                                  # lands after the whoosh at 10.4
        for i, n in enumerate(v):                                         # slow rolled chord, let ring
            self.g(n, 44 - 2 * i, t0 + i * .09, 3.4, ms=2)

    def bar_pick(self, k: int, ch: str, soft: bool = False) -> None:
        v, root = CH[ch]
        t0, base = bar(k), (46 if soft else 56)
        # travis-ish: thumb alternates root / 3rd string on the beats, fingers on the off-beats
        thumb = [v[0], v[1] if len(v) > 4 else v[0], v[0], v[1]]
        fingers = [v[-1], v[-2], v[-1], v[-3]] if not soft else [v[-2], v[-1], v[-2], v[-3]]
        for bt in range(4):
            self.g(thumb[bt], base + 6 * (bt == 0), t0 + bt * BEAT, 1.6)
            self.g(fingers[bt], base - 8 + 4 * (bt == 2), t0 + bt * BEAT + BEAT / 2, 1.2)
        if not soft and k % 4 == 3:                                       # a small fill at the end of each phrase
            self.g(v[-1] + 2 if v[-1] + 2 <= 76 else v[-2], base - 10, t0 + 3.5 * BEAT + BEAT / 4, .5)

    def bar_build(self, k: int, ch: str, idx: int) -> None:
        v, root = CH[ch]
        t0 = bar(k)
        sub = 4 if idx >= 6 else 2                                        # eighths, then sixteenths for the last 2 bars
        steps = 4 * sub
        order = [0, 2, 3, 4, 1, 3, 2, 4] if sub == 2 else [0, 2, 3, 4, 3, 2, 1, 3, 4, 3, 2, 4, 3, 4, 2, 4]
        for e in range(steps):
            n = v[order[e % len(order)] % len(v)]
            self.g(n, 46 + idx * 4 + 6 * (e % sub == 0), t0 + e * BAR / steps, 0.9 if sub == 2 else .45)
        # bass: pulsing eighths from bar 2, getting firmer
        if idx >= 1:
            for e in range(8):
                self.b(root + (12 if e % 4 == 3 and idx >= 4 else 0), 62 + idx * 4, t0 + e * BEAT / 2, BEAT / 2 * .85)
        else:
            self.b(root, 66, t0, BAR * .95)

    def bar_strum(self, k: int, ch: str, full: bool = False) -> None:
        v, root = CH[ch]
        t0 = bar(k)
        # D . D U . U D U  (eighths)
        pattern = [(0, False, 1.0), (2, False, .85), (3, True, .7), (5, True, .7), (6, False, .85), (7, True, .65)]
        base = 70 if full else 62
        for e, up, acc in pattern:
            self.strum(v, base * acc + (8 if e == 0 else 0), t0 + e * BEAT / 2, 1.0 if not up else .6, up)
        if full:                                                          # a high arpeggio line on top
            for e in (1, 4):
                self.g(min(v[-1] + 12, 76), 44, t0 + e * BEAT / 2, .9)
        # bass: root on 1, fifth on the 2&, octave on 3, approach note on 4&
        fifth = root + 7
        self.b(root, 80 if full else 74, t0, BEAT * 1.4)
        self.b(fifth, 66, t0 + 1.5 * BEAT, BEAT * .45)
        self.b(root + 12 if root + 12 <= 50 else root, 70, t0 + 2 * BEAT, BEAT * .9)
        self.b(root, 62, t0 + 3 * BEAT, BEAT * .45)
        self.b(root + (2 if root + 2 <= 50 else -1), 58, t0 + 3.5 * BEAT, BEAT * .45)

    def bass_walk(self, k: int, ch: str, nxt: str | None) -> None:
        v, root = CH[ch]
        t0 = bar(k)
        self.b(root, 70, t0, BEAT * 1.8)
        self.b(root + 7, 60, t0 + 2 * BEAT, BEAT * .9)
        if nxt:                                                           # a passing note into the next chord
            r2 = CH[nxt][1]
            step = 1 if r2 > root else -1
            self.b(r2 - step * (1 if abs(r2 - root) > 2 else 0) if r2 != root else root + 4, 56, t0 + 3.5 * BEAT, BEAT * .45)

    def compose(self) -> None:
        for first, chords, style in PLAN:
            for i, ch in enumerate(chords):
                k = first + i
                nxt = chords[i + 1] if i + 1 < len(chords) else None
                if style == "tick":
                    self.bar_tick(k, ch)
                elif style == "breath":
                    self.bar_breath(k, ch)
                elif style == "pick_soft":
                    self.bar_pick(k, ch, soft=True)
                    if k >= 6:                                            # bass enters softly as Barnaby arrives
                        self.b(CH[ch][1], 50 + 3 * (k - 6), bar(k), BAR * .95)
                elif style == "pick":
                    self.bar_pick(k, ch)
                    self.bass_walk(k, ch, nxt)
                elif style == "build":
                    self.bar_build(k, ch, i)
                elif style in ("strum", "strum_full"):
                    self.bar_strum(k, ch, full=style == "strum_full")
        # the montage's last bar (A) leans into the close; the bell rings at 146.5 over an Asus4 hold
        for i, n in enumerate(CH["Asus4"][0]):
            self.g(n, 40 - 2 * i, 144.8 + i * .06, 2.0, ms=2)
        self.b(CH["Asus4"][1], 56, 144.8, 2.0)
        # final chord with the wordmark: a slow roll of Dadd9, ringing out, and a last high D
        for i, n in enumerate(CH["Dadd9"][0]):
            self.g(n, 76 - 3 * i, FINAL_AT + i * .11, 9.0, ms=2)
        self.b(38, 70, FINAL_AT, 8.0)
        for i, n in enumerate([62, 66, 69, 74]):                          # a soft re-roll under "Even the old ones."
            self.g(n, 62 - 3 * i, 151.6 + i * .14, 7.0, ms=0)
        for i, n in enumerate([57, 62, 66, 69, 74]):                      # and a last one with the credits line
            self.g(n, 60 - 3 * i, 154.0 + i * .16, 6.0, ms=0)
        self.b(38, 54, 154.0, 5.5)


# ── rendering ──
def render_instrument(path: Path, notes, wait: float = 0.0, params: dict | None = None) -> np.ndarray:
    import dawdreamer as daw
    engine = daw.RenderEngine(SR, BLOCK)
    p = engine.make_plugin_processor("inst", str(path))
    for k, val in (params or {}).items():
        p.set_parameter(k, val)
    for n, v, t, d in notes:
        if t < DUR:
            p.add_midi_note(int(n), int(v), float(t), float(min(d, DUR - t)))
    engine.load_graph([(p, [])])
    if wait:
        time.sleep(wait)                                                  # Ample streams its samples asynchronously
    engine.render(DUR)
    a = engine.get_audio().astype(np.float32)
    out = np.zeros((2, N), np.float32)
    m = min(N, a.shape[1])
    out[:, :m] = a[:2, :m] if a.shape[0] >= 2 else np.vstack([a[:1, :m]] * 2)
    return out


def reverb(x: np.ndarray) -> np.ndarray:
    import dawdreamer as daw
    engine = daw.RenderEngine(SR, BLOCK)
    src = engine.make_playback_processor("src", x)
    v = engine.make_plugin_processor("verb", str(VERB))
    v.set_parameter(0, 1.0)                                               # 100% wet: it's a send
    v.set_parameter(2, 0.30)                                              # decay ~2.5 s
    v.set_parameter(1, 0.30)                                              # pre-delay ~25 ms
    engine.load_graph([(src, []), (v, ["src"])])
    engine.render(DUR)
    a = engine.get_audio().astype(np.float32)
    out = np.zeros((2, N), np.float32)
    out[:, :min(N, a.shape[1])] = a[:2, :N]
    return out


def stand_in(notes, bright: float = .45) -> np.ndarray:
    """--no-vst only: a plain plucked stand-in so the arrangement can be checked without loading plugins."""
    out = cq.bus()
    for n, v, t, d in notes:
        y = cq.pluck(n, t60=min(2.0, d + .4), dur=min(2.5, d + .5), bright=bright)
        cq.place(out, y, t, (v / 127) * .25)
    return out


def envelope(x: np.ndarray, attack: float, release: float) -> np.ndarray:
    """Peak follower (mono), for ducking."""
    m = np.abs(x).max(0) if x.ndim == 2 else np.abs(x)
    hop = 240
    blocks = m[: len(m) // hop * hop].reshape(-1, hop).max(1)
    a_up, a_dn = np.exp(-hop / (attack * SR)), np.exp(-hop / (release * SR))
    e, cur = np.empty_like(blocks), 0.0
    for i, s in enumerate(blocks):
        cur = s + a_up * (cur - s) if s > cur else s + a_dn * (cur - s)
        e[i] = cur
    full = np.repeat(e, hop)
    return np.pad(full, (0, len(m) - len(full)), mode="edge")


def voices() -> tuple[np.ndarray, list[dict]]:
    man = json.loads((HERE / "voice" / "manifest.json").read_text(encoding="utf-8"))
    out = cq.bus()
    for line in man:
        y, sr = sf.read(HERE / line["file"], dtype="float32", always_2d=True)
        if sr != SR:                                                      # Kokoro renders at 24 kHz
            from scipy.signal import resample_poly
            y = resample_poly(y, SR // np.gcd(SR, sr), sr // np.gcd(SR, sr), axis=0).astype(np.float32)
        y = y.T if y.shape[1] <= 2 else y
        mono = y.mean(0)
        rms = np.sqrt((mono[np.abs(mono) > 1e-3] ** 2).mean() + 1e-12)
        mono = mono * (0.1 / rms)                                         # every line at the same speaking level
        pan = {"Barnaby": 0.0, "Martin": -0.12, "Theo": -0.1, "Priya": 0.12}.get(line["who"], 0.0)
        cq.place(out, mono, float(line["t"]), 1.0, pan)
    # speech is peaky (crest ~18 dB): tame the peaks on the voice bus so the master limiter isn't doing it
    pk = float(np.abs(out).max())
    out = out * cq.limiter_gain(out, 20 * np.log10(pk) - 6.0)
    return out, man


SFX_MAP = {"tab": "land", "shimmer": "sparkle", "success": "ding"}


def sfx_list() -> list[dict]:
    cues = json.loads((VIDEO / "cues.json").read_text(encoding="utf-8"))
    out, tabs = [], 0
    for s in cues["sfx"]:
        typ = s["type"]
        if typ == "bell":
            out.append({"t": s["t"], "type": "_bell", "gain": .55})
        elif typ == "tick":
            out.append({"t": s["t"], "type": "clock", "dur": .25, "interval": .25, "gain": .35})
        elif typ == "tab":
            out.append({"t": s["t"], "type": "land", "gain": .28, "pan": -.4 + .1 * tabs})
            tabs += 1
        else:
            out.append({**s, "type": SFX_MAP.get(typ, typ), "gain": {"whoosh": .4, "typing": .45, "chime": .5,
                                                                       "pop": .5, "click": .55, "shimmer": .35}.get(typ, .5)})
    return out


def service_bell(dur: float = 3.0) -> np.ndarray:
    """A brass desk bell: inharmonic partials, a bright strike and a long shimmer."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = 1318.5                                                           # E6
    y = np.zeros(n)
    for ratio, amp, tau in ((1.0, 1.0, 1.4), (2.32, .5, .7), (3.94, .3, .4), (5.43, .18, .25), (0.5, .12, 1.0)):
        y += amp * np.sin(2 * np.pi * f0 * ratio * t + 0.3 * np.sin(2 * np.pi * 4.2 * t)) * np.exp(-t / tau)
    y *= 1 - np.exp(-t / .0015)
    return (y / np.abs(y).max()).astype(np.float32)


def render_sfx() -> np.ndarray:
    lst = sfx_list()
    bells = [s for s in lst if s["type"] == "_bell"]
    dry, wet = cq.render_sfx([s for s in lst if s["type"] != "_bell"])
    for s in bells:
        y = service_bell()
        cq.place(dry, y, s["t"], s["gain"] * .5, .1)
        cq.place(wet, y, s["t"], s["gain"] * .4, .1)
    bus = dry + 0.45 * cq.convolve(wet, cq.make_ir(1.4, 2.5, "sfx", lp=9000))
    return cq.sos_filter(bus, "highpass", 60).astype(np.float32)


def master(music: np.ndarray, sfx: np.ndarray, voice: np.ndarray, target: float = -16.0, ceiling: float = -1.5):
    mix = music + sfx + voice
    g = cq.glue_gain(mix)
    fades = np.ones(N, np.float32)
    i0, i1 = int(158.4 * SR), int(159.9 * SR)                           # with the picture's fade to black
    fades[i0:i1] = ((0.5 + 0.5 * np.cos(np.linspace(0, np.pi, i1 - i0))) ** 1.5).astype(np.float32)
    fades[i1:] = 0
    total, gain = g * fades, 1.0
    for _ in range(4):
        y = mix * total * gain
        lim = cq.limiter_gain(y, ceiling - 0.3)
        L = cq.lufs_integrated(y * lim)
        print(f"  master: LUFS {L:6.2f}  gain {20 * np.log10(gain):+5.2f} dB  limiter GR {-20 * np.log10(lim.min()):4.1f} dB")
        if abs(L - target) < 0.1:
            break
        gain *= cq.db(target - L)
    k = total * gain * lim
    return music * k, sfx * k, voice * k


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-vst", action="store_true", help="plain stand-in instruments (structure check only)")
    ap.add_argument("--target", type=float, default=-16.0)
    a = ap.parse_args()
    t0 = time.time()
    sc = Score()
    sc.compose()
    print(f"composed: {len(sc.guitar)} guitar notes, {len(sc.bass)} bass notes")
    if a.no_vst:
        gtr, bass = stand_in(sc.guitar), stand_in([(n + 12, v, t, d) for n, v, t, d in sc.bass], .2)
    else:
        print("rendering guitar (Ample Guitar M Lite II) ...")
        gtr = render_instrument(GUITAR, sc.guitar, wait=8.0)
        print("rendering bass (MODO BASS 2) ...")
        bass = render_instrument(BASS, sc.bass, wait=2.0)
    for name, x in (("guitar", gtr), ("bass", bass)):
        pk = float(np.abs(x).max())
        print(f"  {name}: peak {20 * np.log10(pk + 1e-12):.1f} dBFS")
        if pk < 1e-4:
            print(f"  !! {name} is silent")
            return 3
    gtr = gtr / (np.abs(gtr).max() + 1e-9) * .5
    bass = bass / (np.abs(bass).max() + 1e-9) * .42
    dry = gtr + bass * .9
    send = cq.sos_filter(gtr + .15 * bass, "highpass", 220).astype(np.float32)
    wet = reverb(send) if not a.no_vst else cq.convolve(send, cq.make_ir(2.4, 4.0, "music", lp=8000))
    music = (dry + .32 * wet).astype(np.float32)

    print("voice + sfx ...")
    voice, man = voices()
    duck = cq.db(-6.0 * np.clip(envelope(voice, .08, .45) / .05, 0, 1)).astype(np.float32)
    music = music * duck
    sfx = render_sfx()
    sfx = sfx * cq.sfx_ride(music)
    print("mastering ...")
    m, s, v = master(music.astype(np.float64), sfx.astype(np.float64), voice.astype(np.float64), a.target)
    for name, x in (("music", m), ("sfx", s), ("voice", v), ("soundtrack", m + s + v)):
        cq.write_wav(str(HERE / f"{name}.wav"), x)
    print(f"wrote {HERE / 'soundtrack.wav'} ({DUR:.0f} s) in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
