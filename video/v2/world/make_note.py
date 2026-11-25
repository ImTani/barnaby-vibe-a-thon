"""Theo's sticky note, hand-written: an ink-density texture for the note on the shop monitor's bezel.

"Reports: coming soon (sorry Uncle M)" in Theo's hand (Segoe Print letterforms, CONTINUITY.md) written with a black
felt-tip on a 76 mm note. Every glyph is its own: rendered, then warped by a smooth random field, rotated, scaled and
sheared, set on a wandering, slightly rising baseline with uneven spacing, so no two r's or o's match. The letters are
then thinned to their centre lines and re-stroked with a felt-tip: an even nib with a little width and pressure
variation, ink pooling where the pen lands and lifts, darker where strokes cross, a faint bleed into the paper. The
underline under "Reports:" (a quick stroke: heavy start, thin flicked end) and the small sad face are drawn as strokes.

Output: note_theo.png next to this file, 8-bit grey = ink density (white = none), mapped onto the note by desk.py
(UV 0..1 = the note's face, top of the image = the note's top edge, where the adhesive strip is).

Run with any Python that has Pillow, numpy and scipy (system Python here):
    python video/v2/world/make_note.py [--preview]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "note_theo.png")
FONT = r"C:\Windows\Fonts\segoepr.ttf"           # Theo's hand (CONTINUITY.md)
N = 2048                                          # texture size (px)
NOTE_MM = 76.0
PX = N / NOTE_MM                                  # px per mm
R0 = 0.45 * PX                                    # felt-tip half-width (a 0.9 mm nib)
RNG = np.random.default_rng(1119)                 # Thu 19 Nov

# (text, size spec, x, baseline, tilt deg (negative rises to the right), horizontal squeeze), all in mm
LINES = [
    ("Reports:", ("cap", 9.4), 6.8, 19.6, -1.6, 1.0),
    ("coming soon", ("x", 5.4), 5.4, 35.6, -0.9, 1.0),
    ("(sorry Uncle M)", ("x", 3.8), 6.2, 49.0, -0.5, 0.9),
]


def font_for(spec):
    kind, mm = spec
    probe = ImageFont.truetype(FONT, 1000)
    box = probe.getbbox("H" if kind == "cap" else "x", anchor="ls")
    ratio = (box[3] - box[1]) / 1000.0
    return ImageFont.truetype(FONT, max(8, int(round(mm * PX / ratio))))


def glyph_mask(ch, f, pad):
    """A glyph as a float mask, and its pen origin (left, baseline) in the mask."""
    asc, desc = f.getmetrics()
    adv = f.getlength(ch)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * pad)
    im = Image.new("L", (max(w, 4), max(h, 4)), 0)
    ImageDraw.Draw(im).text((pad, pad + asc), ch, font=f, fill=255, anchor="ls")
    return np.asarray(im, np.float32) / 255.0, (pad, pad + asc), adv


def stamp_glyph(canvas, mask, origin, at, rot, scale, shear, em, rng):
    """Inverse-map the glyph mask onto the canvas: pen origin at `at`, rotated, scaled, sheared, and warped by a
    smooth random field (about 2.5% of the em), so each instance of a letter is shaped a little differently."""
    th = math.radians(rot)
    A = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]) @ \
        np.array([[scale[0], shear * scale[1]], [0.0, scale[1]]])
    Ai = np.linalg.inv(A)
    h, w = mask.shape
    reach = int(max(h, w) * max(scale) * 1.3) + 8
    x0, y0 = int(at[0]) - reach, int(at[1]) - reach
    x1, y1 = int(at[0]) + reach, int(at[1]) + reach
    x0c, y0c, x1c, y1c = max(x0, 0), max(y0, 0), min(x1, N), min(y1, N)
    yy, xx = np.mgrid[y0c:y1c, x0c:x1c].astype(np.float32)
    u, v = (xx - at[0]) / em, (yy - at[1]) / em
    f1, f2, f3 = rng.uniform(0.5, 1.3, 3)
    p1, p2, p3 = rng.uniform(0, 2 * math.pi, 3)
    amp = 0.025 * em
    dx = amp * np.sin(2 * math.pi * (f1 * v + p1)) + 0.5 * amp * np.sin(2 * math.pi * (f3 * u + p3))
    dy = amp * np.sin(2 * math.pi * (f2 * u + p2))
    qx, qy = xx - at[0] - dx, yy - at[1] - dy
    sx = Ai[0, 0] * qx + Ai[0, 1] * qy + origin[0]
    sy = Ai[1, 0] * qx + Ai[1, 1] * qy + origin[1]
    patch = ndi.map_coordinates(mask, [sy, sx], order=1, cval=0.0)
    canvas[y0c:y1c, x0c:x1c] = np.maximum(canvas[y0c:y1c, x0c:x1c], patch)
    return (x0c, y0c, x1c, y1c)


def write_line(canvas, pressure, text, spec, x_mm, base_mm, tilt, squeeze, rng):
    f = font_for(spec)
    em = f.size
    pad = int(em * 0.3)
    x = x_mm * PX
    phase = rng.uniform(0, 2 * math.pi)
    for ch in text:
        adv = f.getlength(ch) * squeeze
        if ch == " ":
            x += adv * rng.uniform(0.85, 1.15)
            continue
        s = 1.0 + rng.normal(0, 0.045)
        y = (base_mm * PX + math.tan(math.radians(tilt)) * (x - x_mm * PX)
             + 0.32 * PX * math.sin(x / (8.5 * PX) + phase) + rng.normal(0, 0.24) * PX)
        mask, origin, _ = glyph_mask(ch, f, pad)
        box = stamp_glyph(canvas, mask, origin, (x, y), tilt + rng.normal(0, 3.0),
                          (s * squeeze * rng.uniform(0.95, 1.05), s * rng.uniform(0.95, 1.05)),
                          rng.normal(-0.04, 0.06), em, rng)
        x0, y0, x1, y1 = box
        region = canvas[y0:y1, x0:x1] > 0.5
        pressure[y0:y1, x0:x1][region] = rng.uniform(0.92, 1.0)          # this letter's pen pressure
        x += adv * s * rng.uniform(0.96, 1.08)
    return x / PX, base_mm + math.tan(math.radians(tilt)) * (x / PX - x_mm)


def thin(img):
    """Zhang-Suen thinning: the letters' centre lines."""
    img = img.astype(np.uint8)
    while True:
        changed = False
        for step in (0, 1):
            P = np.pad(img, 1)
            p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
            p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
            p8, p9 = P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(n.astype(np.int16) for n in nb)
            seq = nb + [p2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                c = ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
            else:
                c = ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)
            m = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                img[m] = 0
                changed = True
        if not changed:
            return img.astype(bool)


def neighbours(sk):
    P = np.pad(sk.astype(np.int16), 1)
    return sum(P[1 + dy:P.shape[0] - 1 + dy, 1 + dx:P.shape[1] - 1 + dx]
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)


def prune(sk, length):
    """Drop the short spurs thinning leaves at sharp corners (branches shorter than `length` px ending in a fork)."""
    sk = sk.copy()
    nbc = neighbours(sk)
    ends = np.argwhere(sk & (nbc == 1))
    offs = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    for y, x in ends:
        path, prev, cur = [(y, x)], None, (y, x)
        while len(path) <= length:
            nxt = [(cur[0] + dy, cur[1] + dx) for dy, dx in offs
                   if 0 <= cur[0] + dy < N and 0 <= cur[1] + dx < N and sk[cur[0] + dy, cur[1] + dx]
                   and (cur[0] + dy, cur[1] + dx) != prev and (cur[0] + dy, cur[1] + dx) not in path]
            if len(nxt) != 1:
                if len(nxt) >= 2 and len(path) < length:              # reached a fork soon: it was a spur
                    for p in path[:-1]:
                        sk[p] = False
                break
            prev, cur = cur, nxt[0]
            path.append(cur)
    return sk


def stroke_path(points_mm, r_scale, d_vals, sk, R, D):
    """Draw a pen stroke's centre line into the skeleton with its own width and density along it."""
    pts = np.array(points_mm, float) * PX
    seg = np.diff(pts, axis=0)
    L = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    t = np.linspace(0, L[-1], int(L[-1] * 2) + 2)
    xs, ys = np.interp(t, L, pts[:, 0]), np.interp(t, L, pts[:, 1])
    f = t / max(L[-1], 1e-6)
    rs, ds = np.interp(f, np.linspace(0, 1, len(r_scale)), r_scale), np.interp(f, np.linspace(0, 1, len(d_vals)), d_vals)
    iy, ix = np.clip(np.round(ys).astype(int), 0, N - 1), np.clip(np.round(xs).astype(int), 0, N - 1)
    sk[iy, ix] = True
    R[iy, ix] = R0 * rs
    D[iy, ix] = ds
    return (ix[0], iy[0]), (ix[-1], iy[-1])


def smooth_noise(sigma, rng):
    n = ndi.gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), sigma)
    return (n - n.mean()) / (n.std() + 1e-6)


def main():
    letters = np.zeros((N, N), np.float32)
    pressure = np.ones((N, N), np.float32)
    ends = []
    for k, (text, spec, x, base, tilt, sq) in enumerate(LINES):
        ends.append(write_line(letters, pressure, text, spec, x, base, tilt, sq, np.random.default_rng(1119 + k)))
    sk = prune(thin(letters > 0.5), int(R0 * 1.1))
    # per-pixel stroke width and ink density along the centre lines
    wobble = smooth_noise(40, RNG)
    R = np.where(sk, R0 * (1.0 + 0.06 * wobble), 0).astype(np.float32)
    D = np.where(sk, pressure * (0.97 + 0.025 * smooth_noise(25, RNG)), 0).astype(np.float32)
    skl = sk.copy()
    # the quick underline under "Reports:": lands heavy, sweeps right and a touch up, thins and flicks off
    rx = ends[0][0]
    ux0, uy0 = LINES[0][2] - 0.6, LINES[0][3] + 3.4
    ux1 = rx + 1.2
    tilt0 = math.tan(math.radians(LINES[0][4] - 1.2))
    under = []
    for f in np.linspace(0, 1, 40):
        xm = ux0 + (ux1 - ux0) * f
        under.append((xm, uy0 + tilt0 * (xm - ux0) + 0.55 * math.sin(math.pi * f) + 0.18 * math.sin(7.0 * f + 0.6)
                      - 1.6 * max(0, f - 0.9) ** 1.5 * 10))
    under_start, under_end = stroke_path(under, [1.08, 1.0, 0.95, 0.8, 0.45], [1.0, 0.95, 0.9, 0.75, 0.5], skl, R, D)
    # the small sad face after "(sorry Uncle M)"
    fx, fy = ends[2][0] + 4.4, ends[2][1] - 2.0
    rr = 2.75
    circle = [(fx + rr * math.cos(a) * (1 + 0.04 * math.sin(3 * a)), fy + rr * 0.96 * math.sin(a))
              for a in np.linspace(math.radians(-104), math.radians(238), 48)]
    stroke_path(circle, [0.78, 0.74, 0.74, 0.62], [0.95, 0.9, 0.88, 0.75], skl, R, D)
    for ex in (-0.95, 0.9):
        stroke_path([(fx + ex, fy - 1.05), (fx + ex + 0.06, fy - 0.68)], [0.8, 0.8], [1.0, 1.0], skl, R, D)
    mouth = [(fx + 1.25 * math.cos(a), fy + 1.95 + 1.25 * math.sin(a)) for a in np.linspace(math.radians(212),
                                                                                         math.radians(328), 14)]
    stroke_path(mouth, [0.72, 0.66], [0.95, 0.8], skl, R, D)
    # ink pools where the pen lands and lifts (stroke ends; not the underline's flicked tail), darker at crossings
    nbc = neighbours(skl)
    endpoints = (skl & (nbc <= 1)).astype(np.float32)
    ey, ex_ = under_end[1], under_end[0]
    endpoints[max(ey - 6, 0):ey + 7, max(ex_ - 6, 0):ex_ + 7] = 0
    sig = R0 * 0.85
    blob = np.clip(ndi.gaussian_filter(endpoints * 2 * math.pi * sig * sig, sig), 0, 1.4)
    cross = np.clip(ndi.gaussian_filter((skl & (nbc >= 3)).astype(np.float32) * 2 * math.pi * 36, 6), 0, 1)
    R = np.where(skl, R * (1 + 0.16 * blob), 0)
    D = np.where(skl, np.clip(D + 0.25 * blob + 0.12 * cross, 0, 1.15), 0)
    # felt-tip coverage: distance from the centre lines against the local nib radius, 1 px anti-aliased edge
    dist, (iy, ix) = ndi.distance_transform_edt(~skl, return_indices=True)
    Rn, Dn = R[iy, ix], D[iy, ix]
    cov = np.clip(Rn - dist + 0.5 + 0.7 * np.clip(smooth_noise(1.6, RNG), -2, 2), 0, 1)   # a ragged felt edge
    ink = cov * Dn
    ink = 0.86 * ink + 0.14 * ndi.gaussian_filter(ink, 2.2)              # a faint bleed into the fibres
    ink *= 0.93 + 0.07 * np.clip(smooth_noise(1.2, RNG), -2, 2) / 2      # the paper's tooth
    out = (255 * (1 - np.clip(ink * 1.05, 0, 1))).astype(np.uint8)
    Image.fromarray(out, "L").save(OUT)
    print("wrote", OUT, f"({N}x{N}, nib {2 * R0 / PX:.2f} mm)")
    if "--preview" in sys.argv:
        prev = Image.new("RGB", (N, N), (235, 208, 98))
        ink_rgb = Image.new("RGB", (N, N), (26, 28, 36))
        prev = Image.composite(ink_rgb, prev, Image.fromarray((255 - out).astype(np.uint8), "L"))
        prev.save(os.path.join(HERE, "out", "_scratch", "note_preview.png"))


if __name__ == "__main__":
    main()
