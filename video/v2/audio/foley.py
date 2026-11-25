"""Barnaby's sound effects and ambience from recorded samples (Ableton Live 12 Suite Core Library), for score_v2.py.

Every effect cue in video/v2/cues.json -> sfx is built from Core Library recordings, layered, EQ'd, placed in a room
(short convolution rooms per space: the back office, the workshop through the doorway, Barnaby's worlds, Theo's flat in
Lisbon) and set by level and pan for its perspective. Synthesis is used only where the library has nothing (road
traffic, a low room tone) and for the long ring of the brass bell, which is a modal extension fitted to the sampled bell's
own partials (frequency, amplitude and phase), so the recording hands over to the model without a seam.

The samples are read in place and never copied into the repo: they are licensed for use in productions, not for
redistribution. Conversions to 48 kHz are cached as .npy under the gitignored .cache/audio/samples/.

  render(cues, voice_env) -> (sfx, ambience, report)       both stereo (2, N) float32 buses; report: cue -> source/timing
  SOURCES                                                   cue type -> Core Library paths (SOUND.md is written from it)
"""
from __future__ import annotations

import hashlib
import importlib.util
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CL = Path(r"C:\ProgramData\Ableton\Live 12 Suite\Resources\Core Library\Samples")
CACHE = ROOT / ".cache" / "audio" / "samples"
SR = 48000

_spec = importlib.util.spec_from_file_location("cq_foley", ROOT / "video" / "audio" / "compose.quorum.py")
cq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cq)

# ── the Core Library sources (paths under Samples/) ──
P = {
    "cassette":   "One Shots/Drums/Wood/Wood Insert Cassette.wav",       # a plastic latch: the mouse button
    "vinyl":      "One Shots/Drums/Misc Percussion/Click Vinyl.wav",      # a small dry click: button release, lamp
    "plastic1":   "One Shots/Drums/Misc Percussion/Perc Plastic 1.wav",   # plastic taps: keys
    "plastic2":   "One Shots/Drums/Misc Percussion/Perc Plastic 2.wav",
    "prod":       "One Shots/Drums/Wood/Wood Prod Soft.wav",              # a soft tap: key upstrokes, modern keys
    "coin":       "One Shots/Drums/Misc Percussion/Foley Coin LDre.wav",  # metal on a surface: the key on the keyboard
    "lock":       "One Shots/FX/Foley Door Lock.wav",                     # a key turning in a lock
    "jingle":     "One Shots/Drums/Misc Percussion/Perc Jingle.wav",      # a bunch of keys
    "rattle":     "One Shots/Drums/Misc Percussion/Metallic Rattle.wav",
    "hit_hard":   "One Shots/Drums/Misc Percussion/Perc Hit Hard.aif",    # the clamp lever
    "metal":      "One Shots/FX/Impact Short Metal.wav",                  # the stand's heavy clunk
    "pan":        "One Shots/Drums/Misc Percussion/Perc Pan.wav",         # its ring
    "tiny":       "One Shots/Drums/Misc Percussion/Perc Tiny.wav",        # grains: drive seeks, freewheel pawls
    "machine":    "Loops/Texture/Machine Noise Ambient.wav",              # a running machine: the PC fan, the compressor
    "sink":       "Loops/Texture/Sink Noise.wav",                         # air hiss: the compressor
    "hit_soft":   "One Shots/Drums/Misc Percussion/Perc Hit Soft.aif",    # soft steps
    "marimba":    "One Shots/Instrument/Mallets/Marimba Cloth C3.aif",    # the steps' soft pitch (stylised)
    "scratch":    "One Shots/Drums/Misc Percussion/Perc Wood Scratch.aif",  # the drawer's slide
    "wood_low":   "One Shots/Drums/Wood/Wood Dry Low.aif",                # the drawer's stop
    "drip":       "One Shots/Drums/FX Hit/FX Drip 2.wav",                 # soft pops
    "celeste":    "One Shots/Instrument/Mallets/Celeste C6.wav",          # the checks' ding
    "swell":      "One Shots/FX/Swell Short Noise.wav",                   # time passing
    "bowl":       "One Shots/FX/Bowl Swell B1.aif",
    "bell":       "One Shots/Drums/Bell/Bell Cash.aif",                   # the brass counter bell (strike and body)
    "rain":       "Loops/Texture/Rain and Train.wav",                     # rain (8-22.5 s and 52-64 s: no gusts, no train)
    "radio":      "Loops/Texture/Radio Station Search.wav",               # a radio, played through a small speaker
    "nuts":       "Loops/Texture/Nuts and Bolts.wav",                     # rummaging in a parts tray: the workshop
    "crowd":      "Loops/Texture/Television Crowd.wav",                   # people talking: customers, the street below
    "cups":       "Loops/Texture/Tea Cups.wav",                           # mugs
    "birds":      "Loops/Texture/Forest Ambience.wav",                    # birds over the street
    "wind":       "Loops/Texture/Wind Air God.wav",                       # night air
    "clatter":    "One Shots/Drums/Misc Percussion/Perc Metallic Clatter.aif",  # the shutter's slats
    "squeak":     "One Shots/Drums/FX Hit/FX Squeak.aif",                 # the chair's spring
    "rough":      "One Shots/Drums/Wood/Wood Rough Low.aif",              # wood creak, a door's body
    "breath":     "One Shots/FX/Riser Taka Breath.wav",                   # a breath out (its tail)
    "paper":      "Loops/Texture/Paper LDre.wav",                         # cloth-like rustle: the coat
    "maracas":    "One Shots/Drums/Shaker/Shake Maracas Soft.aif",        # a sleeve's swish
}


# ── loading and basic processing ──
def S(key: str) -> np.ndarray:
    """A Core Library sample as (2, n) float32 at 48 kHz (cached conversion)."""
    p = CL / P[key]
    st = p.stat()
    h = hashlib.sha1(f"{P[key]}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16]
    c = CACHE / f"{h}.npy"
    if c.exists():
        return np.load(c)
    x, sr = sf.read(str(p), dtype="float64", always_2d=True)
    x = x.T
    x = np.vstack([x, x]) if x.shape[0] == 1 else x[:2]
    if sr != SR:
        g = np.gcd(SR, sr)
        x = signal.resample_poly(x, SR // g, sr // g, axis=1)
    x = x.astype(np.float32)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(c, x)
    return x


def M(key: str) -> np.ndarray:
    return S(key).mean(0)


def speed(x: np.ndarray, ratio: float) -> np.ndarray:
    """Varispeed: ratio > 1 plays faster and higher (like a tape)."""
    if abs(ratio - 1) < 1e-4:
        return x.copy()
    f = Fraction(ratio).limit_denominator(400)
    return signal.resample_poly(x, f.denominator, f.numerator, axis=-1).astype(np.float32)


def st(x: np.ndarray, semis: float) -> np.ndarray:
    return speed(x, 2 ** (semis / 12))


def cut(x: np.ndarray, t0: float, t1: float | None = None, a: float = .001, r: float = .01) -> np.ndarray:
    y = x[..., int(t0 * SR): None if t1 is None else int(t1 * SR)].copy()
    return cq.fade(y, a, r)


def filt(x, kind, fc, order=2):
    return cq.sos_filter(x, kind, fc, order).astype(np.float32)


def peq(x, f0, gain_db, q=1.0):
    """RBJ peaking EQ."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=-1).astype(np.float32)


def shelf(x, f0, gain_db, high=True):
    """RBJ shelf (S = 1)."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / 2 * np.sqrt(2)
    c, sA = np.cos(w), 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + sA), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sA)]
        a = [(A + 1) - (A - 1) * c + sA, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sA]
    else:
        b = [A * ((A + 1) - (A - 1) * c + sA), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sA)]
        a = [(A + 1) + (A - 1) * c + sA, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sA]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=-1).astype(np.float32)


def tame(x, thr_db=-9.0, ratio=4.0):
    """A fast peak compressor for spiky foley (clicks, the lock's bolt): ~0.3 ms attack, 25 ms release, so a click
    keeps its snap but stops poking 10 dB out of the mix. Returns the clip renormalised to peak 1."""
    a = np.abs(x).max(0) if x.ndim == 2 else np.abs(x)
    a = maximum_filter1d(a, int(.0006 * SR) + 1)
    rel = np.exp(-1 / (.025 * SR))
    env = signal.lfilter([1 - rel], [1, -rel], a)
    env = np.maximum(env, a * .5)
    thr = 10 ** (thr_db / 20) * a.max()
    over = np.maximum(env / thr, 1.0)
    g = over ** (1 / ratio - 1)
    return peak1((x * g).astype(np.float32))


def peak1(x):
    return x / (np.abs(x).max() + 1e-12)


def mix_at(parts: list[tuple[np.ndarray, float, float]]) -> np.ndarray:
    """Sum mono parts [(x, t, gain)] into one mono clip."""
    n = max(int(t * SR) + len(x) for x, t, g in parts)
    out = np.zeros(n, np.float32)
    for x, t, g in parts:
        i = int(t * SR)
        out[i:i + len(x)] += g * x
    return out


def onset(x: np.ndarray, rel_db: float = -20.0) -> float:
    """Seconds to the first sample within rel_db of the clip's peak."""
    a = np.abs(x if x.ndim == 1 else x.max(0))
    return float(np.argmax(a >= a.max() * 10 ** (rel_db / 20)) / SR)


# ── the spaces ──
# Rooms are short convolution reverbs (compose.quorum.make_ir, unit energy). Each effect goes dry plus a send.
SPACES = {
    #            rt60, length, lowpass, predelay, send highpass
    "office":   (0.38, 0.9, 6500, .006, 180),          # the back office: small, books and a carpet
    "workshop": (1.05, 2.0, 4800, .018, 160),          # the workshop, heard through the door
    "world":    (1.30, 2.6, 8500, .012, 250),          # Barnaby's worlds: a soft, slightly magic air
    "lisbon":   (0.45, 1.1, 8000, .007, 200),          # Theo's flat: plaster, a window
}
DEFAULT_SEND = {"office": .22, "workshop": .55, "world": .38, "lisbon": .25}


class Buses:
    def __init__(self, n: int):
        self.n = n
        self.dry = np.zeros((2, n), np.float32)
        self.send = {k: np.zeros((2, n), np.float32) for k in SPACES}

    def put(self, x, t, gain, pan=0.0, space="office", send=None, width=0.0, dry=True):
        """Place a mono (or stereo) clip: dry at gain, plus `send` of it into the space's room."""
        if x.ndim == 1 and width > 0:                  # a little width: a 0.4-1.1 ms offset copy on one side
            d = int(width * SR)
            x = np.stack([x, np.concatenate([np.zeros(d, np.float32), x[:-d]])])
            gl, gr = cq.pan_gains(pan)
            x = x * np.array([[gl], [gr]], np.float32)
            pan = 0.0
        if dry:
            cq.place(self.dry, x, t, gain, pan)
        s = DEFAULT_SEND[space] if send is None else send
        if s:
            cq.place(self.send[space], x, t, gain * s, pan)

    def render(self) -> np.ndarray:
        out = self.dry.copy()
        for k, (rt, ln, lp, pd, hp) in SPACES.items():
            b = self.send[k]
            if np.abs(b).max() < 1e-7:
                continue
            ir = cq.make_ir(rt, ln, f"room-{k}", lp=lp, predelay=pd)
            out += cq.convolve(filt(b, "highpass", hp), ir).astype(np.float32)
        return out


# ── one-shots ──
def rng(*k):
    return cq.rng_for("foley", *k)


def mouse(seed, weight=1.0, modern=False):
    """The old shop mouse: a plastic latch going down, a lighter click coming up ~90 ms later. Theo's modern mouse in
    Lisbon: the same gesture, smaller and crisper (higher, shorter, a lighter release)."""
    r = rng("mouse", seed, modern)
    down = cut(M("cassette"), .046, None, a=.0005, r=.02)  # the latch alone (the sample's slide-in before it is cut)
    down = st(down, r.uniform(-.6, .6) + (2.5 if modern else -1.0))
    if modern:
        down = cut(down, 0, .035, r=.012)
    up = cut(st(M("vinyl"), (6 if modern else 4) + r.uniform(-.5, .5)), 0, .03 if modern else .035, r=.012)
    y = mix_at([(down, 0, 1.0), (up, (.07 if modern else .085) + r.uniform(-.012, .012), (.22 if modern else .32) * weight)])
    y = filt(filt(y, "highpass", 600 if modern else 380), "lowpass", 11000 if modern else 9000)
    y = peq(y, 3400 if modern else 2600, 3.0, 1.2)     # the plastic's bite
    y = peak1(y)
    return y, onset(y)                              # the latch lands ~8 ms into the clip


def key_tap(seed):
    """The shop key laid on the keyboard: the coin's first impact (a small clean metal tap, its ring damped by the keys)
    on a soft plastic tap."""
    m = cut(M("coin"), .045, .2, a=.0005, r=.09)
    m = filt(m, "highpass", 900)
    p = cut(st(M("plastic2"), -2), 0, .08, r=.03)
    y = mix_at([(m, 0, 1.0), (filt(p, "lowpass", 5000), .002, .35)])
    y = peak1(y)
    return y, onset(y)


def lamp(seed):
    """The desk lamp's push switch: a click down and the latch catching."""
    a = st(M("cassette"), -4)
    b = cut(st(M("vinyl"), 2), 0, .05, r=.02)
    y = mix_at([(b, 0, .7), (a, .012, 1.0)])
    y = filt(filt(y, "highpass", 250), "lowpass", 8000)
    y = peq(y, 1800, 2.0, 1.0)
    y = peak1(y)
    return y, onset(y, -30)                          # the switch's first contact on the cue


def key_turn(seed):
    """A real key turning in a lock (the recording as is: the key in, the turn, the bolt), trimmed of its lead-in."""
    y = cut(M("lock"), .05, None, a=.003, r=.06)
    y = filt(filt(y, "highpass", 140), "lowpass", 11000)
    y = peq(y, 3200, -2.0, 1.0)                        # a touch less bright: on the desk, not in the ear
    y = peak1(y)
    return y, onset(y)


def keys_jingle(seed):
    """Martin's keys as he puts his coat on: three handfuls of the jingle, overlapping, with a metal rattle."""
    r = rng("jingle", seed)
    j = M("jingle")
    parts = [(st(j, r.uniform(-.5, .5)), 0.0, 1.0), (st(j, .6 + r.uniform(-.3, .3)), .19, .5)]
    y = filt(mix_at(parts), "highpass", 500)
    y = peak1(y)
    return y, onset(y)


def clunk(seed):
    """The repair stand's clamp releasing: the lever's crack, the heavy clunk of the jaw, a short metal ring."""
    r = rng("clunk", seed)
    lever = cut(st(M("hit_hard"), r.uniform(-1, 1)), 0, .25, r=.08)
    jaw = cut(st(M("metal"), -2 + r.uniform(-1, 1)), 0, .5, r=.25)
    ring = cut(st(M("pan"), r.uniform(-.7, .7)), 0, .7, r=.4)
    y = mix_at([(lever, 0, .6), (jaw, .035, 1.0), (ring, .04, .25)])
    y = filt(filt(y, "highpass", 70), "lowpass", 5000)
    y = peak1(y)
    return y, onset(y)


def compressor(seed, dur=2.4):
    """The workshop's air compressor, off-screen: the motor spinning up (the machine-noise loop, varispeed), the piston's
    chug, the air."""
    n = int(dur * SR)
    m = M("machine")
    loop = np.concatenate([m] * 3)
    t = np.arange(n) / SR
    rate = .55 + .45 * np.minimum(1, t / .35) ** .6    # spinning up
    pos = np.cumsum(rate) * .8
    motor = np.interp(pos, np.arange(len(loop)), loop).astype(np.float32)
    motor = filt(motor, "lowpass", 2200)
    chug = 1 + .4 * np.sin(2 * np.pi * np.cumsum(9 + 15 * np.minimum(1, t / .35)) / SR)
    air = filt(filt(M("sink")[int(2 * SR): int(2 * SR) + n], "highpass", 1200), "lowpass", 6000)
    y = motor * chug / (np.abs(motor).max() + 1e-9) + .3 * air[:n] / (np.abs(air).max() + 1e-9)
    e = np.minimum(1, t / .12) * np.minimum(1, (dur - t) / .45)
    return peak1((y * e).astype(np.float32)), 0.0


def freewheel(seed, dur=2.6):
    """A freewheel ticking down after a wheel is spun: pawl clicks (sampled grains), slowing."""
    r = rng("fw", seed)
    g = cut(M("tiny"), 0, .012, r=.006)
    parts, t, rate = [], 0.0, 24.0
    while t < dur:
        parts.append((st(g, 6 + r.uniform(-.5, .5)), t, r.uniform(.6, 1) * (1 - .6 * t / dur)))
        t += 1 / rate
        rate = max(5.0, rate * .972)
    y = filt(mix_at(parts), "highpass", 1500)
    return peak1(y), 0.0


def hdd(dur, seed):
    """The 2009 PC's hard drive seeking: short sampled ticks, irregular, with the case's small resonance."""
    r = rng("hdd", seed, dur)
    g = cut(M("tiny"), 0, .01, r=.005)
    parts, t = [], 0.0
    while t < dur:
        parts.append((st(g, r.uniform(-3, 2)), t, r.uniform(.35, 1) if t > 0 else 1.0))   # the first seek is the hardest
        t += r.choice([.016, .024, .038, .06, .1, .19], p=[.25, .25, .2, .15, .1, .05])
    y = mix_at(parts)
    y = peq(filt(filt(y, "highpass", 400), "lowpass", 6500), 900, 5.0, 3.0)    # the drive cage rings a little
    return peak1(y), 0.0


def typing(dur, seed, modern=False):
    """Keyboard foley. Theo's old shop keyboard: tall plastic keys, a clack down and a tick up, a heavier space bar.
    His modern one in Lisbon: low, soft, quick."""
    r = rng("typing", seed, modern)
    downs = [M("plastic1"), M("plastic2")]
    up = cut(M("prod"), 0, .05, r=.02)
    parts, t, k, nxt = [], 0.0, 0, int(r.integers(4, 8))
    while t < dur:
        space = k == nxt
        if space:
            nxt += int(r.integers(4, 8))
        d = downs[r.integers(0, 2)]
        if modern:
            d = filt(cut(st(d, -4 + r.uniform(-1, 1)), 0, .05, r=.02), "lowpass", 3800)
            parts.append((d, t, r.uniform(.5, .8)))
        else:
            d = cut(st(d, (-3 if space else 0) + r.uniform(-1.5, 1.5)), 0, .07, r=.03)
            parts.append((d, t, (1.0 if space else r.uniform(.55, .9))))
            parts.append((st(up, 3 + r.uniform(-1, 1)), t + r.uniform(.07, .11), r.uniform(.15, .25)))
        k += 1
        gap = r.uniform(.07, .13) if modern else r.uniform(.09, .19)
        if r.random() < (.08 if modern else .12):
            gap += r.uniform(.2, .45)                  # a word ends; a short think
        t += gap
    y = mix_at(parts)
    y = filt(filt(y, "highpass", 300 if modern else 220), "lowpass", 7500 if modern else 9000)
    y = peq(y, 500 if not modern else 380, -7.0, 1.5)   # the plastic samples ring at ~500 Hz: a key, not a bottle
    if not modern:
        y = peq(y, 2200, 2.5, 1.0)
    return peak1(y), 0.0


def step(seed, foot=0):
    """Barnaby's steps in his worlds: soft and stylised. A felted tap with a little cloth-mallet pitch (D or A)."""
    r = rng("step", seed)
    tap = filt(cut(st(M("hit_soft"), -5 + r.uniform(-.5, .5)), 0, .16, r=.08), "lowpass", 1400)
    tone = cut(st(M("marimba"), (2 if foot % 2 == 0 else -3) - 12 + r.uniform(-.05, .05)), 0, .22, r=.15)
    y = mix_at([(tap, 0, 1.0), (filt(tone, "lowpass", 900), .004, .35)])
    y = peak1(filt(y, "highpass", 90))
    return y, onset(y)


def drawer(seed):
    """The parts drawer in Barnaby's world: a wooden slide (the scratch, slowed) and a soft stop."""
    sl = filt(st(M("scratch"), -7), "lowpass", 3500)
    sl = sl * np.linspace(.5, 1, len(sl)).astype(np.float32)
    stop = filt(st(M("wood_low"), -3), "lowpass", 2500)
    y = mix_at([(sl, 0, .7), (stop, len(sl) / SR - .02, 1.0)])
    return peak1(y), 0.0


def radio_off(seed):
    """The workshop radio switched off: a small dry switch click (the radio bed stops on it)."""
    y = mix_at([(cut(st(M("vinyl"), -2), 0, .05, r=.02), 0, 1.0), (cut(st(M("cassette"), -5), .046, None, r=.015), .006, .5)])
    y = peak1(filt(filt(y, "highpass", 300), "lowpass", 6000))
    return y, onset(y)


def shutter(seed, dur=2.6):
    """A roller shutter pulled down, off-screen: the slats rattling down the guides (the metallic clatter, slowed and
    looped, pulsing as each slat rolls over), a rumble in the drum, and the bottom bar landing."""
    n = int(dur * SR)
    r = rng("shutter", seed)
    c = st(M("clatter"), -5)
    c = np.concatenate([c, c[::-1], c])[: n]
    c = np.pad(c, (0, max(0, n - len(c))))
    t = np.arange(n) / SR
    rate = 9 + 5 * np.minimum(1, t / .6)                 # slats per second, the pull speeding up
    pulse = .3 + .7 * np.abs(np.sin(np.pi * np.cumsum(rate) / SR)) ** 2
    rum = filt(st(loop_to(S("machine"), int(n * 1.6), seed, xf=.3)[0], -8)[:n], "lowpass", 300)
    rum = np.pad(rum, (0, max(0, n - len(rum))))
    sl = filt(filt(c * pulse, "lowpass", 4500), "highpass", 250)
    rms_ = lambda v: np.sqrt((v ** 2).mean()) + 1e-9
    body = sl / rms_(sl) + .2 * rum / rms_(rum)          # by RMS: the slats lead, the drum only underneath
    body = body * np.minimum(1, t / .04) * np.clip((dur - .1 - t) / .2, 0, 1)
    land = cut(st(M("metal"), -4 + r.uniform(-.5, .5)), 0, .6, r=.3)
    y = mix_at([(body.astype(np.float32), 0, .8), (filt(land, "lowpass", 3500), dur - .15, 1.0)])
    y = peak1(filt(y, "highpass", 60))
    return y, 0.0


def chair(seed):
    """An office chair taking someone's weight: the spring's squeak (low), the seat's creak, the cushion, then a small
    breath out."""
    sq = filt(st(M("squeak"), -7), "lowpass", 4000)
    creak = filt(cut(st(M("rough"), -5), 0, .6, r=.25), "lowpass", 2500)
    seat = filt(cut(st(M("hit_soft"), -8), 0, .2, r=.1), "lowpass", 500)
    br = M("breath")
    br = filt(filt(cut(br, 1.62, None, a=.05, r=.2), "lowpass", 2800), "highpass", 250)
    y = mix_at([(seat, 0, .8), (creak, .02, .7), (sq, .09, .35), (br, .45, .22)])
    y = peak1(filt(y, "highpass", 70))
    return y, onset(y)


def cup(seed):
    """An espresso cup set down on its saucer: one clean ceramic clink (from the tea-cups recording) and a tiny settle."""
    x = M("cups")
    clink = cut(x, 2.865, 3.35, a=.0008, r=.15)
    settle = cut(x, 3.935, 4.06, a=.0008, r=.05)
    y = mix_at([(clink, 0, 1.0), (settle, .075, .18)])
    y = peak1(filt(filt(y, "highpass", 350), "lowpass", 12000))
    return y, onset(y)


def coat(seed):
    """A coat going on: the cloth's rustle (the paper texture, slowed and darkened) and two sleeve swishes."""
    rus = filt(st(M("paper"), -4), "lowpass", 3000)
    sw = filt(st(M("maracas"), -10), "lowpass", 2200)
    y = mix_at([(sw, 0, .6), (rus, .1, 1.0), (sw, .55, .45)])
    y = peak1(filt(y, "highpass", 180))
    return y, onset(y, -30)


def door(seed, size=1.0):
    """A door closing: the latch (the lock recording's bolt) and the door's wooden body (a rough low wood hit, pitched
    down by the door's size)."""
    latch = filt(cut(M("lock"), .33, .62, a=.001, r=.12), "lowpass", 5000)
    body = filt(cut(st(M("rough"), -7 - 3 * (size - 1)), 0, .5, r=.25), "lowpass", 1200)
    y = mix_at([(body, 0, 1.0), (latch, .012, .45)])
    y = peak1(filt(y, "highpass", 80))
    return y, onset(y)


CHIME = [-10, -6, -3, 2]                               # celeste C6 -> D5, F#5, A5, D6: the hand-back's four steps
STEPS4 = ("the job", "the customer", "a text", "the status")


def chime(note: int, dur: float):
    """One note of the hand-back figure: the celeste, tuned down to D5 / F#5 / A5 / D6, short."""
    y = cut(st(M("celeste"), CHIME[note]), 0, dur + .04, a=.0005, r=.6 * dur)
    y = peak1(filt(filt(y, "lowpass", 6000), "highpass", 250))
    return y, onset(y)


def chime_chord(dur: float = 2.6):
    """The four notes as one chord: the steps have become one."""
    c = M("celeste")
    y = mix_at([(cut(st(c, n), 0, dur, a=.0005, r=.6 * dur), 0, g) for n, g in zip(CHIME, (1.0, .8, .75, .7))])
    y = peak1(filt(filt(y, "lowpass", 6000), "highpass", 200))
    return y, onset(y)


PENTA = [0, 2, 4, 7, 9, 12, 14]                       # D major pentatonic, from D


def pop(seed, k=0):
    """A soft pop in Barnaby's world: a water drip, tuned up the D pentatonic."""
    y = st(M("drip"), -5 + PENTA[k % len(PENTA)] + rng("pop", seed).uniform(-.05, .05))
    y = filt(filt(y, "lowpass", 4200), "highpass", 250)
    y = peak1(y)
    return y, onset(y)


def ding(seed):
    """Checks pass: the celeste on D, with a quiet A above."""
    c = M("celeste")
    y = mix_at([(cut(st(c, 2), 0, 2.2, r=.8), 0, 1.0), (cut(st(c, 9), 0, 1.6, r=.6), .07, .35)])
    y = peak1(filt(y, "lowpass", 7000))
    return y, onset(y)


def timelapse(dur, seed):
    """Time passes: a soft noise swell with a bowl underneath (tuned to D)."""
    sw = M("swell")
    y = speed(sw, len(sw) / SR / (dur + .4))
    bowl = st(M("bowl"), 3)[: len(y)]
    y = filt(y, "lowpass", 4500) + .35 * filt(np.pad(bowl, (0, len(y) - len(bowl))), "lowpass", 1500)
    e = np.minimum(1, np.arange(len(y)) / SR / (.6 * dur))
    return peak1((y * e).astype(np.float32)), 0.0


# the brass counter bell
def _partials(x, t0, freqs, win=.12):
    """Complex amplitude of each partial at t0 (Hann-windowed projection), refined frequency."""
    n = int(win * SR)
    i0 = int(t0 * SR) - n // 2
    seg = x[i0:i0 + n].astype(np.float64)
    w = np.hanning(n)
    tt = (np.arange(n) - n // 2) / SR
    out = []
    for f in freqs:
        best = max(np.linspace(f * .99, f * 1.01, 81), key=lambda g: abs((seg * w * np.exp(-2j * np.pi * g * tt)).sum()))
        c = 2 * (seg * w * np.exp(-2j * np.pi * best * tt)).sum() / w.sum()
        out.append((best, c))
    return out


def bell(soft=False):
    """The brass counter bell. The recording (Core Library 'Bell Cash': a small struck bell with a 1 : 1.52 : 2.28 : 6.6
    partial set) gives the strike and the first 0.2 s; from there a modal model continues each partial with the same
    frequency, amplitude and phase, but the long ring of a counter bell's dome (T60 5 s on the fundamental), with a
    slow beat from each mode's slightly split doublet. Tuned to E6 (the 9th of D: it sits in the score's last chord).
    soft=True: the bell's soft confirm, the strike rounded off and darker."""
    x = M("bell")
    x = st(x, 12 * np.log2(1318.5 / 1296.0))            # E6
    x = x[int(onset(x, -30) * SR):]
    t0, xf = .2, .25
    parts = _partials(x, t0, [1318.5, 1318.5 * 1.515, 1318.5 * 2.282, 1318.5 * 6.6])
    t60 = [5.0, 1.8, 3.4, 1.0]
    beat = [(.9, .15), (1.7, .15), (1.3, .2), (3.1, .15)]  # doublet beat (Hz, depth)
    dur = 6.0
    n = int(dur * SR)
    t = np.arange(n) / SR
    model = np.zeros(n)
    for (f, c), T, (bf, bd) in zip(parts, t60, beat):
        tau = T / 6.9078
        env = np.exp(-np.maximum(t - t0, 0) / tau) * (1 - bd + bd * np.cos(2 * np.pi * bf * np.maximum(t - t0, 0)))
        model += np.real(c * np.exp(2j * np.pi * f * (t - t0))) * env
    w = np.clip((t - t0) / xf, 0, 1)
    w = .5 - .5 * np.cos(np.pi * w)                    # raised-cosine hand-over from the recording to the model
    rec = np.zeros(n)
    rec[: min(n, len(x))] = x[:n]
    # the recording's own decay keeps going under the model (it carries the strike's noise and the room)
    y = rec * (1 - .7 * w) + 1.15 * model * w           # the ring carries on at (a touch over) the strike's level
    y = filt(y.astype(np.float32), "highpass", 400)
    y = cq.fade(y, 0, .5)
    if soft:
        y = filt(y, "lowpass", 3800)
        y = y * (1 - np.exp(-t / .012)).astype(np.float32)
    return peak1(y), 0.0


# ── beds ──
def loop_to(x: np.ndarray, n: int, seed, xf=1.0, lo=0.0, hi=None, ranges=None) -> np.ndarray:
    """Fill n samples (stereo) from random stretches of x[lo:hi] (or of the given (lo, hi) ranges, in seconds), joined
    with equal-power crossfades."""
    r = rng("loop", seed)
    parts = [x[:, int(a * SR): None if b is None else int(b * SR)] for a, b in (ranges or [(lo, hi)])]
    F = int(xf * SR)
    out = np.zeros((2, n + F), np.float32)
    pos, first = 0, True
    while pos < n:
        x = parts[int(r.integers(0, len(parts)))]
        L = x.shape[1]
        seg = min(L, max(F * 3, int(r.uniform(.5, 1) * L)))
        s0 = int(r.integers(0, max(1, L - seg)))
        c = x[:, s0:s0 + seg].copy()
        if not first:
            c[:, :F] *= np.sin(np.linspace(0, np.pi / 2, F))
        c[:, -F:] *= np.cos(np.linspace(0, np.pi / 2, F))
        m = min(c.shape[1], out.shape[1] - pos)
        out[:, pos:pos + m] += c[:, :m]
        pos += seg - F
        first = False
    return out[:, :n]


def gate_env(n, seed, on=.4, min_len=2.0, max_len=7.0, floor=.12):
    """A slow random on/off envelope: someone working, then not."""
    r = rng("gate", seed)
    e = np.zeros(n, np.float32)
    t = 0
    while t < n:
        L = int(r.uniform(min_len, max_len) * SR)
        e[t:t + L] = 1.0 if r.random() < on else floor
        t += L
    return uniform_filter1d(e, int(.6 * SR)).astype(np.float32)


def room_tone(n, seed, lp=180):
    """A low room tone (synth: brown noise, there is no clean room tone in the library)."""
    r = rng("tone", seed)
    x = np.cumsum(r.standard_normal((2, n)), axis=1)
    x = filt(filt(x, "highpass", 30), "lowpass", lp)
    return x / (np.sqrt((x ** 2).mean()) + 1e-12)


def traffic(n, seed, night=False):
    """Road traffic below a window (synth: there is none in the library): low rumble with cars passing, each a swell
    with a slow pan and a slight Doppler-like filter sweep."""
    r = rng("traffic", seed, night)
    base = room_tone(n, seed + 7, lp=260) * (.25 if night else .45)
    t = np.arange(n) / SR
    out = base.copy()
    cars = int(n / SR / (7 if night else 2.8))
    for _ in range(cars):
        c, w = r.uniform(0, n / SR), r.uniform(1.8, 3.5)
        g = np.exp(-((t - c) / w) ** 2) * r.uniform(.4, 1.0)
        i0, i1 = max(0, int((c - 3 * w) * SR)), min(n, int((c + 3 * w) * SR))
        if i1 - i0 < SR:
            continue
        seg = r.standard_normal(i1 - i0)
        seg = cq.tv_biquad(seg, "lowpass", np.linspace(500, 900, i1 - i0) * np.interp(np.arange(i1 - i0), [0, (i1 - i0) / 2, i1 - i0], [.8, 1.3, .7]))
        seg = filt(seg, "highpass", 60)
        p = np.linspace(r.uniform(-.8, -.2), r.uniform(.2, .8), i1 - i0) * (1 if r.random() < .5 else -1)
        gl, gr = cq.pan_gains(p)
        out[0, i0:i1] += 1.2 * seg * g[i0:i1] * gl
        out[1, i0:i1] += 1.2 * seg * g[i0:i1] * gr
    return out


def radio_speaker(x):
    """A small radio's speaker, then a wall: band-limited, a little saturated, boxy."""
    y = filt(filt(x, "highpass", 450), "lowpass", 3000)
    y = peq(y, 1100, 4.0, 1.4)
    y = np.tanh(2.5 * y / (np.abs(y).max() + 1e-9)) / 2.5
    return filt(y.astype(np.float32), "lowpass", 2400)


def bed(typ: str, n: int, seed: int) -> np.ndarray:
    """A stereo ambience bed of n samples, normalised to unit RMS (levels are set in BED_GAIN)."""
    def unit(x):
        x = filt(x, "highpass", 45)
        return x / (np.sqrt((x ** 2).mean()) + 1e-12)

    if typ == "rain":                                  # rain on the window: the steady stretch, softened by the glass
        x = loop_to(S("rain"), n, seed, xf=2.0, ranges=[(8.0, 22.5), (52.0, 64.0)])   # no gusts, no train
        x = tame(shelf(filt(filt(x, "highpass", 110), "lowpass", 7500), 2500, -3.0), -16, 2)
        return unit(x)
    if typ == "fan":                                   # the PC's fan: the machine loop, spun up from rest
        m = loop_to(S("machine"), n + SR, seed, xf=.5)
        t = np.arange(n) / SR
        rate = .25 + .75 * np.minimum(1, t / 1.6) ** .7
        pos = np.cumsum(rate)
        y = np.stack([np.interp(pos, np.arange(m.shape[1]), m[c]) for c in range(2)]).astype(np.float32)
        y = filt(filt(y, "highpass", 70), "lowpass", 3200)
        y = y * np.minimum(1, t / 1.0).astype(np.float32)
        return unit(y)
    if typ == "radio":                                 # a radio far off in the workshop
        x = loop_to(S("radio"), n, seed, xf=1.5)
        return unit(radio_speaker(x.mean(0))[None, :].repeat(2, 0))
    if typ == "office_night":                          # the back office at night: room tone, a distant machine hum
        tone = room_tone(n, seed, lp=160)
        hum = loop_to(S("machine"), n, seed + 1, xf=.5)
        hum = filt(st(hum, -5)[:, :n], "lowpass", 400)
        hum = np.pad(hum, ((0, 0), (0, n - hum.shape[1])))
        return unit(tone + .5 * hum / (np.sqrt((hum ** 2).mean()) + 1e-12))
    if typ in ("workshop", "bustle"):                  # the workshop: room tone and tools now and then (no voices)
        busy = typ == "bustle"
        tone = room_tone(n, seed, lp=220)
        nuts = loop_to(S("nuts"), n, seed + 1, xf=1.0)
        nuts = tame(filt(filt(nuts, "lowpass", 5000), "highpass", 300), -30, 4) * gate_env(
            n, seed + 2, on=.4 if busy else .25, min_len=1.5, max_len=4.0, floor=.05)
        nuts = nuts / (np.sqrt((nuts ** 2).mean()) + 1e-12)
        y = .7 * tone + .45 * nuts
        if busy:                                       # Tuesday: more hands at the trays, a mug now and then
            cups = filt(loop_to(S("cups"), n, seed + 5, xf=.5), "lowpass", 6000) * gate_env(n, seed + 6, on=.15, floor=0)
            cups = cups / (np.sqrt((cups ** 2).mean()) + 1e-12)
            y = y + .2 * cups
        return unit(y)
    if typ in ("street", "street_night"):              # below Theo's window in Lisbon: traffic, birds, night air
        night = typ == "street_night"
        y = traffic(n, seed, night)
        y = y / (np.sqrt((y ** 2).mean()) + 1e-12)
        if night:
            wind = filt(loop_to(S("wind"), n, seed + 5, xf=1.0, lo=0.0, hi=5.5), "lowpass", 2500)
            wind = wind / (np.sqrt((wind ** 2).mean()) + 1e-12)
            y = y + .35 * wind
        else:
            birds = filt(loop_to(S("birds"), n, seed + 5, xf=1.0), "highpass", 1500)
            birds = birds / (np.sqrt((birds ** 2).mean()) + 1e-12)
            y = y + .2 * birds
        return unit(filt(y, "lowpass", 6000 if not night else 4500))   # through the window
    raise ValueError(typ)


# the level audit's categories (check.py --levels)
CATEGORIES = {
    "rain": {"rain"}, "fan (2009 PC)": {"fan"}, "radio (scene 1)": {"radio"}, "room tone (back office)": {"office_night"},
    "workshop": {"workshop"}, "workshop, Tuesday": {"bustle"}, "Lisbon street": {"street"},
    "Lisbon street, night": {"street_night"},
    "foley": {"key_tap", "lamp_click", "lamp_on", "key_turn", "keys_jingle", "clunk", "compressor", "freewheel", "hdd",
              "typing", "keys_modern", "chair", "cup", "coat", "door_shop", "door_lisbon", "shutter", "radio_off"},
    "UI (clicks, reload, pops, ding)": {"tab", "tab_close", "mouse_click", "reload", "pop", "ding"},
    "worlds (steps, chimes, drawer, soft bells, swell)": {"step", "chime", "chime_chord", "drawer", "bell_soft", "timelapse"},
    "the bell": {"bell"},
}

# ambience levels as RMS before the master (the voices sit near -20 dBFS RMS)
BED_GAIN = {"rain": .006, "fan": .004, "radio": .0035, "office_night": .005, "workshop": .0065, "bustle": .009,
            "street": .008, "street_night": .0065}   # v2.3: the beds well under the dialogue (SOUND.md, levels table)
BED_PAN = {"fan": -.25, "radio": .45}

SOURCES = {
    "tab": [P["cassette"], P["vinyl"]],
    "tab_close": [P["cassette"], P["vinyl"]],
    "mouse_click": [P["cassette"], P["vinyl"]],
    "key_tap": [P["coin"], P["plastic2"]],
    "lamp_click": [P["cassette"], P["vinyl"]],
    "key_turn": [P["lock"]],
    "keys_jingle": [P["jingle"]],
    "radio_off": [P["vinyl"], P["cassette"]],
    "shutter": [P["clatter"], P["machine"], P["metal"]],
    "chair": [P["hit_soft"], P["rough"], P["squeak"], P["breath"]],
    "lamp_on": [P["cassette"], P["vinyl"]],
    "cup": [P["cups"]],
    "coat": [P["paper"], P["maracas"]],
    "door_shop": [P["rough"], P["lock"]],
    "door_lisbon": [P["rough"], P["lock"]],
    "clunk": [P["hit_hard"], P["metal"], P["pan"]],
    "compressor": [P["machine"], P["sink"]],
    "freewheel": [P["tiny"]],
    "hdd": [P["tiny"]],
    "reload": [P["tiny"], P["machine"]],
    "typing": [P["plastic1"], P["plastic2"], P["prod"]],
    "keys_modern": [P["plastic1"], P["plastic2"]],
    "step": [P["hit_soft"], P["marimba"]],
    "drawer": [P["scratch"], P["wood_low"]],
    "pop": [P["drip"]],
    "ding": [P["celeste"]],
    "timelapse": [P["swell"], P["bowl"]],
    "bell": [P["bell"], "modal ring (fitted to the sample)"],
    "bell_soft": [P["bell"], "modal ring (fitted to the sample)"],
    "rain": [P["rain"]],
    "fan": [P["machine"]],
    "radio": [P["radio"]],
    "office_night": ["synth: room tone", P["machine"]],
    "workshop": ["synth: room tone", P["nuts"]],
    "bustle": ["synth: room tone", P["nuts"], P["cups"]],
    "chime": [P["celeste"]],
    "chime_chord": [P["celeste"]],
    "street": ["synth: traffic", P["birds"]],
    "street_night": ["synth: traffic", P["wind"]],
}


# how each kind of cue is built and placed (SOUND.md is generated from this, SOURCES and the measurements)
PROCESS = {
    "tab": "old shop mouse: the cassette's latch (from 46 ms) -1 st (down) + vinyl click +4 st 85 ms later (up); HP 380 Hz, LP 9 kHz, "
           "+3 dB at 2.6 kHz; fast peak compressor; a little width; office room 22 %; pan follows the tab a little",
    "tab_close": "as tab, a little lighter",
    "mouse_click": "the shop: as tab (the old shop mouse). Lisbon: Theo's modern mouse, +2.5 st, shorter, HP 600 Hz, "
                   "+3 dB at 3.4 kHz, Lisbon room",
    "key_tap": "the coin's first impact only (45-200 ms: the ring damped by the keys), HP 900 Hz, on a plastic tap -2 st "
               "LP 5 kHz; fast compressor; office room 18 %",
    "lamp_click": "vinyl click +2 st, then the cassette latch -4 st 12 ms later; HP 250 Hz, LP 8 kHz, +2 dB at 1.8 kHz; "
                  "fast compressor; panned left (the lamp); office room",
    "key_turn": "the lock recording as is (lead-in trimmed): the key in, the turn, the bolt; HP 140 Hz, LP 11 kHz, -2 dB "
                "at 3.2 kHz; fast compressor; office room 25 %; the score ducks 5 dB around it",
    "keys_jingle": "two overlapping handfuls of the jingle (+-0.5 st), HP 500 Hz, LP 6 kHz; "
                   "off-screen: workshop room 70 %, panned left, low",
    "clunk": "the lever's crack (hit, +-1 st) + the jaw's clunk (metal impact -2 st, 35 ms later) + a short pan ring; "
             "HP 70 Hz, LP 5 kHz; off-screen: workshop room 75 %, panned right, low",
    "compressor": "a 1.2 s run: the machine loop varispeed-spun up (0.55 -> 1.0 in 0.35 s), LP 2.2 kHz, a 9-24 Hz chug, air "
                  "hiss (sink noise, BP 1.2-6 kHz); off-screen: workshop room 80 %, panned right",
    "freewheel": "12 ms grains of the tiny perc +6 st at 24 Hz slowing to 5 Hz, HP 1.5 kHz; off-screen: workshop room",
    "hdd": "10 ms grains of the tiny perc (-3..+2 st) at irregular seek intervals, HP 400 Hz, LP 6.5 kHz, a +5 dB "
           "resonance at 900 Hz (the drive cage); under the desk, left; office room 12 %",
    "reload": "a 0.55 s burst of the drive's seeks + the fan bed rising and falling over 1.8 s",
    "typing": "the old keyboard: plastic taps (two samples, +-1.5 st; the space bar -3 st and louder) with a soft wooden "
              "upstroke +3 st 70-110 ms later; word gaps; HP 220 Hz, LP 9 kHz, -7 dB at 500 Hz (the samples' plastic ring), "
              "+2.5 dB at 2.2 kHz; office room",
    "keys_modern": "Theo's modern keyboard: the same taps -4 st, 50 ms long, LP 3.8 kHz, -7 dB at 380 Hz, quicker, no upstroke; "
                   "Lisbon room",
    "step": "a soft hit -5 st LP 1.4 kHz + a cloth-mallet marimba note an octave down (D or A, alternate feet) LP 900 Hz; "
            "Barnaby's world room 30 %; alternate pan +-0.08 (the marimba is on D or A)",
    "radio_off": "a dry switch: vinyl click -2 st + the cassette latch -5 st, HP 300 Hz, LP 6 kHz; through the workshop "
                 "door (workshop room 60 %, right); the radio bed stops on it",
    "shutter": "the metallic clatter -5 st, looped (forward, reversed) to the cue's length and pulsed at 9-14 slats a second, "
               "BP 250 Hz-4.5 kHz, a little rumble (machine loop -8 st LP 300 Hz), and the bottom bar landing (metal impact -4 st, LP 3.5 "
               "kHz) at the end; off-screen: workshop room 85 %, right, low",
    "chair": "the cushion (soft hit -8 st LP 500 Hz), the seat's creak (rough wood -5 st LP 2.5 kHz), the spring's squeak "
             "-7 st LP 4 kHz, and a breath out 0.45 s later (the breath riser's tail, BP 250 Hz-2.8 kHz); office room 20 %",
    "lamp_on": "as lamp_click (another take of the same switch)",
    "cup": "one clink from the tea-cups recording (2.865-3.35 s) and a small settle (3.935 s) 75 ms later, HP 350 Hz; "
           "Lisbon room 22 %",
    "coat": "the paper rustle -4 st LP 3 kHz (cloth) between two sleeve swishes (soft maracas -10 st LP 2.2 kHz); "
            "off-screen: workshop room 45 %, left, low",
    "door_shop": "a door = its wooden body (rough low wood -7 st, LP 1.2 kHz) + the latch (the lock's bolt, LP 5 kHz); the "
                 "back-office door, then 1.7 s later the shop door, bigger, darker (LP 2.5 kHz), further off (90 % room)",
    "door_lisbon": "the same door, smaller, LP 3.5 kHz, off in Theo's flat (Lisbon room 70 %), right",
    "drawer": "the wood scratch -7 st (a slow slide, LP 3.5 kHz, rising) and a dry wood knock -3 st as it stops; world room",
    "pop": "a water drip tuned up the D major pentatonic, LP 4.2 kHz, HP 250 Hz; six rising pops 75 ms apart for 'six "
           "light up', two for 'two rows change'; world room 40 %",
    "ding": "the celeste on D (+2 st) with a quiet A above 70 ms later, LP 7 kHz; world room 45 %",
    "timelapse": "a noise swell varispeeded to the cue's length, LP 4.5 kHz, with a singing bowl +3 st (B -> D) LP 1.5 kHz; "
                 "world room",
    "bell": "the counter bell: Bell Cash tuned +0.3 st to E6; the recording's strike for 0.2 s, then a modal ring fitted to "
            "its own four partials (1318, 1998, 3009, 8700 Hz: amplitude and phase measured at 0.2 s; T60 5.0, 1.8, 3.4, "
            "1.0 s; slow doublet beats), a raised-cosine hand-over over 0.25 s with the recording kept at 30 % under it; "
            "HP 400 Hz; office room 35 % (50 % for the last bell) plus an air halo in the world room; the score ducks "
            "3 dB for the last one",
    "bell_soft": "the same bell, its strike rounded (12 ms attack) and darker (LP 3.8 kHz), lower, world room 70 %",
    "rain": "rain on the window: random 7-15 s stretches of the steady rain (2 s crossfades), HP 110 Hz, LP 7.5 kHz, "
            "-3 dB shelf above 2.5 kHz (the glass), gentle peak compression",
    "fan": "the machine loop varispeeded up from 25 % over 1.6 s (the fan spinning up), BP 70 Hz-3.2 kHz, panned left",
    "radio": "the radio recording through a small speaker (BP 450 Hz-3 kHz, +4 dB at 1.1 kHz, soft saturation, LP 2.4 "
             "kHz), panned right, very low",
    "office_night": "a low room tone (synth: brown noise LP 160 Hz) with the machine loop -5 st LP 400 Hz under it",
    "workshop": "room tone (synth) + tools now and then (the parts trays: nuts and bolts, BP 300 Hz-5 kHz, peak-compressed, "
                "on a slow random gate ~25 % on, peak-compressed hard so no clink pokes out); no voices, no radio",
    "bustle": "the same, busier (gate ~40 % on), and a mug now and then; no voices",
    "street": "traffic below the window (synth: a rumble and passing cars, each a filtered noise swell with a slow pan) + "
              "birds (HP 1.5 kHz); LP 6 kHz (the window); no voices",
    "street_night": "sparser traffic (synth) + night air (wind, LP 2.5 kHz); LP 4.5 kHz",
    "chime": "the hand-back figure, one note per step: the celeste tuned to D5, F#5, A5, D6 (-10, -6, -3, +2 st), cut to "
             "1.2x the step interval (0.54 s, 0.31 s, 0.2 s), LP 6 kHz; panned left to right across the four stops; world room 35 %",
    "chime_chord": "the four notes at once (D5 F#5 A5 D6), 2.6 s, LP 6 kHz; world room 45 %; replaces the passage's soft "
                   "bell",
}


def handback_chimes(cues: dict) -> list[dict]:
    """Scene 5: each of a hand-back's four steps (the job, the customer, a text, the status) gets one note of the same
    figure, D-F#-A-D, on Barnaby's steps from the cue sheet: walk 1, then quicker in walk 2 and walk 3 (where the sheet
    has no steps, they are derived, quicker again). At the passage, and for Tom's one step, the four notes sound as one
    chord."""
    mk = cues["marks"]
    steps = sorted(float(s["t"]) for s in cues["sfx"] if s["type"] == "step")
    walks = [w for w in ("walk1", "walk2", "walk3") if w in mk]
    out, iv = [], .45
    for i, w in enumerate(walks):
        end = mk[walks[i + 1]] if i + 1 < len(walks) else mk.get("passage", mk[w] + 3)
        ts = [t for t in steps if mk[w] <= t < end][:4]
        if len(ts) == 4:
            iv = (ts[-1] - ts[0]) / 3
        else:                                          # derived: the same walk, quicker still
            iv = max(.15, iv * .65)
            ts = [round(mk[w] + .12 + k * iv, 3) for k in range(4)]
            out += [{"t": t, "type": "step", "gain": .13, "label": f"Barnaby's walk {i + 1}, quicker (derived from marks.{w})"}
                    for t in ts]
        dur = float(np.clip(1.2 * iv, .18, .9))          # each note as long as its step: crisper as he speeds up
        out += [{"t": t, "type": "chime", "note": k, "dur": round(dur, 3), "gain": .3,
                 "label": f"hand-back chime {k + 1}/4 ({STEPS4[k]}), walk {i + 1}"} for k, t in enumerate(ts)]
    if "passage" in mk:
        out.append({"t": round(mk["passage"] + .35, 3), "type": "chime_chord", "gain": .3,
                    "label": "the passage: the four notes as one chord"})
    if "walk4" in mk:
        out.append({"t": round(mk["walk4"] + .05, 3), "type": "chime_chord", "gain": .26,
                    "label": "Tom's Brompton in one step: the chord once"})
    return out


def extra_cues(cues: dict) -> list[dict]:
    """Effects the beat sheet describes but cues.json -> sfx does not carry (voice timing is not ours to change):
    Barnaby's steps across the workshop floor and the parts drawer in scene 3, and the back office's night tone."""
    mk = cues["marks"]
    # the film walks him from marks.walk to drawer 1 by marks.pads_callout - 0.15 (video/v2/film/scenes/s3.js)
    t0, t1 = mk["walk"] + .15, mk["pads_callout"] - .35
    n = int((t1 - t0) / .42) + 1
    out = [{"t": round(t0 + k * (t1 - t0) / max(1, n - 1), 3), "type": "step", "gain": .13 if 0 < k < n - 1 else .1,
            "label": "Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout)"}
           for k in range(n)]
    out += handback_chimes(cues)
    out.append({"t": round(mk["shelf"] + .3, 3), "type": "drawer", "gain": .3,
                "label": "drawer 1 of the parts cabinet slides open in the shelf shot (derived from marks.shelf)"})
    out.append({"t": 0.0, "type": "office_night", "level": 1.0, "fade_in": 2.5, "until": mk["timelapse"] + 1.6,
                "label": "the back office at night (derived: scenes 1-2)"})
    out.append({"t": mk["shop_night"], "type": "office_night", "level": .8, "fade_in": 1.2, "until": mk["end"],
                "label": "the back office at night (derived: scene 9)"})
    return out


def render(cues: dict, n: int, voice_env: np.ndarray | None = None, only: set | None = None):
    """All effects and beds (or only the cue types in `only`). Returns (sfx (2,n), ambience (2,n), report rows)."""
    cq.N, cq.DUR = n, n / SR                          # the helpers (place, convolve) work on buses of the film's length
    cq.T = np.arange(n, dtype=np.float64) / SR
    fx = Buses(n)
    amb = np.zeros((2, n), np.float32)
    report = []
    lisbon = (cues["marks"]["lisbon_wide"], cues["marks"]["shop_night"])
    items = sorted(cues["sfx"] + extra_cues(cues), key=lambda s: s["t"])
    # the passage's soft bell gives way to the chime chord (the steps become one)
    pas = cues["marks"].get("passage")
    if pas is not None:
        items = [s for s in items if not (s["type"] == "bell_soft" and abs(float(s["t"]) - pas) < 1.0)]
    radio_off_t = min((float(s["t"]) for s in items if s["type"] == "radio_off"), default=None)
    pops = 0
    for k, s in enumerate(items):
        typ, t = s["type"], float(s["t"])
        if only is not None and typ not in only:
            continue
        g = float(s.get("gain", .5))
        pan = float(s.get("pan", 0.0))
        if typ in BED_GAIN:
            until = float(s.get("until", n / SR))
            fi, fo = float(s.get("fade_in", .6 if "leads the cut" in s.get("label", "") else 1.0)), 1.6
            if typ == "radio" and radio_off_t and t < radio_off_t < until:
                until, fo = radio_off_t + .02, .03    # switched off: it stops on the click
            m = int((until - t) * SR)
            y = bed(typ, m, k)
            tt = np.arange(m) / SR
            e = np.minimum(1, tt / fi) * np.clip((until - t - tt) / fo, 0, 1)
            y = y * (e * BED_GAIN[typ] * float(s.get("level", 1.0))).astype(np.float32)
            if typ in BED_PAN:
                gl, gr = cq.pan_gains(BED_PAN[typ])
                y = y * np.array([[gl], [gr]], np.float32)
            cq.place(amb, y, t, 1.0)
            report.append((s, typ, "bed", t, None))
            continue
        in_lisbon = lisbon[0] <= t < lisbon[1]
        if typ in ("tab", "tab_close", "mouse_click"):
            y, o = mouse(k, .8 if typ != "mouse_click" else 1.0, modern=in_lisbon)
            y = tame(y, -10)
            gg = {"tab": .12, "tab_close": .09, "mouse_click": .2 * g / .55}[typ]
            fx.put(y, t - o, gg, .1 + pan * .25, "lisbon" if in_lisbon else "office", width=.0006)
        elif typ == "key_tap":
            y, o = key_tap(k)
            fx.put(tame(y, -8), t - o, .19 * g / .6, .05, "office", send=.18)
        elif typ == "lamp_click":
            y, o = lamp(k)
            fx.put(tame(y, -9), t - o, .15 * g / .55, -.35, "office")
        elif typ == "key_turn":
            y, o = key_turn(k)
            fx.put(tame(y, -10), t - o, .38 * g / .65, .15, "office", send=.25, width=.0008)
        elif typ == "keys_jingle":
            y, o = keys_jingle(k)
            fx.put(filt(y, "lowpass", 6000), t - o, .1 * g / .3, -.35, "workshop", send=.7)
        elif typ == "clunk":
            y, o = clunk(k)
            fx.put(y, t - o, .09 * g / .5, .4, "workshop", send=.75)
        elif typ == "compressor":
            y, o = compressor(k, 1.2)                  # short, and done before Barnaby starts walking
            fx.put(y, t - o, .028 * g / .22, .5, "workshop", send=.8)
        elif typ == "freewheel":
            y, o = freewheel(k, 1.6)
            fx.put(y, t - o, .06 * g / .3, .45, "workshop", send=.8)
        elif typ == "hdd":
            y, o = hdd(float(s.get("dur", .5)), k)
            fx.put(tame(y, -8), t - o, .05, -.3, "office", send=.12)
        elif typ == "reload":                          # the old PC works: the drive chatters, the fan rises
            y, o = hdd(.55, k)
            fx.put(tame(y, -8), t - o, .1 * g / .25, -.3, "office", send=.12)
            f = bed("fan", int(1.8 * SR), k)[0]
            f = f * np.sin(np.pi * np.arange(len(f)) / len(f)) ** 2
            fx.put(f.astype(np.float32), t, .006, -.3, "office", send=.1)
        elif typ in ("typing", "keys_modern"):
            modern = typ == "keys_modern"
            y, o = typing(float(s.get("dur", 2.0)), k, modern)
            fx.put(tame(y, -10), t - o, (.14 if modern else .17) * g / .55, .1 if modern else -.05, "lisbon" if modern else "office",
                   send=.18, width=.0005)
        elif typ == "step":
            foot = int(round(t * 10))
            y, o = step(k, foot)
            fx.put(y, t - o, .075 * g / .16, .08 * (1 if foot % 2 else -1), "world", send=.3)
        elif typ == "radio_off":
            y, o = radio_off(k)
            fx.put(y, t - o, .11 * g / .4, .45, "workshop", send=.6)
        elif typ == "shutter":
            y, o = shutter(k, float(s.get("dur", 2.6)))
            fx.put(y, t - o, .09 * g / .45, .5, "workshop", send=.85, width=.0009)
        elif typ == "chair":
            y, o = chair(k)
            fx.put(y, t - o, .095 * g / .4, -.15, "office", send=.2)
        elif typ == "lamp_on":
            y, o = lamp(k + 101)
            fx.put(tame(y, -9), t - o, .15 * g / .55, -.35, "office")
        elif typ == "cup":
            y, o = cup(k)
            fx.put(y, t - o, .13 * g / .35, .2, "lisbon", send=.22)
        elif typ == "coat":
            y, o = coat(k)
            fx.put(y, t - o, .1 * g / .3, -.3, "workshop", send=.45)
        elif typ == "door_shop":                       # the back-office door, then the shop door further off
            y, o = door(k, 1.0)
            fx.put(y, t - o, .13 * g / .35, -.3, "workshop", send=.5)
            y2, _ = door(k + 1, 1.4)
            fx.put(filt(y2, "lowpass", 2500), t - o + 1.7, .045 * g / .35, -.45, "workshop", send=.8)
        elif typ == "door_lisbon":
            y, o = door(k, .8)
            fx.put(filt(y, "lowpass", 3500), t - o, .08 * g / .3, .35, "lisbon", send=.7)
        elif typ == "drawer":
            y, o = drawer(k)
            fx.put(y, t - o, .12 * g / .3, .15, "world", send=.3)
        elif typ == "pop":
            many = 6 if "six" in s.get("label", "") else 2 if "two" in s.get("label", "") else 1
            for j in range(many):
                y, o = pop(k, j + (2 if many == 1 else 0))
                fx.put(y, t - o + j * .075, .105 * g / .18 * (1 - .05 * j), -.25 + .1 * j if many > 1 else .1, "world", send=.4)
            pops += many
        elif typ == "ding":
            y, o = ding(k)
            fx.put(y, t - o, .1 * g / .25, .1, "world", send=.45)
        elif typ == "timelapse":
            d = float(s.get("dur", 2.0))
            y, o = timelapse(d, k)
            fx.put(y, t - o, .09 * g / .35, 0, "world", send=.3, width=.0011)
        elif typ == "bell":
            y, o = bell()
            final = t > n / SR - 20
            fx.put(y, t - o, .3 * g / .5, .1, "office", send=.5 if final else .35, width=.0007)
            fx.put(y, t - o, .3 * g / .5 * .5, .1, "world", send=1.0, dry=False)    # and a halo of air
        elif typ == "chime":
            note = int(s["note"])
            y, o = chime(note, float(s["dur"]))
            fx.put(y, t - o, .13 * g / .3, -.15 + .1 * note, "world", send=.35)
        elif typ == "chime_chord":
            y, o = chime_chord()
            fx.put(y, t - o, .11 * g / .3, 0.0, "world", send=.45, width=.0007)
        elif typ == "bell_soft":
            y, o = bell(soft=True)
            fx.put(y, t - o, .1 * g / .3, .05, "world", send=.7, width=.0007)
        else:
            print("  ! no foley for", typ)
            continue
        report.append((s, typ, "one-shot", t, t - o + onset(y)))
    sfx = fx.render()
    return sfx, filt(amb, "highpass", 40), report


def reel(path: Path) -> list[tuple[float, str]]:
    """Every one-shot design, dry and alone, one after another (for auditioning): .cache/audio/foley_reel.wav."""
    items = [("mouse (old shop)", mouse(1)), ("mouse (Lisbon, modern)", mouse(1, modern=True)), ("key tap", key_tap(1)),
             ("lamp switch", lamp(1)), ("key turn", key_turn(1)), ("keys jingle", keys_jingle(1)), ("clunk", clunk(1)),
             ("compressor", compressor(1, 1.8)), ("freewheel", freewheel(1)), ("hard drive", hdd(1.6, 1)),
             ("typing (old)", typing(4.2, 1)), ("typing (modern)", typing(1.0, 1, True)), ("steps", None),
             ("drawer", drawer(1)), ("pops (six)", None), ("ding", ding(1)), ("time-lapse swell", timelapse(2.2, 1)),
             ("bell", bell()), ("bell (soft)", bell(soft=True))]
    out, marks, t = [], [], 0.5
    for name, yo in items:
        if name == "steps":
            y = mix_at([(step(k, k)[0], .4 * k, .8) for k in range(4)])
        elif name.startswith("pops"):
            y = mix_at([(pop(1, k)[0], .075 * k, .8) for k in range(6)])
        else:
            y = yo[0]
        marks.append((round(t, 2), name))
        out.append((y, t, .7))
        t += len(y) / SR + .8
    x = mix_at(out)
    sf.write(str(path), np.stack([x, x], 1), SR, subtype="PCM_16")
    return marks


if __name__ == "__main__":
    dst = ROOT / ".cache" / "audio" / "foley_reel.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    for t, name in reel(dst):
        print(f"{t:7.2f}  {name}")
    print("wrote", dst)
