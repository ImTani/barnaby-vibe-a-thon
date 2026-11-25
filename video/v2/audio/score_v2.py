"""The film's soundtrack: video/audio/score.py (v1) adapted to the v2 cue sheet, with recorded foley and ambience.
Music on Ample Guitar M Lite II, MODO BASS 2 and Valhalla VintageVerb (a send), all hosted offline by DawDreamer; sound
effects and ambience from the Ableton Live 12 Suite Core Library (foley.py); voices from voice/manifest.json; one mix
and master (glue, true-peak limiter, -16 LUFS integrated, <= -1 dBTP, 48 kHz stereo).

  runtime/audio/.venv/Scripts/python video/v2/audio/score_v2.py            (a minute or two; Ample needs ~8 s to load)
  ... score_v2.py --no-vst      quick structural check with a plain synth stand-in (never ship this)
  ... score_v2.py --fresh       re-render the instruments even if the cached render matches the notes

Writes video/v2/audio/soundtrack.wav and its stems {music,sfx,ambience,voice}.wav (48 kHz, cues.json -> duration; the
stems sum to the soundtrack). The instrument renders are cached under .cache/audio/music/ (keyed by the notes).

- Music: D major, 80 BPM (bar = 3 s), on a grid that puts a downbeat exactly on the tab change in scene 6
  (marks.tab_change: "the music builds, then releases on the click and the tab change"). Sections follow cues.json ->
  music: silent through scene 1; enters after the bell (handover); walking pace for Monday; thins under "Who's got too
  much on this week?"; builds from the code to the click; releases on the tab change; settles for Priya; brighter in
  Lisbon; resolves with the bell and the titles. The run prints each section's cue time against its bar line.
- Sound effects and ambience follow cues.json -> sfx (foley.py; sources and processing in SOUND.md).
- Voices from video/v2/audio/voice/manifest.json (video/audio/voices.py, which also takes recorded lines via --takes).
  Off-screen lines (Martin from the workshop, the two goodnights from the door) are pushed back: high-cut and more
  room. Under speech (60 ms look-ahead) the music ducks -8 dB (up to 4 dB more where it runs hot) with a further -3 dB
  presence dip around 2.5 kHz, the ambience -4 dB and the effects -2 dB; the score steps back for the key turning, the
  click and the last bell.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d

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

import foley  # noqa: E402  (after cq is set up; foley loads its own copy)

MUSIC_CACHE = V2.parents[1] / ".cache" / "audio" / "music"

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
    # the build climbs bar by bar to the click; since the 3:38 lock it has 7 bars (the code mark moved later), so the
    # Em/D passing bar goes and the climb keeps its top (see compose: the last two bars still run in sixteenths)
    build = {8: ["Bm", "Bm/A", "G", "G/F#", "Em7", "Em/D", "Asus4", "A"],
             7: ["Bm", "Bm/A", "G", "G/F#", "Em7", "Asus4", "A"]}
    assert kL - kB in build, f"the build must be 7 or 8 bars into the lift (bars {kB}..{kL})"
    cyc = lambda seq, n: [seq[i % len(seq)] for i in range(n)]
    return [
        (kH, cyc(["D", "A/C#", "Bm7", "Gmaj7", "D/F#"], kW - 3 - kH), "pick_soft"),   # handover: sparse, warm
        (kW - 3, ["Asus4"], "hold"),                                                  # rings under the key and the lamp
        (kW - 1, ["D"], "breath"),                                                    # daylight: the time-lapse
        (kW, cyc(["D", "G", "Bm", "A"], k5 - kW), "pick"),                            # Monday: walking pace
        (k5, cyc(["D", "G", "Bm", "A"], kQ - k5), "pick_plus"),                       # the montage: a little more forward
        (kQ, cyc(["Bm", "G", "D", "A"], kB - kQ), "pick_soft"),                       # under the question: thinner
        (kB, build[kL - kB], "build"),                                                # the code -> the click
        (kL, cyc(["D", "A/C#", "Bm", "G"], kT - kL - 1), "strum"),                    # release: the tab change
        (kT - 1, cyc(["D", "A/C#", "Bm", "G"], kT - kL)[-1:], "ring"),                # one strum rings over the cut
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
                    self.bar_build(k, ch, i if i < 4 else i + 8 - len(chords))     # the climb keeps its top
                elif style == "ring":
                    self.strum(CH[ch][0], 58, bar(k), 4.2)
                    self.b(CH[ch][1], 62, bar(k), 3.4)
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
def render_instrument(path: Path, notes, wait: float = 0.0, fresh: bool = False) -> np.ndarray:
    key = hashlib.sha1(repr((str(path), path.stat().st_mtime_ns, DUR, SR, [(int(n), int(v), round(t, 5), round(d, 5))
                                                                         for n, v, t, d in notes])).encode()).hexdigest()[:16]
    c = MUSIC_CACHE / f"{path.stem}-{key}.npy"
    if c.exists() and not fresh:
        print(f"  (cached render {c.name})")
        return np.load(c)
    out = _render_instrument(path, notes, wait)
    MUSIC_CACHE.mkdir(parents=True, exist_ok=True)
    np.save(c, out)
    return out


def _render_instrument(path: Path, notes, wait: float = 0.0) -> np.ndarray:
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
        mono = cq.sos_filter(y.mean(1), "highpass", 75).astype(np.float32)     # a recorded take may bring rumble
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


def master(stems: dict[str, np.ndarray], target=-16.0, ceiling=-1.5) -> dict[str, np.ndarray]:
    """One gain curve for every stem (so they still sum to the soundtrack): glue, the end fade, the level to `target`
    LUFS integrated, and a true-peak limiter (4x oversampled detection) at `ceiling` - 0.3 dBTP."""
    mix = sum(stems.values())
    g = cq.glue_gain(mix)
    fades = np.ones(N, np.float32)
    i0, i1 = int(MARK["fade_out"] * SR), min(N, int(MARK["end"] * SR) - 1)
    fades[i0:i1] = ((0.5 + 0.5 * np.cos(np.linspace(0, np.pi, i1 - i0))) ** 1.5).astype(np.float32)
    fades[i1:] = 0
    total, gain = g * fades, 1.0
    for _ in range(5):
        y = mix * total * gain
        lim = cq.limiter_gain(y, ceiling - 0.3)
        L = cq.lufs_integrated(y * lim)
        print(f"  master: LUFS {L:6.2f}  gain {20 * np.log10(gain):+5.2f} dB  limiter GR {-20 * np.log10(lim.min()):4.1f} dB")
        if abs(L - target) < 0.05:
            break
        gain *= cq.db(target - L)
    k = total * gain * lim
    return {name: x * k for name, x in stems.items()}


# the score steps back for the story's sounds: (cue time, dB, from, to) - the key turning, the click, the last bell
def spot_ducks() -> np.ndarray:
    spots = [(MARK["unlock"], 5.0, .15, 1.0), (MARK["click_build"], 3.0, .1, .5), (MARK["bell_final"], 3.0, .1, .6)]
    g = np.zeros(N)
    t = np.arange(N) / SR
    for tc, d, pre, post in spots:
        a, b = tc - pre, tc + post
        up = np.clip((t - (a - .08)) / .08, 0, 1)             # 80 ms in
        dn = np.clip(((b + .4) - t) / .4, 0, 1)               # 400 ms out
        g = np.minimum(g, -d * np.minimum(up, dn))
    return cq.db(g)


def check_music_marks() -> None:
    """Each music section's cue time (cues.json -> music) against the bar line its part of the arrangement starts on."""
    starts = {"handover": SEC["handover"] + .35}                                   # the first roll
    p = plan()
    by = {"work": p[3][0], "before_build": p[5][0], "build": p[6][0], "lift": p[7][0], "tuesday": p[9][0], "lisbon": p[10][0]}
    print("music sections vs. the arrangement:")
    for m in CUES["music"]:
        sec = m["section"]
        if sec in by:
            t = bar(by[sec])
            print(f"  {sec:13} cue {m['t']:7.2f}  bar line {t:7.2f}  ({t - m['t']:+5.2f} s)")
        elif sec == "handover":
            print(f"  {sec:13} cue {m['t']:7.2f}  first roll {starts['handover']:7.2f}  ({starts['handover'] - m['t']:+5.2f} s)")
        else:
            print(f"  {sec:13} cue {m['t']:7.2f}  held chord at bar {bar(bar_at(SEC['close'])):7.2f}; final Dadd9 at title {MARK['title']:.2f}")
    assert abs(bar(p[7][0]) - MARK["tab_change"]) < 1e-6, "the lift must land on the tab change"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-vst", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="re-render the instruments (ignore the cache)")
    ap.add_argument("--target", type=float, default=-16.0)
    a = ap.parse_args()
    t0 = time.time()
    print(f"film {DUR:.2f} s; grid: bar 0 at {GRID0:.2f} s, lift bar line at {LIFT:.2f} s")
    for first, chords, style in plan():
        print(f"  bars {first:3d}-{first + len(chords) - 1:3d}  {bar(first):7.2f}-{bar(first + len(chords)):7.2f}  {style:10} {' '.join(chords)}")
    check_music_marks()
    sc = Score()
    sc.compose()
    end = max(t + d for _, _, t, d in sc.guitar + sc.bass)
    print(f"composed: {len(sc.guitar)} guitar notes, {len(sc.bass)} bass notes; last note-off {end:.2f} s "
          f"(film {DUR:.2f} s; notes are cut at the end, the master fades from {MARK['fade_out']:.2f} s)")
    if a.no_vst:
        gtr, bass = stand_in(sc.guitar), stand_in([(n + 12, v, t, d) for n, v, t, d in sc.bass], .2)
    else:
        print("rendering guitar (Ample Guitar M Lite II) ...")
        gtr = render_instrument(GUITAR, sc.guitar, wait=8.0, fresh=a.fresh)
        print("rendering bass (MODO BASS 2) ...")
        bass = render_instrument(BASS, sc.bass, wait=2.0, fresh=a.fresh)
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

    print("voices ...")
    voice = voices()
    venv = np.clip(envelope(voice, .08, .45) / .05, 0, 1).astype(np.float32)
    look = int(.06 * SR)                                         # look-ahead: the duck is down by the first syllable
    venv = np.concatenate([venv[look:], np.repeat(venv[-1:], look)])
    # under speech: -8 dB, and a further presence dip where the words live; where the music runs hotter than it usually
    # does under speech (the Lisbon strums), up to 4 dB more
    dip = foley.peq(music, 2500, -3.0, .8)
    ms = uniform_filter1d((music.astype(np.float64) ** 2).mean(0), int(.4 * SR))
    mdb = 10 * np.log10(ms + 1e-12)
    ref = float(np.median(mdb[venv > .5]))
    extra = np.clip(mdb - ref, 0, 4) * venv
    music = (music * (1 - venv) + dip * venv) * cq.db(-8.0 * venv - extra).astype(np.float32)
    music = music * spot_ducks().astype(np.float32)
    print("sound effects + ambience (Core Library) ...")
    sfx, amb, report = foley.render(CUES, N, venv)
    amb = amb * cq.db(-4.0 * venv).astype(np.float32)
    sfx = sfx * cq.db(-2.0 * venv).astype(np.float32)          # effects give way a little to the words, too
    worst = max((abs(ta - t) for _, _, kind, t, ta in report if ta is not None), default=0.0)
    late = [(s.get("label", typ), t, ta) for s, typ, kind, t, ta in report if ta is not None and abs(ta - t) > .03]
    print(f"  {len(report)} cues; one-shots land within {worst * 1000:.0f} ms of their cue (first transient)")
    for lab, t, ta in late:
        print(f"    {lab}: cue {t:.2f}, sound at {ta:.2f} ({(ta - t) * 1000:+.0f} ms)")
    print("mastering ...")
    st = master({"music": music.astype(np.float64), "sfx": sfx.astype(np.float64), "ambience": amb.astype(np.float64),
                 "voice": voice.astype(np.float64)}, a.target)
    for name, x in {**st, "soundtrack": sum(st.values())}.items():
        cq.write_wav(str(HERE / f"{name}.wav"), x)
    print(f"wrote {HERE / 'soundtrack.wav'} + stems ({DUR:.2f} s) in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
