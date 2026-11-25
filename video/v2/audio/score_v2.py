"""The v2.1 animatic's soundtrack: video/audio/score.py (v1) adapted to the v2 cue sheet. Same instruments (Ample Guitar M
Lite II, MODO BASS 2, Valhalla VintageVerb as a send, all hosted offline by DawDreamer), same mastering (glue, limiter,
integrated loudness to -16 LUFS) and ducking; new arrangement, sound effects and ambience from video/v2/cues.json.

  runtime/audio/.venv/Scripts/python video/v2/audio/score_v2.py            (a minute or two; Ample needs ~8 s to load)
  ... score_v2.py --no-vst      quick structural check with a plain synth stand-in (never ship this)

Writes video/v2/audio/{music,sfx,voice,soundtrack}.wav (48 kHz, the film's length from cues.json -> duration).

- Music: D major, 80 BPM (bar = 3 s), on a grid that puts a downbeat exactly on the tab change in scene 6
  (marks.tab_change: "the music builds, then releases on the click and the tab change"). Sections follow cues.json ->
  music: silent through scene 1; enters after the bell (handover); walking pace for Monday; thins under "Who's got too
  much on this week?"; builds from the code to the click; releases on the tab change; settles for Priya; brighter in
  Lisbon; resolves with the bell and the titles.
- Sound effects and ambience follow cues.json -> sfx. Everything is synthesised (numpy/scipy) with the helpers in
  video/audio/compose.quorum.py: the brass bell (as v1), mouse and tab clicks, a key turning in a lock, the stand's
  clamp clunk, keyboard foley, the lamp switch, the key's metal tap, rain, the 2009 PC's fan and hard drive, a radio far
  off, workshop and street beds. Rough by design: placeholders for recorded sound.
- Voices from video/v2/audio/voice/manifest.json (voices.py). Off-screen lines (Martin from the workshop, the two
  goodnights from the door) are pushed back: high-cut and more room. Music ducks -6 dB under speech, ambience -3 dB.
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
V2 = HERE.parent
VIDEO = V2.parent
CUES = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))
MARK = CUES["marks"]
SR, BLOCK = 48000, 512
DUR = float(CUES["duration"])
N = int(SR * DUR)

_spec = importlib.util.spec_from_file_location("cq", VIDEO / "audio" / "compose.quorum.py")
cq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cq)
cq.DUR, cq.N = DUR, N
cq.T = np.arange(N, dtype=np.float64) / SR

PLUGINS = Path(r"X:\VST Plugins")
GUITAR = PLUGINS / "VST2" / "AGML2.dll"
BASS = PLUGINS / "VST3" / "MODO BASS 2.vst3"
VERB = PLUGINS / "VST3" / "ValhallaVintageVerb.vst3"

BPM = 80
BEAT = 60 / BPM
BAR = 4 * BEAT
LIFT = MARK["tab_change"]
GRID0 = LIFT - BAR * np.floor(LIFT / BAR)           # a bar line exactly on the tab change


def bar(k: float) -> float:
    return GRID0 + k * BAR


def bar_at(t: float, early: float = .15) -> int:
    """First bar starting at or after t (allowing a bar line up to `early` bars before)."""
    return int(np.ceil((t - GRID0) / BAR - early))


SEC = {m["section"]: m["t"] for m in CUES["music"]}

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


def plan() -> list[tuple[int, list[str], str]]:
    """(first bar, chords one per bar, style), from the music sections in cues.json."""
    kH = bar_at(SEC["handover"])
    kW = bar_at(SEC["work"])
    k5 = bar_at(CUES["scenes"][4]["start"])
    kQ = bar_at(SEC["before_build"])
    kB = bar_at(SEC["build"])
    kL = bar_at(SEC["lift"], early=0)
    kT = bar_at(SEC["tuesday"])
    kS = bar_at(SEC["lisbon"] + 1.5)                    # the street first, then the music
    kC = bar_at(SEC["close"])
    assert kB + 8 == kL, f"build must be 8 bars into the lift (bars {kB}..{kL})"
    cyc = lambda seq, n: [seq[i % len(seq)] for i in range(n)]
    return [
        (kH, cyc(["D", "A/C#", "Bm7", "Gmaj7", "D/F#"], kW - 3 - kH), "pick_soft"),   # handover: sparse, warm
        (kW - 3, ["Asus4"], "hold"),                                                  # rings under the key and the lamp
        (kW - 1, ["D"], "breath"),                                                    # daylight: the time-lapse
        (kW, cyc(["D", "G", "Bm", "A"], k5 - kW), "pick"),                            # Monday: walking pace
        (k5, cyc(["D", "G", "Bm", "A"], kQ - k5), "pick_plus"),                       # the montage: a little more forward
        (kQ, cyc(["Bm", "G", "D", "A"], kB - kQ), "pick_soft"),                       # under the question: thinner
        (kB, ["Bm", "Bm/A", "G", "G/F#", "Em7", "Em/D", "Asus4", "A"], "build"),      # the code -> the click
        (kL, cyc(["D", "A/C#", "Bm", "G"], kT - kL), "strum"),                        # release: the tab change
        (kT, cyc(["D", "G", "Bm", "A"], kS - kT), "pick_soft"),                       # Priya: settles
        (kS, cyc(["D", "A/C#", "Bm", "G"], kC - kS), "strum_full"),                   # Lisbon: brighter, fuller
    ]


class Score:
    def __init__(self, seed: int = 11):
        self.rng = np.random.default_rng(seed)
        self.guitar: list[tuple[int, int, float, float]] = []
        self.bass: list[tuple[int, int, float, float]] = []

    def _h(self, t, ms=7):
        return max(0.0, t + self.rng.normal(0, ms / 1000))

    def _v(self, v, spread=6):
        return int(np.clip(v + self.rng.normal(0, spread), 1, 127))

    def g(self, note, vel, t, dur, ms=7):
        self.guitar.append((note, self._v(vel), self._h(t, ms), dur))

    def b(self, note, vel, t, dur):
        self.bass.append((note, self._v(vel, 4), self._h(t, 5), dur))

    def roll(self, ch, vel, t, dur, step=.09, top=None):
        v = CH[ch][0] if top is None else CH[ch][0] + [top]
        for i, n in enumerate(v):
            self.g(n, vel - 2 * i, t + i * step, dur, ms=2)

    def strum(self, notes, vel, t, dur, up=False, spread=.014):
        seq = notes[::-1][:4] if up else notes
        for i, n in enumerate(seq):
            self.g(n, vel * (0.78 if up else 1.0) * (0.92 + 0.08 * (i == 0)), t + i * spread, dur, ms=3)

    def bar_pick(self, k, ch, base=56, fill=True):
        v, root = CH[ch]
        t0 = bar(k)
        thumb = [v[0], v[1] if len(v) > 4 else v[0], v[0], v[1]]
        fingers = [v[-1], v[-2], v[-1], v[-3]] if base > 50 else [v[-2], v[-1], v[-2], v[-3]]
        for bt in range(4):
            self.g(thumb[bt], base + 6 * (bt == 0), t0 + bt * BEAT, 1.6)
            self.g(fingers[bt], base - 8 + 4 * (bt == 2), t0 + bt * BEAT + BEAT / 2, 1.2)
        if fill and k % 4 == 3:
            self.g(v[-1] + 2 if v[-1] + 2 <= 76 else v[-2], base - 10, t0 + 3.5 * BEAT + BEAT / 4, .5)

    def bass_walk(self, k, ch, nxt, vel=70):
        v, root = CH[ch]
        t0 = bar(k)
        self.b(root, vel, t0, BEAT * 1.8)
        self.b(root + 7, vel - 10, t0 + 2 * BEAT, BEAT * .9)
        if nxt:
            r2 = CH[nxt][1]
            step = 1 if r2 > root else -1
            self.b(r2 - step * (1 if abs(r2 - root) > 2 else 0) if r2 != root else root + 4, vel - 14, t0 + 3.5 * BEAT, BEAT * .45)

    def bar_build(self, k, ch, idx):
        v, root = CH[ch]
        t0 = bar(k)
        sub = 4 if idx >= 6 else 2
        steps = 4 * sub
        order = [0, 2, 3, 4, 1, 3, 2, 4] if sub == 2 else [0, 2, 3, 4, 3, 2, 1, 3, 4, 3, 2, 4, 3, 4, 2, 4]
        for e in range(steps):
            n = v[order[e % len(order)] % len(v)]
            self.g(n, 42 + idx * 4 + 6 * (e % sub == 0), t0 + e * BAR / steps, 0.9 if sub == 2 else .45)
        if idx >= 1:
            for e in range(8):
                self.b(root + (12 if e % 4 == 3 and idx >= 4 else 0), 60 + idx * 4, t0 + e * BEAT / 2, BEAT / 2 * .85)
        else:
            self.b(root, 64, t0, BAR * .95)

    def bar_strum(self, k, ch, full=False):
        v, root = CH[ch]
        t0 = bar(k)
        pattern = [(0, False, 1.0), (2, False, .85), (3, True, .7), (5, True, .7), (6, False, .85), (7, True, .65)]
        base = 68 if full else 60
        for e, up, acc in pattern:
            self.strum(v, base * acc + (8 if e == 0 else 0), t0 + e * BEAT / 2, 1.0 if not up else .6, up)
        if full:
            for e in (1, 4):
                self.g(min(v[-1] + 12, 76), 42, t0 + e * BEAT / 2, .9)
        self.b(root, 78 if full else 72, t0, BEAT * 1.4)
        self.b(root + 7, 64, t0 + 1.5 * BEAT, BEAT * .45)
        self.b(root + 12 if root + 12 <= 50 else root, 68, t0 + 2 * BEAT, BEAT * .9)
        self.b(root, 60, t0 + 3 * BEAT, BEAT * .45)
        self.b(root + (2 if root + 2 <= 50 else -1), 56, t0 + 3.5 * BEAT, BEAT * .45)

    def compose(self):
        # the bell rings at bell_arrive; the guitar enters just after it with one slow roll, then the picking
        self.roll("D", 46, SEC["handover"] + .35, 4.0, step=.11)
        for first, chords, style in plan():
            for i, ch in enumerate(chords):
                k = first + i
                nxt = chords[i + 1] if i + 1 < len(chords) else None
                if style == "pick_soft":
                    self.bar_pick(k, ch, base=46)
                    if i >= 2:
                        self.b(CH[ch][1], 50 + min(6, 2 * i), bar(k), BAR * .95)
                elif style == "hold":
                    self.roll(ch, 44, bar(k) + .1, 6.0, step=.1)
                    self.b(CH[ch][1], 48, bar(k), 4.0)
                elif style == "breath":
                    self.roll(ch, 42, bar(k) + .2, 3.6, step=.09)
                elif style == "pick":
                    self.bar_pick(k, ch)
                    self.bass_walk(k, ch, nxt)
                elif style == "pick_plus":
                    self.bar_pick(k, ch, base=58)
                    self.bass_walk(k, ch, nxt, vel=74)
                    self.g(min(CH[ch][0][-1] + 12, 76), 40, bar(k) + 2.5 * BEAT, .6)
                elif style == "build":
                    self.bar_build(k, ch, i)
                elif style in ("strum", "strum_full"):
                    self.bar_strum(k, ch, full=style == "strum_full")
        # the close: a held Asus4 under the goodnights, G as we cut to Lisbon, A for the two desks; the bell; then
        # the final Dadd9 with the title, a soft re-roll under "Even the old ones." and a last one with the credit
        kC = bar_at(SEC["close"])
        self.roll("Asus4", 42, bar(kC) + .1, 4.2, step=.1)
        self.b(CH["Asus4"][1], 50, bar(kC), 3.8)
        self.roll("Gmaj7", 40, MARK["lisbon_night"] + .15, 4.0, step=.1)
        self.b(CH["Gmaj7"][1], 48, MARK["lisbon_night"] + .1, 3.6)
        self.roll("Asus4", 40, MARK["two_desks"] + .05, 3.0, step=.08)
        self.b(CH["Asus4"][1], 50, MARK["two_desks"], 2.6)
        fin = MARK["title"]
        for i, n in enumerate(CH["Dadd9"][0]):
            self.g(n, 74 - 3 * i, fin + i * .11, 9.0, ms=2)
        self.b(38, 68, fin, 8.0)
        for i, n in enumerate([62, 66, 69, 74]):
            self.g(n, 58 - 3 * i, MARK["old_ones"] + i * .14, 6.0, ms=0)
        for i, n in enumerate([57, 62, 66, 69, 74]):
            self.g(n, 56 - 3 * i, MARK["credit"] + i * .16, 5.0, ms=0)
        self.b(38, 52, MARK["credit"], 4.0)


# ── rendering (as v1) ──
def render_instrument(path: Path, notes, wait: float = 0.0) -> np.ndarray:
    import dawdreamer as daw
    engine = daw.RenderEngine(SR, BLOCK)
    p = engine.make_plugin_processor("inst", str(path))
    for n, v, t, d in notes:
        if t < DUR:
            p.add_midi_note(int(n), int(v), float(t), float(min(d, DUR - t)))
    engine.load_graph([(p, [])])
    if wait:
        time.sleep(wait)
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
    v.set_parameter(0, 1.0)
    v.set_parameter(2, 0.30)
    v.set_parameter(1, 0.30)
    engine.load_graph([(src, []), (v, ["src"])])
    engine.render(DUR)
    a = engine.get_audio().astype(np.float32)
    out = np.zeros((2, N), np.float32)
    out[:, :min(N, a.shape[1])] = a[:2, :N]
    return out


def stand_in(notes, bright: float = .45) -> np.ndarray:
    out = cq.bus()
    for n, v, t, d in notes:
        y = cq.pluck(n, t60=min(2.0, d + .4), dur=min(2.5, d + .5), bright=bright)
        cq.place(out, y, t, (v / 127) * .25)
    return out


def envelope(x: np.ndarray, attack: float, release: float) -> np.ndarray:
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


# ── voices ──
OFFSCREEN = {1: .85, 51: .6, 53: .6}                   # cue line -> how far off (o.s. in the script)


def voices() -> np.ndarray:
    man = json.loads((HERE / "voice" / "manifest.json").read_text(encoding="utf-8"))
    from scipy.signal import resample_poly
    out, far = cq.bus(), cq.bus()
    for i, line in enumerate(man, 1):
        y, sr = sf.read(HERE / line["file"], dtype="float32", always_2d=True)
        if sr != SR:
            y = resample_poly(y, SR // np.gcd(SR, sr), sr // np.gcd(SR, sr), axis=0).astype(np.float32)
        mono = y.mean(1)
        rms = np.sqrt((mono[np.abs(mono) > 1e-3] ** 2).mean() + 1e-12)
        mono = mono * (0.1 / rms)
        pan = {"Barnaby": 0.0, "Martin": -0.12, "Theo": -0.1, "Priya": 0.12}.get(line["who"], 0.0)
        if i in OFFSCREEN:
            d = OFFSCREEN[i]
            mono = cq.sos_filter(mono, "lowpass", 5200 - 2400 * d).astype(np.float32)
            cq.place(out, mono, float(line["t"]), cq.db(-3.5 * d), pan - .25 * d)
            cq.place(far, mono, float(line["t"]), .55 * d, pan)
        else:
            cq.place(out, mono, float(line["t"]), 1.0, pan)
            cq.place(far, mono, float(line["t"]), .07, pan)
    far = cq.sos_filter(far, "highpass", 220).astype(np.float32)
    room = cq.convolve(far, cq.make_ir(0.55, 1.2, "office", lp=6000, predelay=.008)) * .5
    out = out + room.astype(np.float32)
    pk = float(np.abs(out).max())
    return out * cq.limiter_gain(out, 20 * np.log10(pk) - 6.0)


# ── sound effects ──
def rng(*k):
    return cq.rng_for("v2", *k)


def noise(n, seed, kind="white"):
    r = rng("noise", seed, n)
    x = r.standard_normal(n)
    if kind == "white":
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X *= 1 / np.sqrt(f) if kind == "pink" else 1 / f
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return (1 - np.exp(-t / max(a, 1e-4))) * np.exp(-t / d)


def ping(freqs, taus, dur, amps=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    amps = amps or [1.0] * len(freqs)
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau) for f, tau, a in zip(freqs, taus, amps))
    return cq.fade(y * (1 - np.exp(-t / .0008)), .0002, .01)


def burst(dur, lo, hi, tau, seed):
    n = int(dur * SR)
    y = cq.sos_filter(rng("burst", seed, dur).standard_normal(n), "bandpass", [lo, hi]) * env_ad(n, .0005, tau)
    return y / (np.abs(y).max() + 1e-9)


def service_bell(dur=3.0):
    """v1's brass desk bell: inharmonic partials, a bright strike and a long shimmer."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, amp, tau in ((1.0, 1.0, 1.4), (2.32, .5, .7), (3.94, .3, .4), (5.43, .18, .25), (0.5, .12, 1.0)):
        y += amp * np.sin(2 * np.pi * 1318.5 * ratio * t + 0.3 * np.sin(2 * np.pi * 4.2 * t)) * np.exp(-t / tau)
    y *= 1 - np.exp(-t / .0015)
    return (y / np.abs(y).max()).astype(np.float32)


def key_turn(seed):
    """A key going into a lock and turning: a scrape, two tumbler ticks, the bolt's clack."""
    out = np.zeros(int(.75 * SR))
    sc = burst(.16, 2500, 7000, .05, seed) * .35
    out[: len(sc)] += sc
    for k, at in enumerate((.22, .3)):
        c = burst(.03, 3000, 8000, .004, seed + k) * .6
        i = int(at * SR); out[i:i + len(c)] += c
    cl = ping([1650, 2480, 3900], [.05, .035, .02], .25, [1, .6, .4]) * .8
    th = np.sin(2 * np.pi * np.cumsum(90 + 120 * np.exp(-np.arange(int(.2 * SR)) / SR / .02)) / SR) * env_ad(int(.2 * SR), .001, .05)
    i = int(.46 * SR); out[i:i + len(cl)] += cl; out[i:i + len(th)] += .7 * th
    return out / np.abs(out).max()


def clunk(seed):
    """The repair stand's clamp releasing: a heavy metal clunk and a short ring, heard through the doorway."""
    y, _ = cq.fx_thunk(seed)
    r = ping([780, 1310, 2140, 3020], [.18, .12, .08, .05], .8, [.6, .4, .3, .15])
    n = max(len(y), len(r))
    out = np.zeros(n); out[: len(y)] += y; out[: len(r)] += .45 * r
    return cq.sos_filter(out, "lowpass", 5000) / (np.abs(out).max() + 1e-9)


def key_tap(seed):
    """The key on the keyboard: a small, clean metal tap on plastic."""
    m = ping([2850, 4120, 6300, 7900], [.06, .045, .03, .02], .3, [1, .6, .35, .2])
    p = burst(.02, 1500, 5000, .003, seed) * .5
    m[: len(p)] += p
    return m / np.abs(m).max()


def lamp_click(seed):
    out = np.zeros(int(.25 * SR))
    for k, (at, fc) in enumerate(((0, 2600), (.07, 3400))):
        c = burst(.04, fc * .6, fc * 1.5, .005, seed + k)
        th = np.sin(2 * np.pi * 160 * np.arange(len(c)) / SR) * env_ad(len(c), .0005, .012)
        i = int(at * SR); out[i:i + len(c)] += (1 - .4 * k) * (c + .6 * th)
    return out / np.abs(out).max()


def keys_jingle(seed):
    r = rng("jingle", seed)
    out = np.zeros(int(1.2 * SR))
    for k in range(9):
        p = ping(list(r.uniform(2500, 7000, 3)), list(r.uniform(.03, .12, 3)), .4, list(r.uniform(.3, 1, 3)))
        i = int(r.uniform(0, .7) * SR); out[i:i + len(p)] += r.uniform(.3, 1) * p
    return out / np.abs(out).max()


def hdd(dur, seed):
    """2009 hard drive chatter: seek clicks with a small resonant thunk, irregular."""
    r = rng("hdd", seed, dur)
    out = np.zeros(int((dur + .1) * SR))
    t = 0.0
    while t < dur:
        c = burst(.012, 1800, 6000, .0025, int(t * 1000) + seed) * r.uniform(.3, 1)
        th = np.sin(2 * np.pi * r.uniform(180, 320) * np.arange(len(c)) / SR) * env_ad(len(c), .0003, .004)
        i = int(t * SR); out[i:i + len(c)] += c + .4 * th
        t += r.choice([.018, .025, .04, .06, .11, .2], p=[.25, .25, .2, .15, .1, .05])
    return out / (np.abs(out).max() + 1e-9)


def freewheel(seed, dur=2.6):
    """A freewheel ticking down: pawl clicks slowing."""
    r = rng("fw", seed)
    out = np.zeros(int((dur + .1) * SR))
    t, rate = 0.0, 26.0
    while t < dur:
        c = burst(.006, 3000, 7500, .0015, int(t * 997) + seed) * r.uniform(.6, 1) * (1 - t / dur)
        i = int(t * SR); out[i:i + len(c)] += c
        t += 1 / rate
        rate = max(6.0, rate * .975)
    return out / (np.abs(out).max() + 1e-9)


def compressor(seed, dur=2.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((50, 1), (100, .6), (150, .35), (300, .15)))
    hiss = cq.sos_filter(noise(n, seed), "bandpass", [600, 3000]) * .25
    e = np.minimum(1, t / .25) * np.minimum(1, (dur - t) / .4)
    y = cq.sos_filter((hum + hiss) * e, "lowpass", 2500)
    return y / (np.abs(y).max() + 1e-9)


def rain_bed(n, seed):
    """Rain on a window: hiss, droplets, a low wash; stereo."""
    out = np.zeros((2, n))
    for ch in range(2):
        hiss = cq.sos_filter(noise(n, seed + ch, "pink"), "bandpass", [500, 6500]) * .5
        wash = cq.sos_filter(noise(n, seed + 10 + ch, "brown"), "lowpass", 300) * .5
        r = rng("drops", seed, ch)
        drops = np.zeros(n)
        for _ in range(int(n / SR * 28)):
            d = burst(.008, 2000, 7000, r.uniform(.0015, .004), int(r.integers(1 << 30)))
            i = int(r.integers(0, n - len(d)))
            drops[i:i + len(d)] += r.uniform(.05, .35) * d
        am = 1 + .18 * np.sin(2 * np.pi * (.07 + .02 * ch) * np.arange(n) / SR + ch)
        out[ch] = (hiss + wash + drops) * am
    return out / np.abs(out).max()


def fan_bed(n, seed, spinup=1.6):
    t = np.arange(n) / SR
    f = 30 + 85 * np.minimum(1, t / spinup) ** .7
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = np.sin(ph) + .4 * np.sin(2 * ph) + .15 * np.sin(3 * ph)
    air = cq.sos_filter(noise(n, seed, "pink"), "bandpass", [250, 2200])
    e = np.minimum(1, t / spinup)
    y = .25 * hum * e + .9 * air * (.3 + .7 * e)
    return y / np.abs(y).max()


def radio_bed(n, seed):
    """A radio far off: a little tune and a presenter's murmur through a small speaker, in another room."""
    out = np.zeros(n)
    r = rng("radio", seed)
    prog = [(55, [67, 71, 74]), (60, [64, 67, 72]), (62, [66, 69, 74]), (55, [67, 71, 74])]
    beat = .5
    t, k = 0.3, 0
    while t < n / SR - 1:
        root, tri = prog[(k // 8) % 4]
        note = tri[r.integers(0, 3)] + (12 if r.random() < .2 else 0)
        y = cq.pluck(note, t60=.6, dur=.7, bright=.5)
        i = int(t * SR); m = min(len(y), n - i); out[i:i + m] += .5 * y[:m]
        if k % 4 == 0:
            yb = cq.pluck(root - 12, t60=1.2, dur=1.4, bright=.3)
            m = min(len(yb), n - i); out[i:i + m] += .45 * yb[:m]
        t += beat; k += 1
    talk = cq.sos_filter(noise(n, seed + 3), "bandpass", [300, 2500])
    syl = (np.sin(2 * np.pi * 4.3 * np.arange(n) / SR + 2 * np.sin(2 * np.pi * .7 * np.arange(n) / SR)) > .2) * 1.0
    seg = (np.sin(2 * np.pi * .05 * np.arange(n) / SR) > .55) * 1.0     # the presenter, now and then
    out = out + .35 * talk * cq.sos_filter(syl, "lowpass", 30) * seg
    out = cq.sos_filter(out, "bandpass", [350, 3200])
    return out / np.abs(out).max()


def room_bed(n, seed, busy=1.0):
    """Workshop room tone with tools now and then (busy scales the activity)."""
    y = cq.sos_filter(noise(n, seed, "brown"), "lowpass", 250) * .6
    r = rng("room", seed)
    t = r.uniform(.5, 2)
    while t < n / SR - 1:
        p = ping(list(r.uniform(900, 4200, 3)), list(r.uniform(.05, .3, 3)), .6, list(r.uniform(.2, 1, 3)))
        i = int(t * SR); y[i:i + len(p)] += r.uniform(.08, .25) * p
        t += r.uniform(1.5, 4.5) / busy
    return y / np.abs(y).max()


def street_bed(n, seed, night=False):
    """Below a Lisbon window: traffic swells, a distant voice or two, gulls (day); sparser at night."""
    t = np.arange(n) / SR
    rumble = cq.sos_filter(noise(n, seed, "brown"), "lowpass", 220)
    r = rng("street", seed, night)
    swell = np.zeros(n) + .35
    for _ in range(int(n / SR / (9 if night else 4))):
        c = r.uniform(0, n / SR); w = r.uniform(2, 4)
        swell += np.exp(-((t - c) / w) ** 2) * r.uniform(.4, 1)
    y = rumble * swell
    if not night:
        for _ in range(int(n / SR / 6)):
            c = r.uniform(0, n / SR - 1)
            g = np.sin(2 * np.pi * np.cumsum(np.linspace(1500, 1100, int(.25 * SR))) / SR) * env_ad(int(.25 * SR), .02, .08)
            i = int(c * SR); y[i:i + len(g)] += .08 * g
        talk = cq.sos_filter(noise(n, seed + 5), "bandpass", [400, 2000]) * (np.sin(2 * np.pi * 3.7 * t) > .3) * (np.sin(2 * np.pi * .04 * t) > .6)
        y += .06 * talk
    return y / np.abs(y).max()


def bed(typ, n, seed):
    if typ == "rain":
        return rain_bed(n, seed)
    if typ == "fan":
        return fan_bed(n, seed)
    if typ == "radio":
        return radio_bed(n, seed)
    if typ == "workshop":
        y = room_bed(n, seed, 1.0); rd = radio_bed(n, seed + 1)
        return y + .5 * rd
    if typ == "bustle":
        y = room_bed(n, seed, 2.2); rd = radio_bed(n, seed + 2)
        return y + .45 * rd
    if typ == "street":
        return street_bed(n, seed)
    if typ == "street_night":
        return street_bed(n, seed, night=True)
    raise ValueError(typ)


# ambience levels as RMS (pre-master; the voices sit near -20 dBFS RMS): rain -32 dB, fan -41, radio -44, workshop -38,
# Tuesday bustle -36, Lisbon street -35, the quieter street at night -40
BED_GAIN = {"rain": .024, "fan": .009, "radio": .006, "workshop": .0125, "bustle": .016, "street": .018, "street_night": .01}
BED_LP = {"radio": 2600, "workshop": 6000, "bustle": 7000, "rain": 7000}


def render_sfx() -> tuple[np.ndarray, np.ndarray]:
    """Returns (sfx, ambience) stereo buses."""
    dry, wet = cq.bus(), cq.bus()
    amb = cq.bus()
    ir_far = cq.make_ir(1.1, 2.0, "workshop", lp=5000, predelay=.02)
    far = cq.bus()
    for k, s in enumerate(CUES["sfx"]):
        typ, t = s["type"], float(s["t"])
        g = float(s.get("gain", .5))
        pan = float(s.get("pan", 0.0))
        if typ in BED_GAIN:
            until = float(s.get("until", DUR))
            fi, fo = float(s.get("fade_in", 1.0)), 1.6
            n = int((until - t) * SR)
            y = bed(typ, n, k)
            if typ in BED_LP:
                y = cq.sos_filter(y, "lowpass", BED_LP[typ])
            y = cq.sos_filter(y, "highpass", 45)                     # brown noise is mostly sub-audio: measure what is heard
            y = y / (np.sqrt((y ** 2).mean()) + 1e-12)              # beds are set by RMS, not peak
            e = np.minimum(1, np.arange(n) / SR / fi) * np.minimum(1, (until - t - np.arange(n) / SR) / fo)
            y = y * e * BED_GAIN[typ] * float(s.get("level", 1.0))
            if y.ndim == 1:
                y = np.stack([y, np.roll(y, int(.0011 * SR))])
            cq.place(amb, y.astype(np.float32), t, 1.0)
            continue
        if typ == "bell":
            y = service_bell()
            cq.place(dry, y, t, g * .38, .1); cq.place(wet, y, t, g * .35, .1)
        elif typ == "bell_soft":
            y = cq.sos_filter(service_bell(2.2), "lowpass", 5000)
            cq.place(dry, y, t, g * .4, .05); cq.place(wet, y, t, g * .5, .05)
        elif typ in ("tab", "tab_close", "mouse_click"):
            y, _ = cq.fx_click(k)
            gg = {"tab": .32, "tab_close": .26, "mouse_click": 1.0}[typ] * (g if typ == "mouse_click" else 1)
            cq.place(dry, y, t, gg * .6, pan); cq.place(wet, y, t, gg * .08, pan)
        elif typ == "hdd":
            y = hdd(float(s.get("dur", .5)), k)
            cq.place(dry, cq.sos_filter(y, "lowpass", 6000), t, .09, -.3)
        elif typ == "key_tap":
            y = key_tap(k); cq.place(dry, y, t, g * .55, .05); cq.place(wet, y, t, g * .2, .05)
        elif typ == "lamp_click":
            y = lamp_click(k); cq.place(dry, y, t, g * .55, -.35); cq.place(wet, y, t, g * .12, -.35)
        elif typ == "key_turn":
            y = key_turn(k); cq.place(dry, y, t, g * .6, .2); cq.place(wet, y, t, g * .15, .2)
        elif typ == "clunk":
            y = clunk(k); cq.place(far, y, t, g * .7, .35); cq.place(dry, y, t, g * .25, .35)
        elif typ == "freewheel":
            y = freewheel(k); cq.place(far, y, t, g * .5, .4)
        elif typ == "compressor":
            y = compressor(k); cq.place(far, y, t, g * .5, .45)
        elif typ == "keys_jingle":
            y = keys_jingle(k); cq.place(far, y, t, g * .5, -.3)
        elif typ == "typing":
            y, _ = cq.fx_typing(float(s.get("dur", 2.0)), k)
            cq.place(dry, cq.sos_filter(y, "lowpass", 7000), t, g * .4, -.05); cq.place(wet, y, t, g * .05, -.05)
        elif typ == "keys_modern":
            y, _ = cq.fx_typing(float(s.get("dur", 1.0)), k + 50)
            cq.place(dry, y, t, g * .35, .1)
        elif typ == "reload":
            y = hdd(.45, k); cq.place(dry, cq.sos_filter(y, "lowpass", 6000), t, g * .5, -.3)
        elif typ == "step":
            y = cq.fx_tick(False, k); cq.place(dry, y, t, g * .25, 0)
        elif typ in ("pop", "ding", "timelapse"):
            sub = {"pop": [{"t": t, "type": "pop", "gain": g, "f": 620}],
                   "ding": [{"t": t, "type": "ding", "gain": g}],
                   "timelapse": [{"t": t + float(s.get("dur", 2.0)) * .6, "type": "whoosh", "dur": float(s.get("dur", 2.0)), "f0": 200, "f1": 2500, "peak": .6, "gain": g}]}[typ]
            d2, w2 = cq.render_sfx(sub)
            dry += d2; wet += w2
        else:
            print("  ! unknown sfx type", typ)
    # the IRs carry most of their energy below ~1 kHz, so a low thump or hum would be boosted ~12 dB: high-pass the sends
    wet = cq.sos_filter(wet, "highpass", 200).astype(np.float32)
    farw = cq.sos_filter(far, "highpass", 180).astype(np.float32)
    sfx = dry + 0.45 * cq.convolve(wet, cq.make_ir(1.4, 2.5, "sfx", lp=9000)) + 0.3 * cq.convolve(farw, ir_far) + .3 * far
    sfx = cq.sos_filter(sfx, "highpass", 60).astype(np.float32)
    return sfx, cq.sos_filter(amb, "highpass", 40).astype(np.float32)


def master(music, sfx, voice, target=-16.0, ceiling=-1.5):
    mix = music + sfx + voice
    g = cq.glue_gain(mix)
    fades = np.ones(N, np.float32)
    i0, i1 = int(MARK["fade_out"] * SR), min(N, int(MARK["end"] * SR) - 1)
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
    ap.add_argument("--no-vst", action="store_true")
    ap.add_argument("--target", type=float, default=-16.0)
    a = ap.parse_args()
    t0 = time.time()
    print(f"film {DUR:.2f} s; grid: bar 0 at {GRID0:.2f} s, lift bar line at {LIFT:.2f} s")
    for first, chords, style in plan():
        print(f"  bars {first:3d}-{first + len(chords) - 1:3d}  {bar(first):7.2f}-{bar(first + len(chords)):7.2f}  {style:10} {' '.join(chords)}")
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
    music = (dry + .32 * wet).astype(np.float32) * .8           # v2 is a dialogue film: the score sits lower than v1's

    print("voice + sfx + ambience ...")
    voice = voices()
    venv = np.clip(envelope(voice, .08, .45) / .05, 0, 1)
    music = music * cq.db(-6.0 * venv).astype(np.float32)
    sfx, amb = render_sfx()
    sfx = sfx + amb * cq.db(-3.0 * venv).astype(np.float32)
    print("mastering ...")
    m, s, v = master(music.astype(np.float64), sfx.astype(np.float64), voice.astype(np.float64), a.target)
    for name, x in (("music", m), ("sfx", s), ("voice", v), ("soundtrack", m + s + v)):
        cq.write_wav(str(HERE / f"{name}.wav"), x)
    print(f"wrote {HERE / 'soundtrack.wav'} ({DUR:.2f} s) in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
