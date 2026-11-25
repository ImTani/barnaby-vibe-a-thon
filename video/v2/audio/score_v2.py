"""The film's soundtrack: video/audio/score.py (v1) adapted to the v2 cue sheet, with recorded foley and ambience.
Music on Ample Guitar M Lite II, MODO BASS 2 and Valhalla VintageVerb (a send), all hosted offline by DawDreamer; sound
effects and ambience from the Ableton Live 12 Suite Core Library (foley.py); voices from voice/manifest.json; one mix
and master (glue, true-peak limiter, -16 LUFS integrated, <= -1 dBTP, 48 kHz stereo).

  runtime/audio/.venv/Scripts/python video/v2/audio/score_v2.py            (a minute or two; Ample needs ~8 s to load)
  ... score_v2.py --no-vst      quick structural check with a plain synth stand-in (never ship this)
  ... score_v2.py --fresh       re-render the instruments even if the cached render matches the notes

Writes video/v2/audio/soundtrack.wav and its stems music.wav + sfx.wav + voice.wav (48 kHz, cues.json -> duration; they
sum to the soundtrack), with sfx.wav also split into effects.wav and ambience.wav. The instrument renders are cached under .cache/audio/music/ (keyed by the notes).

- Music: D major, 80 BPM (bar = 3 s), on a grid that puts a downbeat exactly on the tab change in scene 6
  (marks.tab_change: "the music builds, then releases on the click and the tab change"). Sections follow cues.json ->
  music: silent until the bell; enters after it (handover) and resolves before the key, rain only under the
  lamp-off and the time-lapse; walking pace for Monday; thins under "Who's got too
  much on this week?"; builds from the code to the click; releases on the tab change; settles for Priya; brighter in
  Lisbon; resolves with the bell and the titles. The run prints each section's cue time against its bar line.
- Sound effects and ambience follow cues.json -> sfx (foley.py; sources and processing in SOUND.md).
- Voices from video/v2/audio/voice/manifest.json (video/audio/voices.py, which also takes recorded lines via --takes).
  One chain for every line (v2.4, see voices()): HP 75 Hz; Supertone Clear (VST3, offline, cached in
  .cache/audio/voice_chain/) on the recorded takes, Martin fully and Theo and Priya lightly; a 1/3-octave match EQ moving
  each human speaker toward Barnaby's long-term spectrum (+-6 dB); a 5-9 kHz de-esser; 2.5:1 compression (~3-4 dB);
  every line levelled to the same loudness (BS.1770, gated); one short room shared by all four voices.
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
    kH = bar_at(MARK["bell_arrive"] + 1.0, early=0)    # the first full bar after the bell (the entry roll fills the gap)
    kR = int(np.floor((MARK["key"] - 3.9 - GRID0) / BAR))   # the resolving bar: its roll has died away before the key
    kW = bar_at(SEC["work"])
    k5 = bar_at(CUES["scenes"][4]["start"])
    kQ = bar_at(SEC["before_build"])
    kB = bar_at(SEC["build"])
    kL = bar_at(SEC["lift"], early=0)
    kT = bar_at(SEC["tuesday"])
    kS = bar_at(SEC["lisbon"] + 1.5)                    # the street first, then the music
    kC = bar_at(SEC["close"])
    # the build climbs bar by bar from the code to the click: 8 bars (7 in the 3:38 cut, where the Em/D passing bar went
    # and the climb kept its top: see compose, the last two bars run in sixteenths either way)
    build = {8: ["Bm", "Bm/A", "G", "G/F#", "Em7", "Em/D", "Asus4", "A"],
             7: ["Bm", "Bm/A", "G", "G/F#", "Em7", "Asus4", "A"]}
    assert kL - kB in build, f"the build must be 7 or 8 bars into the lift (bars {kB}..{kL})"
    cyc = lambda seq, n: [seq[i % len(seq)] for i in range(n)]
    return [
        (kH, cyc(["D", "A/C#", "Bm7", "Gmaj7", "D/F#"], kR - kH - 1) + ["Asus4"], "pick_soft"),   # handover
        (kR, ["D"], "resolve"),                                                       # resolves before the key; then
        (kW, cyc(["D", "G", "Bm", "A"], k5 - kW), "pick"),                            # rain only until Monday's walk
        (k5, cyc(["D", "G", "Bm", "A"], kQ - k5), "pick_plus"),                       # the montage: a little more forward
        (kQ, cyc(["Bm", "G", "D", "A"], kB - kQ), "pick_soft"),                       # under the question: thinner
        (kB, build[kL - kB], "build"),                                                # the code -> the click
        (kL, cyc(["D", "A/C#", "Bm", "G"], kT - kL - 1), "strum"),                    # release: the tab change
        (kT - 1, cyc(["D", "A/C#", "Bm", "G"], kT - kL)[-1:], "ring"),                # one strum rings over the cut
        (kT, cyc(["D", "G", "Bm", "A"], kS - kT), "pick_soft"),                       # Priya: settles
        (kS, cyc(["D", "A/C#", "Bm", "G"], kC - kS - 1), "strum_full"),               # Lisbon: brighter, fuller
        (kC - 1, cyc(["D", "A/C#", "Bm", "G"], kC - kS)[-1:], "ring"),                # one strum rings into the night
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
                elif style == "resolve":
                    self.roll(ch, 44, bar(k) + .15, 3.0, step=.11)
                    self.b(CH[ch][1], 48, bar(k) + .1, 2.8)
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
        # the close: a held Asus4 under the goodnights, G as we cut to Lisbon, A for the two desks; the bell, and the
        # final Dadd9 resolving on it (the bell is its 9th), a soft re-roll under "Even the old ones." and a last one with
        # the credit
        kC = bar_at(SEC["close"])
        self.roll("Asus4", 42, bar(kC) + .1, 4.2, step=.1)
        self.b(CH["Asus4"][1], 50, bar(kC), 3.8)
        self.roll("Gmaj7", 40, MARK["lisbon_night"] + .15, 4.0, step=.1)
        self.b(CH["Gmaj7"][1], 48, MARK["lisbon_night"] + .1, 3.6)
        self.roll("Asus4", 40, MARK["two_desks"] + .05, 3.0, step=.08)
        self.b(CH["Asus4"][1], 50, MARK["two_desks"], 2.6)
        fin = MARK["bell_final"] + .25
        for i, n in enumerate(CH["Dadd9"][0]):
            self.g(n, 74 - 3 * i, fin + i * .11, 9.0, ms=2)
        self.b(38, 68, fin, 8.0)
        if "end_card" in MARK:
            # the product end card: the roll under "Even the old ones." is the last chord; it carries into the card and
            # is faded out by marks.fade_out (music_gate)
            hold = MARK["fade_out"] - MARK["old_ones"] + .5
            for i, n in enumerate([57, 62, 66, 69, 74]):
                self.g(n, 58 - 3 * i, MARK["old_ones"] + i * .14, hold, ms=0)
            self.b(38, 54, MARK["old_ones"], hold)
        else:
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
VOICE_LEVEL = -20.5                                    # each line's loudness before the master (LUFS)
CLEAR = PLUGINS / "VST3" / "Clear.vst3"                # Supertone Clear (AI noise reduction), hosted offline
VOICE_CACHE = V2.parents[1] / ".cache" / "audio" / "voice_chain"
# Clear's Ambience Gain (normalised): 0.0 = -60 dB (Martin's noisy mic), 0.1 = -20.7 dB (a light clean on the others);
# Voice and Voice Reverb stay at 0 dB. Barnaby (ElevenLabs) is the reference and is not cleaned.
CLEAR_AMB = {"Martin": 0.0, "Theo": 0.1, "Priya": 0.1}
EQ_LIMIT = 6.0                                         # the match EQ's correction, at most +-6 dB per 1/3-octave band
COMP = dict(ratio=2.5, attack=.015, release=.15, gr=3.0)   # gentle: ~3-4 dB of gain reduction on the louder words
DEESS = (5000, 9000)                                   # the de-esser's band


def _read_mono(p: Path) -> np.ndarray:
    from scipy.signal import resample_poly
    y, sr = sf.read(p, dtype="float32", always_2d=True)
    if sr != SR:
        y = resample_poly(y, SR // np.gcd(SR, sr), sr // np.gcd(SR, sr), axis=0).astype(np.float32)
    return y.mean(1).astype(np.float32)


def clear_takes(man: list[dict]) -> dict[str, np.ndarray]:
    """Supertone Clear on the recorded takes (Martin, Theo, Priya), offline in DawDreamer, latency removed by
    cross-correlation; cached under .cache/audio/voice_chain/ by the take's bytes and the setting."""
    from scipy.signal import correlate
    out, need = {}, []
    for line in man:
        who = line["who"]
        if who not in CLEAR_AMB:
            continue
        p = HERE / line["file"]
        key = hashlib.sha1(p.read_bytes() + f"clear1|{CLEAR_AMB[who]}".encode()).hexdigest()[:16]
        c = VOICE_CACHE / f"{p.stem}_{key}.wav"
        if c.exists():
            out[line["file"]] = sf.read(c, dtype="float32")[0]
        else:
            need.append((line, p, c))
    if not need:
        return out
    import dawdreamer as daw
    VOICE_CACHE.mkdir(parents=True, exist_ok=True)
    print(f"  Supertone Clear on {len(need)} takes ...")
    eng = daw.RenderEngine(SR, BLOCK)
    pl = eng.make_plugin_processor("clear", str(CLEAR))
    src = eng.make_playback_processor("src", np.zeros((2, SR), np.float32))
    eng.load_graph([(src, []), (pl, ["src"])])
    pre, post = int(.3 * SR), int(.6 * SR)
    for line, p, c in need:
        y = _read_mono(p)
        x = np.concatenate([np.zeros(pre, np.float32), y, np.zeros(post, np.float32)])
        src.set_data(np.vstack([x, x]))
        pl.set_parameter(0, CLEAR_AMB[line["who"]])          # ambience
        pl.set_parameter(4, .5)                              # voice 0 dB
        pl.set_parameter(8, .5)                              # voice reverb 0 dB
        pl.set_parameter(15, 0.0)                            # not bypassed
        eng.render(len(x) / SR)
        a = eng.get_audio()[:, :len(x)].mean(0).astype(np.float32)
        # the plugin's latency: the lag (0-200 ms) that best lines the output up with the input
        L, maxlag = min(len(y), 4 * SR), int(.2 * SR)
        cc = correlate(a[pre: pre + L + maxlag], x[pre: pre + L], mode="valid")
        lag = int(np.argmax(cc[: maxlag + 1]))
        z = a[pre + lag: pre + lag + len(y)]
        z = np.pad(z, (0, len(y) - len(z))).astype(np.float32)
        sf.write(c, z, SR, subtype="FLOAT")
        out[line["file"]] = z
        print(f"    {p.name}: latency {lag} samples")
    return out


def _voiced(x: np.ndarray, hop: int = 1024) -> np.ndarray:
    """Frames (hop samples) that carry speech: within 30 dB of the line's loudest frames."""
    m = len(x) // hop
    r = 10 * np.log10((x[: m * hop].reshape(m, hop).astype(np.float64) ** 2).mean(1) + 1e-14)
    return r > np.percentile(r, 95) - 30


THIRD_OCT = 1000 * 2 ** (np.arange(-14, 13) / 3)        # 1/3-octave centres, 40 Hz - 16 kHz


def ltas(xs: list[np.ndarray]) -> np.ndarray:
    """Long-term average spectrum over the voiced frames, in 1/3-octave bands (dB)."""
    nfft, hop = 4096, 1024
    win = np.hanning(nfft)
    acc, k = np.zeros(nfft // 2 + 1), 0
    for x in xs:
        v = _voiced(x, hop)
        for i in np.nonzero(v)[0]:
            f = x[i * hop: i * hop + nfft]
            if len(f) < nfft:
                break
            acc += np.abs(np.fft.rfft(f * win)) ** 2
            k += 1
    acc /= max(k, 1)
    fr = np.fft.rfftfreq(nfft, 1 / SR)
    bands = []
    for fc in THIRD_OCT:
        sel = (fr >= fc * 2 ** (-1 / 6)) & (fr < fc * 2 ** (1 / 6))
        bands.append(10 * np.log10(acc[sel].mean() + 1e-20))
    return np.array(bands)


def f0_median(xs: list[np.ndarray]) -> float:
    """A speaker's median pitch (Hz): autocorrelation over 40 ms voiced frames, 70-400 Hz, frames with a clear period."""
    from scipy.signal import decimate
    f0s, n = [], 1920
    for x in xs:
        y = decimate(x.astype(np.float64), 4)                   # 12 kHz is plenty for a pitch estimate
        v = _voiced(y, n // 4)
        for i in np.nonzero(v)[0]:
            f = y[i * n // 4: i * n // 4 + n // 4 * 2]
            if len(f) < n // 2:
                break
            f = f - f.mean()
            ac = np.correlate(f, f, "full")[len(f) - 1:]
            lo, hi = int(12000 / 400), int(12000 / 70)
            k = lo + int(np.argmax(ac[lo:hi]))
            if ac[k] > .45 * ac[0]:
                f0s.append(12000 / k)
    return float(np.median(f0s)) if f0s else 120.0


def match_curve(ref: np.ndarray, spk: np.ndarray, f0: float = 80.0) -> np.ndarray:
    """The 1/3-octave correction moving a speaker's tonal balance toward the reference: level-matched over the bands
    from 150 Hz (or 1.25 x the speaker's pitch) to 6 kHz, smoothed across neighbouring bands, held to +-EQ_LIMIT, and
    eased to 0 dB below the speaker's own pitch (a voice has nothing there to match: Priya's sits an octave above
    Barnaby's) and above 12 kHz."""
    d = ref - spk
    core = (THIRD_OCT >= max(150.0, 1.25 * f0)) & (THIRD_OCT <= 6000)
    d = d - d[core].mean()
    d = np.convolve(np.pad(d, 1, mode="edge"), [.25, .5, .25], mode="valid")
    d = np.clip(d, -EQ_LIMIT, EQ_LIMIT)
    edge = max(80.0, f0)
    lo = np.clip(np.log2(THIRD_OCT / (edge * 2 ** (-1 / 3))) / (1 / 3), 0, 1)      # 0 a third below, 1 at the edge
    hi = np.clip(np.log2(16000 / THIRD_OCT) / np.log2(16000 / 12000), 0, 1)
    return d * lo * hi


def apply_eq(x: np.ndarray, curve_db: np.ndarray) -> np.ndarray:
    """A linear-phase FIR (4095 taps) through the 1/3-octave gains."""
    from scipy.signal import firwin2, oaconvolve
    f = np.concatenate([[0], THIRD_OCT, [SR / 2]])
    g = np.concatenate([[curve_db[0]], curve_db, [curve_db[-1]]])
    h = firwin2(4095, f / (SR / 2), 10 ** (g / 20))
    return oaconvolve(x, h, mode="same").astype(np.float32)


def _smooth_gain(gdb: np.ndarray, attack: float, release: float, hop: int) -> np.ndarray:
    """One-pole attack/release smoothing of a gain-reduction curve (dB, <= 0) at `hop`-sample resolution."""
    a_a, a_r = np.exp(-hop / (attack * SR)), np.exp(-hop / (release * SR))
    out, cur = np.empty_like(gdb), 0.0
    for i, g in enumerate(gdb):
        cur = g + (a_a if g < cur else a_r) * (cur - g)
        out[i] = cur
    return out


def _env_db(x: np.ndarray, hop: int, win: float = .01) -> np.ndarray:
    m = len(x) // hop + 1
    e = uniform_filter1d(x.astype(np.float64) ** 2, max(1, int(win * SR)))
    e = np.pad(e, (0, m * hop - len(e)), mode="edge")[: m * hop].reshape(m, hop).max(1)
    return 10 * np.log10(e + 1e-14)


def deess(x: np.ndarray, pct=92.0, rel=3.0, ratio=.6, cap=6.0) -> tuple[np.ndarray, float]:
    """A split-band de-esser: the 5-9 kHz band (zero-phase FIR split, so band + rest = the line exactly) comes down only
    on the sibilants - where it runs above its own `pct` percentile in the line's voiced frames, or comes within `rel` dB
    of the whole voice (an "s" dominating) - by (excess x `ratio`), at most `cap` dB; 2 ms attack, 60 ms release.
    Returns (audio, the deepest cut in dB)."""
    from scipy.signal import firwin, oaconvolve
    h = firwin(1023, DEESS, pass_zero=False, fs=SR)
    s = oaconvolve(x, h, mode="same").astype(np.float32)
    rest = x - s
    hop = 48
    es, ef = _env_db(s, hop, .005), _env_db(x, hop, .005)
    v = ef > ef.max() - 30
    thr = np.percentile(es[v], pct) if v.any() else es.max()
    over = np.maximum(np.maximum(es - thr, 0), np.maximum(es - (ef - rel), 0)) * ratio
    gdb = _smooth_gain(-np.minimum(over, cap), .002, .06, hop)
    g = np.repeat(10 ** (gdb / 20), hop)[: len(x)]
    return (rest + s * g).astype(np.float32), float(-gdb.min())


def compress(x: np.ndarray, ratio=2.5, attack=.015, release=.15, gr=3.5):
    """A gentle RMS compressor, its threshold set per line so the louder words (90th percentile of the voiced
    envelope) see about `gr` dB of gain reduction; 6 dB soft knee; makeup is left to the levelling that follows.
    Returns (audio, gain reduction at the louder words in dB)."""
    hop = 48
    e = _env_db(x, hop, .02)
    v = e > e.max() - 30
    thr = np.percentile(e[v], 90) - gr / (1 - 1 / ratio)
    over, knee = e - thr, 6.0
    red = np.where(over <= -knee / 2, 0.0,
                   np.where(over >= knee / 2, over, (over + knee / 2) ** 2 / (2 * knee))) * (1 - 1 / ratio)
    gdb = _smooth_gain(-red, attack, release, hop)
    g = np.repeat(10 ** (gdb / 20), hop)[: len(x)]
    return (x * g).astype(np.float32), float(-np.percentile(gdb[v], 10))


def offscreen(line: dict) -> float:
    """How far off a line is (o.s. in the script): Martin from the workshop in scene 1, the two goodnights from the door.
    Found by scene and words, not by line number, so a re-laid cue sheet or new takes keep it."""
    if line.get("scene") == 1 and line["who"] == "Martin":
        return .85
    if line.get("scene") == 9 and line["text"].strip().lower().startswith("night"):
        return .6
    return 0.0


def voices() -> np.ndarray:
    """The dialogue: every line through one chain - high-pass 75 Hz, Supertone Clear on the recorded takes (Martin
    fully, Theo and Priya lightly), a 1/3-octave match EQ moving each human speaker toward Barnaby's long-term spectrum
    (+-6 dB), a 5-9 kHz de-esser, gentle 2.5:1 compression, the same loudness for every line, and one short room for
    everyone (off-screen lines keep their high-cut and the bigger, farther room)."""
    man = json.loads((HERE / "voice" / "manifest.json").read_text(encoding="utf-8"))
    out, far, near = cq.bus(), cq.bus(), cq.bus()
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    cleaned = clear_takes(man)
    raw = {}
    for line in man:
        y = cleaned.get(line["file"])
        if y is None:
            y = _read_mono(HERE / line["file"])
        raw[line["file"]] = cq.sos_filter(y, "highpass", 75).astype(np.float32)    # a recorded take may bring rumble
    by = {}
    for line in man:
        by.setdefault(line["who"], []).append(raw[line["file"]])
    curves = {}
    if "Barnaby" in by:
        ref = ltas(by["Barnaby"])
        for who, xs in by.items():
            if who == "Barnaby":
                continue
            f0 = f0_median(xs)
            c = curves[who] = match_curve(ref, ltas(xs), f0)
            show = [(f, g) for f, g in zip(THIRD_OCT, c) if min(abs(f / q - 1) for q in
                                                                (100, 200, 400, 800, 1600, 3150, 5000, 8000, 12500)) < .06]
            print(f"  match EQ {who:6} (pitch ~{f0:.0f} Hz): " + "  ".join(f"{f:,.0f} {g:+.1f}" for f, g in show) +
                  f"  (dB; largest {np.abs(c).max():.1f})")
    grs, ess = [], {}
    for i, line in enumerate(man, 1):
        mono = raw[line["file"]]
        if line["who"] in curves:
            mono = apply_eq(mono, curves[line["who"]])
        mono, e = deess(mono)
        ess.setdefault(line["who"], []).append(e)
        mono, gr = compress(mono, **COMP)
        grs.append(gr)
        # every line to the same loudness (BS.1770 integrated, block-gated, so pauses don't count): TTS lines and recorded
        # takes (the ElevenLabs Barnaby is mastered louder and more compressed) sit level with each other
        lk = meter.integrated_loudness(mono.astype(np.float64)) if len(mono) > .6 * SR else -99.0
        if not np.isfinite(lk) or lk < -70:
            act = np.abs(mono) > 1e-3
            kw = cq.k_weight(mono[None, :].astype(np.float64))[0]
            lk = -0.691 + 10 * np.log10((kw[act] ** 2).mean() + 1e-12)
        mono = (mono * 10 ** ((VOICE_LEVEL - lk) / 20)).astype(np.float32)
        pan = {"Barnaby": 0.0, "Martin": -0.12, "Theo": -0.1, "Priya": 0.12}.get(line["who"], 0.0)
        d = offscreen(line)
        if d:
            mono = cq.sos_filter(mono, "lowpass", 5200 - 2400 * d).astype(np.float32)
            cq.place(out, mono, float(line["t"]), cq.db(-3.5 * d), pan - .25 * d)
            cq.place(far, mono, float(line["t"]), .55 * d, pan)
        else:
            cq.place(out, mono, float(line["t"]), 1.0, pan)
        cq.place(near, mono, float(line["t"]), .16, pan)                 # one short room for all four voices
    print(f"  compression: {np.median(grs):.1f} dB median gain reduction on the louder words "
          f"(range {min(grs):.1f}-{max(grs):.1f})")
    print("  de-esser, deepest cut per line (median / max): " + ", ".join(
        f"{w} {np.median(v):.1f}/{max(v):.1f} dB" for w, v in ess.items()))
    far = cq.sos_filter(far, "highpass", 220).astype(np.float32)
    room = cq.convolve(far, cq.make_ir(0.55, 1.2, "office", lp=6000, predelay=.008)) * .5
    near = cq.sos_filter(near, "highpass", 250).astype(np.float32)
    small = cq.convolve(near, cq.make_ir(0.28, .6, "booth", lp=6500, predelay=.004)) * .5
    out = out + room.astype(np.float32) + small.astype(np.float32)
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
    np.save(MUSIC_CACHE.parent / "master_gain.npy", k.astype(np.float32))      # for check.py --levels
    return {name: x * k for name, x in stems.items()}


# the score steps back for the story's sounds: (cue time, dB, before, after) - the key turning, "Fussy." and the click
def spot_ducks() -> np.ndarray:
    spots = [(MARK["unlock"], 5.0, .15, 1.0), (MARK["click_build"], 3.0, .5, .5)]    # the click lands on "Fussy."
    g = np.zeros(N)
    t = np.arange(N) / SR
    for tc, d, pre, post in spots:
        a, b = tc - pre, tc + post
        up = np.clip((t - (a - .08)) / .08, 0, 1)             # 80 ms in
        dn = np.clip(((b + .4) - t) / .4, 0, 1)               # 400 ms out
        g = np.minimum(g, -d * np.minimum(up, dn))
    return cq.db(g)


def styled(style: str, after: str | None = None) -> int:
    """The first bar of the plan's first `style` part (after the first `after` part, if given)."""
    p, seen = plan(), after is None
    for first, chords, st in p:
        if seen and st == style:
            return first
        seen = seen or st == after
    raise KeyError(style)


def music_gate() -> np.ndarray:
    """Silence the score where the picture asks for it: nothing before the bell; after the handover resolves, nothing
    under the key and the lamp-off (rain only) until Monday's walking music starts; on the end card the last chord
    fades out by marks.fade_out."""
    t = np.arange(N) / SR
    g = np.ones(N)
    g[t < MARK["bell_arrive"]] = 0.0
    a, b = MARK["key"] - .6, MARK["key"]
    w0 = bar(styled("pick")) - .05
    fade = (t >= a) & (t < b)
    g[fade] = .5 + .5 * np.cos(np.pi * (t[fade] - a) / (b - a))
    g[(t >= b) & (t < w0)] = 0.0
    if "end_card" in MARK:                                       # the last chord fades through the card, gone by fade_out
        a, b = MARK["end_card"] + 1.5, MARK["fade_out"]
        fade = (t >= a) & (t < b)
        g[fade] *= (.5 + .5 * np.cos(np.pi * (t[fade] - a) / (b - a))) ** 1.5
        g[t >= b] = 0.0
    return g.astype(np.float32)


def check_music_marks() -> None:
    """Each music section's cue time (cues.json -> music) against the bar line its part of the arrangement starts on."""
    starts = {"handover": SEC["handover"] + .35}                                   # the first roll
    by = {"work": styled("pick"), "before_build": styled("pick_soft", "pick_plus"), "build": styled("build"),
          "lift": styled("strum"), "tuesday": styled("pick_soft", "ring"), "lisbon": styled("strum_full")}
    print("music sections vs. the arrangement:")
    for m in CUES["music"]:
        sec = m["section"]
        if sec in by:
            t = bar(by[sec])
            print(f"  {sec:13} cue {m['t']:7.2f}  bar line {t:7.2f}  ({t - m['t']:+5.2f} s)")
        elif sec == "handover":
            print(f"  {sec:13} cue {m['t']:7.2f}  first roll {starts['handover']:7.2f}  ({starts['handover'] - m['t']:+5.2f} s);"
                  f" resolves at bar {bar(styled('resolve')):.2f}, silent from the key ({MARK['key']:.2f}) to "
                  f"{bar(styled('pick')):.2f}")
        else:
            print(f"  {sec:13} cue {m['t']:7.2f}  held chord at bar {bar(bar_at(SEC['close'])):7.2f}; the final Dadd9 "
                  f"resolves on the last bell ({MARK['bell_final']:.2f} + 0.25)")
    assert abs(bar(styled("strum")) - MARK["tab_change"]) < 1e-6, "the lift must land on the tab change"
    assert bar(styled("resolve")) + .15 + 3.0 < MARK["key"] - .5, "the handover must resolve before the key"


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
    music = music * music_gate()                                  # no music before the bell, none under the lamp-off

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
    MUSIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(MUSIC_CACHE.parent / "voice_env.npy", venv)                           # for check.py --levels
    sfx, amb, report = foley.render(CUES, N, venv)
    amb = amb * cq.db(-4.0 * venv).astype(np.float32)
    sfx = sfx * cq.db(-2.0 * venv).astype(np.float32)          # effects give way a little to the words, too
    worst = max((abs(ta - t) for _, _, kind, t, ta in report if ta is not None), default=0.0)
    late = [(s.get("label", typ), t, ta) for s, typ, kind, t, ta in report if ta is not None and abs(ta - t) > .03]
    print(f"  {len(report)} cues; one-shots land within {worst * 1000:.0f} ms of their cue (first transient)")
    for lab, t, ta in late:
        print(f"    {lab}: cue {t:.2f}, sound at {ta:.2f} ({(ta - t) * 1000:+.0f} ms)")
    print("mastering ...")
    st = master({"music": music.astype(np.float64), "effects": sfx.astype(np.float64), "ambience": amb.astype(np.float64),
                 "voice": voice.astype(np.float64)}, a.target)
    # sfx.wav keeps its old meaning (effects + ambience: music + sfx + voice = the soundtrack, and the DubMate backing
    # is music + sfx); effects.wav and ambience.wav are its two halves
    out = {**st, "sfx": st["effects"] + st["ambience"], "soundtrack": sum(st.values())}
    for name, x in out.items():
        cq.write_wav(str(HERE / f"{name}.wav"), x)
    print(f"wrote {HERE / 'soundtrack.wav'} + stems ({DUR:.2f} s) in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
