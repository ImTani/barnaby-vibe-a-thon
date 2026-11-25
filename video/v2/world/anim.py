"""Barnaby film v2: motion for the approved 3D stills (cameras, lights, object moves, screen swaps). Nothing here
changes the sets: it builds desk.py / lisbon.py exactly as approved, then animates on top and renders JPEG sequences.

Run from the repo root (Git Bash), ONE Blender at a time:
    source scripts/env.sh
    "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
        --python video/v2/world/anim.py -- --set shop --shots s1_open,s2_key [--samples 24] [--test 1,mid,last]

    --set shop|lisbon   which set to build (each set renders only its own shots)
    --shots a,b         shot ids (see SHOTS below; default: every Tier A shot of the set)
    --samples N         Eevee samples (default 24)
    --scale P           resolution percentage (default 100)
    --test LIST         render only these frames (numbers, or first/mid/last) to out/anim/_test/ (no manifest)
    --tmp               re-render beside finished work: sequences to out/anim/_tmp_<id>/, stills to out/_tmp_<file>,
                        no manifest update (swap the old away and the new in, then update the manifest)
    --compose           (no build) join the two halves of s9_two_desks with ffmpeg, then exit

Timing: video/v2/cues.json is the clock; spans come from the animatic (anim/spans.js resolves them). Every shot is
its on-screen span plus 12 frames of handle each side, 24 fps, frame 0001 = film time `start` in anim/shots.json.
Output: out/anim/<shot_id>/0001.jpg ... (gitignored). The manifest anim/shots.json is updated as shots finish.
"""
import json
import math
import os
import subprocess
import sys
import time
from math import cos, exp, pi, radians, sin

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
OUT_ANIM = os.path.join(HERE, "out", "anim")
MANIFEST = os.path.join(HERE, "anim", "shots.json")
FPS, HANDLE = 24, 12


# ------------------------------------------------------------------------------------------------ easing and time
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def sine(x):
    return 0.5 - 0.5 * cos(pi * clamp01(x))


def smoother(x):
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def bezier(x1, y1, x2, y2):
    """CSS cubic-bezier easing."""
    def f(x):
        x = clamp01(x)
        lo, hi = 0.0, 1.0
        for _ in range(40):
            s = (lo + hi) / 2
            bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
            if bx < x:
                lo = s
            else:
                hi = s
        s = (lo + hi) / 2
        return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
    return f


SLOW_SETTLE = bezier(0.42, 0.0, 0.22, 1.0)        # gentle start, long settle
DRIFT = bezier(0.37, 0.0, 0.63, 1.0)             # a soft symmetric drift
CALM = bezier(0.3, 0.0, 0.7, 1.0)                # a slow, nearly even drift (trims well anywhere)
LONG_RES = (1600, 900)                           # the long re-timed shots render here and are upscaled to 1080p


def P(t, a, d):
    return clamp01((t - a) / d)


def lerp(a, b, u):
    return a + (b - a) * u


def catmull(pts, u):
    """Centripetal-ish Catmull-Rom through pts (Vectors), u in [0, 1] mapped by chord length."""
    if len(pts) == 2:
        return pts[0].lerp(pts[1], u)
    lens = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    tot = sum(lens)
    d = clamp01(u) * tot
    i = 0
    while i < len(lens) - 1 and d > lens[i]:
        d -= lens[i]
        i += 1
    s = d / lens[i] if lens[i] else 0.0
    p0 = pts[i - 1] if i > 0 else pts[0] * 2 - pts[1]
    p1, p2 = pts[i], pts[i + 1]
    p3 = pts[i + 2] if i + 2 < len(pts) else pts[-1] * 2 - pts[-2]
    s2, s3 = s * s, s * s * s
    return 0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3)


def _cr(p0, p1, p2, p3, s, alpha=0.5):
    """Centripetal Catmull-Rom (Barry-Goldman), s in [0, 1] between p1 and p2."""
    def nxt(ti, a, b):
        return ti + max((b - a).length, 1e-6) ** alpha
    t0 = 0.0
    t1 = nxt(t0, p0, p1)
    t2 = nxt(t1, p1, p2)
    t3 = nxt(t2, p2, p3)
    t = t1 + (t2 - t1) * s
    a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
    a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
    a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
    b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
    b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
    return b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1))


class Path:
    """A smooth curve through points, parameterised by arc length (u = fraction of the distance travelled), so an
    eased u gives an eased speed with no jumps at the waypoints."""
    def __init__(self, pts, n=240):
        pts = [Vector(p) for p in pts]
        ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
        self.s = []
        for i in range(len(pts) - 1):
            for k in range(n):
                self.s.append(_cr(ext[i], ext[i + 1], ext[i + 2], ext[i + 3], k / n))
        self.s.append(pts[-1].copy())
        self.c = [0.0]
        for a, b in zip(self.s, self.s[1:]):
            self.c.append(self.c[-1] + (b - a).length)

    def at(self, u):
        import bisect
        d = clamp01(u) * self.c[-1]
        i = min(max(bisect.bisect_right(self.c, d) - 1, 0), len(self.s) - 2)
        seg = self.c[i + 1] - self.c[i]
        return self.s[i].lerp(self.s[i + 1], (d - self.c[i]) / seg if seg > 0 else 0.0)


def span(t0, t1):
    """Frame 0001 time and frame count for an on-screen span [t0, t1] plus the handles."""
    return t0 - HANDLE / FPS, int(round((t1 - t0) * FPS)) + 2 * HANDLE


# ------------------------------------------------------------------------------------------------ the camera rig
RIG = {}


def make_rig(DM):
    ob = DM.camera("ACAM", (0, -1, 1), (0, 0, 1), 35, 2.8, (0, 0, 1))
    RIG["cam"] = ob
    RIG["focus"] = ob.data.dof.focus_object
    bpy.context.scene.camera = ob


def pose(name):
    ob = bpy.data.objects[name]
    loc = Vector(ob.location)
    fwd = ob.rotation_euler.to_quaternion() @ Vector((0, 0, -1))
    foc = Vector(ob.data.dof.focus_object.location)
    dist = max((foc - loc).length, 0.3)
    return dict(loc=loc, tgt=loc + fwd * dist, lens=ob.data.lens, fstop=ob.data.dof.aperture_fstop, focus=foc,
                name=name)


def pixel_point(p, px, py, res=(1920, 1080)):
    """The point at image pixel (px, py) of pose p, at the pose's focus distance."""
    loc = p["loc"]
    d = p["tgt"] - loc
    q = d.to_track_quat("-Z", "Y")
    fwd, right, up = q @ Vector((0, 0, -1)), q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    w, h = res
    sw = 36.0 if w >= h else 36.0 * w / h
    sx = (px / w - 0.5) * sw
    sy = (0.5 - py / h) * sw * h / w
    ray = (fwd * p["lens"] + right * sx + up * sy).normalized()
    dist = (p["focus"] - loc).length
    return loc + ray * dist / max(ray.dot(fwd), 0.2)


def pushed(p, px, py, s, res=(1920, 1080), lens=None):
    """A dolly toward image point (px, py) that magnifies the subject there by s (the animatic's cam zoom)."""
    pt = pixel_point(p, px, py, res)
    loc = p["loc"] + (pt - p["loc"]) * (1 - 1 / s)
    return dict(loc=loc, tgt=pt, lens=lens or p["lens"], fstop=p["fstop"], focus=p["focus"], name=p["name"] + "+")


def set_cam(loc, tgt, lens, focus, fstop):
    ob = RIG["cam"]
    ob.location = loc
    ob.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler("XYZ", ob.rotation_euler)
    ob.data.lens = lens
    ob.data.dof.aperture_fstop = fstop
    RIG["focus"].location = focus


def cam_between(a, b, u):
    set_cam(a["loc"].lerp(b["loc"], u), a["tgt"].lerp(b["tgt"], u), lerp(a["lens"], b["lens"], u),
            a["focus"].lerp(b["focus"], u), lerp(a["fstop"], b["fstop"], u))


# ------------------------------------------------------------------------------------------------ a shot
class Shot:
    def __init__(self, sid, scene, replaces, t0, t1, res=(1920, 1080), notes=""):
        self.id, self.scene, self.replaces, self.t0, self.t1 = sid, scene, replaces, t0, t1
        self.start, self.frames = span(t0, t1)
        self.res, self.notes = res, notes
        self.no_probe = False       # the screen's planar probe costs ~1.8 s/frame: off where no screen is seen
        self.black_until = None     # film time before which the frame is pure black (written, not rendered)
        self.render_until = None    # film time after which the last rendered frame is held (hidden by the film)
        self.upscale_to = None      # (w, h): lanczos-upscale the finished frames (rendered smaller for time)
        self.active = None          # held shots: [(t0, t1)] where something changes; other frames are exact copies
        self.events = {}            # cue-sheet mark -> film time of that story event in this render (-> frame)
        self.samples = None         # per-shot Eevee samples (None: the run's --samples)
        self.segments = []          # [(time the segment starts, setup())]
        self.frame_fn = None        # (t) -> None, continuous state for film time t
        self.out_dir = os.path.join(OUT_ANIM, sid)

    def time(self, f):
        return self.start + (f - 1) / FPS

    def frame(self, t):
        return int(round((t - self.start) * FPS)) + 1

    def seg_ranges(self):
        out = []
        for i, (ts, fn) in enumerate(self.segments):
            fa = 1 if i == 0 else next(f for f in range(1, self.frames + 2) if self.time(f) >= ts - 1e-6)
            out.append([fa, None, fn])
        for i in range(len(out)):
            out[i][1] = out[i + 1][0] - 1 if i + 1 < len(out) else self.frames
        return [tuple(r) for r in out if r[1] >= r[0]]


CUR = {"fn": None, "shot": None}


def _on_frame(scene, depsgraph=None):
    sh, fn = CUR["shot"], CUR["fn"]
    if sh is not None and fn is not None:
        fn(sh.time(scene.frame_current + scene.frame_subframe))


def render_shot(sh, args, test=None):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = sh.res
    sc.render.resolution_percentage = args.scale
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.render.image_settings.color_mode = "RGB"
    sc.render.use_overwrite = bool(args.overwrite)         # resume: frames already on disk are skipped
    sc.eevee.taa_render_samples = sh.samples or args.samples
    sc.camera = RIG["cam"]
    CUR["shot"], CUR["fn"] = sh, sh.frame_fn
    pr = bpy.data.objects.get("screen_probe")
    if pr:
        pr.hide_render = sh.no_probe
    t1 = time.time()
    if test:
        os.makedirs(os.path.join(OUT_ANIM, "_test"), exist_ok=True)
        frames = []
        for k in test:
            frames.append(1 if k == "first" else sh.frames if k == "last" else (sh.frames + 1) // 2 if k == "mid"
                          else int(k))
        for f in frames:
            fa, fb, setup = next(r for r in sh.seg_ranges() if r[0] <= f <= r[1])
            setup()
            sc.frame_set(f)
            sh.frame_fn(sh.time(f))
            sc.render.filepath = os.path.join(OUT_ANIM, "_test", f"{sh.id}_{f:04d}")
            tf = time.time()
            bpy.ops.render.render(write_still=True)
            print(f"TEST {sh.id} frame {f} (t={sh.time(f):.2f}) in {time.time() - tf:.1f}s")
        return
    lo, hi = (int(x) for x in args.range.split("-")) if args.range else (1, sh.frames)
    out_dir = (os.path.join(OUT_ANIM, "_test", sh.id) if args.range else
               os.path.join(OUT_ANIM, "_tmp_" + sh.id) if args.tmp else sh.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    if not args.range and not args.tmp:
        manifest_update(sh, "rendering")
    if sh.black_until is not None and not args.range:
        blk = os.path.join(OUT_ANIM, f"_black_{sh.res[0]}x{sh.res[1]}.jpg")
        if not os.path.exists(blk):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            f"color=black:s={sh.res[0]}x{sh.res[1]}", "-frames:v", "1", "-q:v", "2", blk], check=True)
        import shutil
        for f in range(1, sh.frames + 1):
            if sh.time(f) < sh.black_until:
                shutil.copyfile(blk, os.path.join(out_dir, f"{f:04d}.jpg"))
                lo = f + 1
    if sh.render_until is not None and not args.range:
        hi = max(f for f in range(1, sh.frames + 1) if sh.time(f) <= sh.render_until)
    need = set(range(lo, hi + 1))
    if sh.active is not None and not args.range:          # a held frame with nothing changing: render it once
        act = [any(a <= sh.time(f) <= b for a, b in sh.active) for f in range(sh.frames + 2)]
        need = {f for f in range(lo, hi + 1) if act[f] or f == lo or act[f - 1]}
    for fa, fb, setup in sh.seg_ranges():
        fa, fb = max(fa, lo), min(fb, hi)
        if fb < fa:
            continue
        frs = sorted(f for f in need if fa <= f <= fb)
        if not frs:
            continue
        setup()
        runs, a = [], frs[0]
        for x, y in zip(frs, frs[1:] + [None]):
            if y != x + 1:
                runs.append((a, x))
                a = y
        for ra, rb in runs:
            sc.frame_start, sc.frame_end = ra, rb
            sc.frame_set(ra)
            sc.render.filepath = os.path.join(out_dir, "####")
            bpy.ops.render.render(animation=True)
    if sh.active is not None and not args.range:
        import shutil
        for f in range(lo, hi + 1):
            if f not in need:
                shutil.copyfile(os.path.join(out_dir, f"{f - 1:04d}.jpg"), os.path.join(out_dir, f"{f:04d}.jpg"))
    if sh.render_until is not None and not args.range:
        import shutil
        for f in range(hi + 1, sh.frames + 1):
            shutil.copyfile(os.path.join(out_dir, f"{hi:04d}.jpg"), os.path.join(out_dir, f"{f:04d}.jpg"))
    if args.range:
        dt = time.time() - t1
        print(f"RANGE {sh.id} {lo}-{hi}: {dt:.0f}s ({dt / (hi - lo + 1):.2f} s/frame)")
        return
    if sh.upscale_to:
        upscale(out_dir, sh.upscale_to)
    dt = time.time() - t1
    print(f"RENDERED {sh.id}: {sh.frames} frames in {dt:.0f}s ({dt / sh.frames:.2f} s/frame)")
    with open(os.path.join(OUT_ANIM, "_log.txt"), "a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} {sh.id} {sh.frames}f {dt:.0f}s {dt / sh.frames:.2f}s/f "
                 f"samples={args.samples} scale={args.scale}\n")
    if not sh.id.endswith("_half") and not args.tmp:
        manifest_update(sh, "done")


def upscale(d, size):
    import shutil
    tmp = d + "_up"
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-start_number", "1", "-i", os.path.join(d, "%04d.jpg"),
                    "-vf", f"scale={size[0]}:{size[1]}:flags=lanczos", "-q:v", "2", "-start_number", "1",
                    os.path.join(tmp, "%04d.jpg")], check=True)
    for f in os.listdir(tmp):
        shutil.move(os.path.join(tmp, f), os.path.join(d, f))
    os.rmdir(tmp)


class Still:
    """A held frame (B-still): its own camera pose, state, resolution and samples; written to out/<file>."""
    def __init__(self, sid, scene, file, setup, cam, res=(2560, 1440), samples=32, notes="", ev=0.0, probe=True):
        self.id, self.scene, self.file, self.setup, self.cam = sid, scene, file, setup, cam
        self.res, self.samples, self.notes, self.ev, self.probe = res, samples, notes, ev, probe


def render_still(st, args, test=None):
    sc = bpy.context.scene
    st.setup()
    sc.view_settings.exposure += st.ev
    c = st.cam() if callable(st.cam) else st.cam
    set_cam(c["loc"], c["tgt"], c["lens"], c["focus"], c["fstop"])
    RIG["cam"].data.shift_x = c.get("shift_x", 0.0)
    if "grid" in RIG:
        RIG["grid"]()
    sc.camera = RIG["cam"]
    pr = bpy.data.objects.get("screen_probe")
    if pr:
        pr.hide_render = not st.probe
    sc.render.resolution_x, sc.render.resolution_y = st.res
    sc.render.resolution_percentage = 25 if test else 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    keep = sc.eevee.taa_render_samples
    sc.eevee.taa_render_samples = 4 if test else st.samples
    CUR["shot"] = None
    path = (os.path.join(OUT_ANIM, "_test", st.file) if test else
            os.path.join(HERE, "out", ("_tmp_" if args.tmp else "") + st.file))
    sc.render.filepath = path
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    sc.eevee.taa_render_samples = keep
    RIG["cam"].data.shift_x = 0.0
    print(f"STILL {st.id} -> {os.path.basename(path)} in {time.time() - t1:.0f}s")
    if not test and not args.tmp:
        m = manifest_load()
        e = dict(id=st.id, kind="still", scene=st.scene, file="world/" + st.file, start=None, frames=1,
                 res=list(st.res), status="done", notes=st.notes)
        old = next((x for x in m["shots"] if x["id"] == st.id), {})
        if "screen_quad" in old:
            e["screen_quad"] = old["screen_quad"]
        m["shots"] = [x for x in m["shots"] if x["id"] != st.id] + [e]
        manifest_save(m)


def _corner_world(ob, uv_corners=((0, 1), (1, 1), (1, 0), (0, 0))):
    """World positions of the picture's corners (image UV corners TL, TR, BR, BL) on a screen mesh."""
    me = ob.data
    uvl = me.uv_layers.active.data
    out = []
    for cu, cv in uv_corners:
        best = min(range(len(me.loops)), key=lambda i: (uvl[i].uv[0] - cu) ** 2 + (uvl[i].uv[1] - cv) ** 2)
        out.append(ob.matrix_world @ me.vertices[me.loops[best].vertex_index].co)
    return out


def _project(corners):
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    vs = [world_to_camera_view(sc, RIG["cam"], co) for co in corners]
    if any(v.z <= 0 for v in vs):
        return None
    q = [[round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)] for v in vs]
    xs, ys = [c[0] for c in q], [c[1] for c in q]
    if max(xs) < 0 or min(xs) > 1920 or max(ys) < 0 or min(ys) > 1080:
        return None
    return q


def screen_quads(sh, ob):
    """Per-frame picture corners for a sequence -> manifest "screen_quads": {frame: [TL, TR, BR, BL]} (1920x1080
    output px), every frame where the screen is in view."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.camera = RIG["cam"]
    bpy.context.view_layer.update()
    corners = _corner_world(ob)
    quads = {}
    for fa, fb, setup in sh.seg_ranges():
        setup()
        for f in range(fa, fb + 1):
            sh.frame_fn(sh.time(f))
            bpy.context.view_layer.update()
            q = _project(corners)
            if q:
                quads[str(f)] = q
    m = manifest_load()
    for e in m["shots"]:
        if e["id"] == sh.id:
            e["screen_quads"] = quads
            if str(sh.frames) in quads:
                e["screen_quad"] = quads[str(sh.frames)]
    manifest_save(m)
    print(f"QUADS {sh.id}: {len(quads)} frames")


def still_quad(sid, scene, file, cam, ob, res, notes="", approved=False):
    """One picture-corner quad for a still (1920x1080 px of the same frame; scale for larger renders)."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    set_cam(cam["loc"], cam["tgt"], cam["lens"], cam["focus"], cam["fstop"])
    RIG["cam"].data.shift_x = cam.get("shift_x", 0.0)
    bpy.context.view_layer.update()
    q = _project(_corner_world(ob))
    RIG["cam"].data.shift_x = 0.0
    m = manifest_load()
    e = next((x for x in m["shots"] if x["id"] == sid), None)
    if e is None:
        e = dict(id=sid, kind="still", scene=scene, file="world/" + file, start=None, frames=1, res=list(res),
                 status="approved" if approved else "pending", notes=notes)
        m["shots"].append(e)
    e["screen_quad"] = q
    manifest_save(m)
    print(f"QUAD still {sid}: {q}")


class Task:
    """Something to run in order with the renders (e.g. measuring the screen's corners)."""
    def __init__(self, fn):
        self.fn = fn


def screen_quad(sh, f, ob, uv_corners=((0, 1), (1, 1), (1, 0), (0, 0))):
    """The four corners of the visible picture (image UV corners: top-left, top-right, bottom-right, bottom-left)
    in 1920x1080 output pixels at frame f of shot sh. Saved into the shot's manifest entry as screen_quad."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    sh.segments[-1 if f > sh.seg_ranges()[-1][0] - 1 else 0][1]()
    sh.frame_fn(sh.time(f))
    bpy.context.view_layer.update()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    me = ob.data
    uvl = me.uv_layers.active.data
    mw = ob.matrix_world
    quad = []
    for cu, cv in uv_corners:
        best = min(range(len(me.loops)), key=lambda i: (uvl[i].uv[0] - cu) ** 2 + (uvl[i].uv[1] - cv) ** 2)
        co = mw @ me.vertices[me.loops[best].vertex_index].co
        v = world_to_camera_view(sc, RIG["cam"], co)
        quad.append([round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)])
    m = manifest_load()
    for e in m["shots"]:
        if e["id"] == sh.id:
            e["screen_quad"] = quad
            e.pop("screen_quad_frame", None)
            if f != sh.frames:
                e["quad_frame"] = f
    manifest_save(m)
    print(f"QUAD {sh.id} frame {f}: {quad}")
    return quad


# ------------------------------------------------------------------------------------------------ the manifest
def manifest_load():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as fh:
            return json.load(fh)
    return {"complete": False, "fps": FPS, "shots": []}


def manifest_save(m):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as fh:
        json.dump(m, fh, indent=1)
        fh.write("\n")


def manifest_update(sh, status):
    m = manifest_load()
    m["shots"] = [s for s in m["shots"] if not s["id"].endswith("_half")]   # halves are internal (see compose)
    if sh.id.endswith("_half"):
        manifest_save(m)
        return
    e = dict(id=sh.id, kind="seq", scene=sh.scene,
             replaces=sh.replaces[0] if len(sh.replaces) == 1 else sh.replaces,
             start=round(sh.start, 4), frames=sh.frames, status=status, notes=sh.notes)
    if sh.events:
        e["events"] = {k: sh.frame(t) for k, t in sh.events.items()}
    old = next((x for x in m["shots"] if x["id"] == sh.id), {})
    if old.get("frames") == sh.frames:                  # same render: keep its measured metadata
        for k in ("screen_quads", "screen_quad", "quad_frame"):
            if k in old:
                e[k] = old[k]
    m["shots"] = [s for s in m["shots"] if s["id"] != sh.id] + [e]
    m["shots"].sort(key=lambda s: (s["start"] is None, s["start"] or 0))
    manifest_save(m)


# ================================================================================================ the shop
def build_shop(args):
    import desk as DM
    cap = {}
    bm, bc = DM.build_materials, DM.build_corkboard

    def _bm():
        cap["M"] = bm()
        return cap["M"]

    def _bc(M):
        cap["hands"] = bc(M)
        return cap["hands"]

    DM.build_materials, DM.build_corkboard = _bm, _bc
    argv = sys.argv
    sys.argv = [argv[0], "--", "--no-render", "--samples", str(args.samples)]
    try:
        DM.main()
    finally:
        sys.argv = argv
    DM.build_materials, DM.build_corkboard = bm, bc
    make_rig(DM)
    add_flash()
    return DM, cap["M"], cap["hands"]


def add_flash():
    """A white flash at the end of the grade (the time-lapse swaps props inside it). Factor 0 = no change."""
    sc = bpy.context.scene
    ng = sc.compositing_node_group
    out = next(n for n in ng.nodes if n.bl_idname == "NodeGroupOutput")
    lk = out.inputs["Image"].links[0]
    src = lk.from_socket
    ng.links.remove(lk)
    import desk as DM
    mx = ng.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MIX"
    DM.sock(mx.inputs, "Factor_Float").default_value = 0.0
    DM.sock(mx.inputs, "B_Color").default_value = (1.0, 0.97, 0.92, 1.0)
    ng.links.new(src, DM.sock(mx.inputs, "A_Color"))
    ng.links.new(DM.sock(mx.outputs, "Result_Color"), out.inputs["Image"])
    RIG["flash"] = DM.sock(mx.inputs, "Factor_Float")


def COLL_OF(ob):
    return ob.users_collection[0].name if ob.users_collection else ""


def shop_shots(DM, M, hands):
    L = DM.LIGHTS
    sc = bpy.context.scene
    bulb = DM.principled(M["bulb"]).inputs["Emission Strength"]
    shots = {}
    base = {}
    rest = [(ob, Vector(ob.location), ob.rotation_euler.copy()) for ob in
            (bpy.data.objects[n] for n in ("backoffice_key", "key_tag", "lamp_switch", "drawer_BRAKE PADS",
                                           "rain_streaks", "rag"))]
    streaks = bpy.data.objects["rain_streaks"]
    streaks_rest = Vector(streaks.location)

    def rain(t):
        """Falling rain outside the window: the streaks re-scatter every frame, as rain does on film."""
        import random
        r = random.Random(int(round(t * FPS)) * 7919 + 17)
        streaks.location = streaks_rest + Vector((0.0, r.uniform(-0.12, 0.12), r.uniform(-0.3, 0.3)))

    L0 = {k: (ob.data.energy, tuple(ob.data.color)) for k, ob in L.items()}

    key_tree = [bpy.data.objects["backoffice_key"]] + list(bpy.data.objects["backoffice_key"].children_recursive)

    def preset(name, ev=0.0, key=True):
        """A lighting/dressing state. key=False: Theo's BACK OFFICE key is not on the keyboard yet (it lands in
        s2_key_lamp), for the night shots the film shows before that."""
        def setup():
            for ob, lc, rt in rest:                        # every animated prop back to its approved place
                ob.location, ob.rotation_euler = Vector(lc), rt.copy()
            for ob in key_tree:
                ob.hide_render = not key
            for k, (en, col) in L0.items():                # every light back to its built level (dusk moves some)
                if k in L:
                    L[k].data.energy, L[k].data.color = en, col
            bpy.data.objects["rain_streaks"].hide_render = False
            for nm in ("A_sweep", "A_car"):
                if nm in L:
                    L[nm].data.energy = 0.0
            DM.apply_preset(name, M, hands)
            sc.view_settings.exposure += ev
            RIG["flash"].default_value = 0.0
            base.clear()
            base["exp"] = sc.view_settings.exposure
            for k, ob in L.items():
                base[k] = ob.data.energy
            base["bulb"] = bulb.default_value
            base["sbright"] = DM.SCREEN["bright"].outputs[0].default_value
        return setup

    scr_ob = bpy.data.objects["screen"]
    bpy.context.view_layer.update()
    scr_c = sum((scr_ob.matrix_world @ Vector(c) for c in scr_ob.bound_box), Vector()) / 8

    def grid():
        if "grid" not in DM.SCREEN:
            return
        cam = RIG["cam"]
        d = (cam.location - scr_c).length
        footprint = d * 36.0 / (cam.data.lens * 1920 * sc.render.resolution_percentage / 100)
        cell_px = (0.408 / DM.PANEL_NATIVE[0]) / footprint
        DM.SCREEN["grid"].outputs[0].default_value = max(0.0, min(1.0, (cell_px - 1.5) / 2.5)) * 0.85

    def screen_light(bright_now, path_mean=None):
        """The monitor lights the desk with its own picture (apply_preset's rule), at the panel's current level."""
        mean = DM.SCREEN.get("mean") if path_mean is None else path_mean
        if mean is None:
            return
        import numpy as np
        lum = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
        for nm, b0 in (("L_screen", 5.0), ("L_screen_day", 2.0)):
            L[nm].data.energy = b0 * bright_now * max(lum, 0.01) / 0.16

    car = DM.light("A_car", "SPOT", (-3.4, 4.5, 0.95), 0.0, (1.0, 0.93, 0.82), "SET", spot=38, blend=0.7,
                   radius=0.12)

    # ---------------------------------------------------------------- 1 · s1 opening: up from black, one push
    sh = Shot("s1_open", 1, ["world/01_wide_night.png", "world/02_medium_night.png"], 0.0, 15.0)
    A, B = pose("CAM_wide"), pose("CAM_medium")
    C = dict(loc=scr_c + (B["loc"] - scr_c).normalized() * 0.8, tgt=scr_c.copy(), lens=50.0, fstop=2.8,
             focus=scr_c.copy())
    path_loc = Path([A["loc"], B["loc"].lerp(C["loc"], 0.15), C["loc"]])
    path_tgt = Path([A["tgt"], B["tgt"].lerp(C["tgt"], 0.3), C["tgt"]])
    path_foc = Path([A["focus"], B["focus"], C["focus"]])
    ease1 = bezier(0.5, 0.0, 0.3, 1.0)                # the room sits, then a slow approach, a long settle
    T_UP, T_LIT, T_GO, T_ARRIVE = 0.7, 3.2, 5.0, 14.8
    T_CAR = (3.9, 6.1)

    def f1(t):
        u = ease1(P(t, T_GO, T_ARRIVE - T_GO))
        set_cam(path_loc.at(u), path_tgt.at(u), lerp(A["lens"], C["lens"], smoother(u)),
                path_foc.at(u), lerp(1.6, 2.8, u))
        b = sine(P(t, T_UP, T_LIT - T_UP))
        sc.view_settings.exposure = base["exp"] + lerp(0.45, 0.0, smoother(u)) + 2.2 * math.log2(max(b, 1e-4))
        rain(t)
        k = P(t, T_CAR[0], T_CAR[1] - T_CAR[0])          # a car passes in the rain: its lights sweep the room
        car.data.energy = 650.0 * sin(pi * k) ** 2 if 0 < k < 1 else 0.0
        car.location = Vector((-3.4, lerp(4.5, -1.5, k), 0.95))
        car.rotation_euler = (Vector((2.4, lerp(0.6, 2.6, k), 1.55)) - car.location).to_track_quat("-Z", "Y").to_euler()
        grid()
    sh.segments = [(sh.start, preset("night", key=False))]      # before the key drop (s2)
    sh.frame_fn = f1
    sh.black_until = 0.7                                # before light_up the frame is black: write it, don't render
    sh.notes = (f"16 s, lived in: up from black ({T_UP}-{T_LIT} s, frames {sh.frame(T_UP)}-{sh.frame(T_LIT)}; baked "
                f"in, drop the still's brightness grade), the room sits in lamp and monitor light with rain on the "
                f"window and a car's lights sweeping the wall (frames {sh.frame(T_CAR[0])}-{sh.frame(T_CAR[1])}), "
                f"then one slow approach from the wide (frame {sh.frame(T_GO)}) that lands framed on the monitor by "
                f"frame {sh.frame(T_ARRIVE)} for the cut to the full-screen PC. Covers both s1 stills; full frame, "
                f"no cam crop. No key on the keyboard yet (Theo leaves it in s2). 1920x1080, 12 samples.")
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 2+3 · s2: the key lands, the lamp clicks off
    sh = Shot("s2_key_lamp", 2, ["world/03_keys_night.png"], 38.04, 38.04 + 8.0, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    sh2 = sh
    K = pose("CAM_keys")
    K2 = pushed(K, 640, 840, 1.12)
    T_PUSH = (38.04, 41.6)
    key = bpy.data.objects["backoffice_key"]
    tag = bpy.data.objects["key_tag"]
    sw = bpy.data.objects["lamp_switch"]
    key_rest = (Vector(key.location), key.rotation_euler.copy())
    tag_rest = (Vector(tag.location), tag.rotation_euler.copy())
    sw_rest = Vector(sw.location)
    T_LAND, T_LAMP = 38.04 + 1.2, 38.04 + 4.2
    sh.notes = (f"SHOTLIST 2.9: Theo's BACK OFFICE key drops in from above frame and lands on the keyboard at frame "
                f"{sh.frame(T_LAND)} (the key tap) with a small bounce, the tag settling after; a calm push toward the "
                f"key (frames 1-{sh.frame(T_PUSH[1])}), then held; the desk lamp clicks off at frame "
                f"{sh.frame(T_LAMP)} and the room drops to the monitor's glow; held in the dark to the end. Baked in: "
                f"no brightness grade on top. 1600x900 at 12 samples, upscaled.")
    sh.active = [(sh.start - 1, T_PUSH[1] + 0.05), (T_LAMP - 0.1, T_LAMP + 0.3)]
    LAMP_OFF_EV = -2.2          # with the lamp off the room drops to the monitor's glow (the animatic's .16)
    # how high above the keyboard the key must start to be out of frame (camera at its start pose)
    from bpy_extras.object_utils import world_to_camera_view
    set_cam(K["loc"], K["tgt"], K["lens"], K["focus"], K["fstop"])
    bpy.context.view_layer.update()
    kw = key.matrix_world.translation.copy()
    h_out = 0.08
    while h_out < 0.6:
        v = world_to_camera_view(sc, RIG["cam"], kw + Vector((0, 0.03, h_out - 0.035)))
        if v.y > 1.02 or v.x < -0.02 or v.x > 1.02:
            break
        h_out += 0.01
    h_out += 0.05                                       # margin for the key's length and its tumble
    T_FALL = math.sqrt(2 * h_out / 9.81)
    print(f"key: out of frame at {h_out:.2f} m above, fall {T_FALL:.3f}s")
    kb_inv = key.parent.matrix_world.to_3x3().inverted() if key.parent else None
    up_local = (kb_inv @ Vector((0, 0, 1))).normalized() if kb_inv else Vector((0, 0, 1))
    fwd_local = (kb_inv @ Vector((0, 0.03, 0))) if kb_inv else Vector((0, 0.03, 0))

    def key_pose(t):
        loc, rot = Vector(key_rest[0]), key_rest[1].copy()
        tl, tr = Vector(tag_rest[0]), tag_rest[1].copy()
        dt = t - T_LAND
        if dt < 0:                                     # falling (from out of frame), tumbling flat as it comes
            fall = max(0.0, T_FALL + dt)
            h = h_out - 0.5 * 9.81 * fall * fall if dt > -T_FALL else h_out + 0.2
            k = clamp01(-dt / T_FALL)
            loc += up_local * max(h, 0.0) + fwd_local * k
            rot.x += radians(16) * k
            rot.y += radians(-9) * k
            rot.z += radians(22) * k
            tr.z += radians(-14) * k
        else:                                          # a small bounce (stylised, two hops) and a rocking settle
            hop = 0.0
            if dt < 0.17:
                hop = 0.0055 * sin(pi * dt / 0.17)
            elif dt < 0.27:
                hop = 0.0012 * sin(pi * (dt - 0.17) / 0.10)
            loc += up_local * hop
            rock = exp(-dt / 0.12) * sin(2 * pi * dt / 0.16)
            rot.x += radians(3.5) * rock
            rot.y += radians(-2.0) * exp(-dt / 0.1) * sin(2 * pi * dt / 0.2)
            tr.z += radians(-14) * exp(-dt / 0.09) + radians(5) * exp(-dt / 0.2) * sin(2 * pi * dt / 0.34)
            tl.z += 0.0025 * exp(-dt / 0.06) * (1 if dt < 0.06 else 0.4)
        key.location, key.rotation_euler = loc, rot
        tag.location, tag.rotation_euler = tl, tr

    def lamp_level(t, t_lamp=None):
        """1 = lamp on, 0 = off: the switch clicks at t_lamp; 80% gone in one frame, then a tungsten afterglow
        fading over 3-4 frames."""
        dt = t - (T_LAMP if t_lamp is None else t_lamp)
        if dt <= 0:
            return 1.0
        if dt < 1 / FPS:
            return lerp(1.0, 0.2, dt * FPS)
        return 0.2 * exp(-(dt - 1 / FPS) / 0.05)

    def lamp_off_state(lv):
        L["L_lamp"].data.energy = 40.0 * lv
        bulb.default_value = 20.0 * lv
        L["L_floor_spill"].data.energy = lerp(2.5, 9.0, lv)
        L["L_bounce"].data.energy = lerp(2.0, 7.0, lv)
        L["L_box_kick"].data.energy = lerp(2.0, 7.0, lv)
        sc.view_settings.exposure = base["exp"] + LAMP_OFF_EV * (1 - lv)

    def f2(t):
        cam_between(K, K2, CALM(P(t, T_PUSH[0], T_PUSH[1] - T_PUSH[0])))
        key_pose(t)
        lv = lamp_level(t)
        L["L_lamp"].data.energy = 40.0 * lv
        bulb.default_value = 20.0 * lv
        L["L_floor_spill"].data.energy = lerp(2.5, 9.0, lv)
        L["L_bounce"].data.energy = lerp(2.0, 7.0, lv)
        L["L_box_kick"].data.energy = lerp(2.0, 7.0, lv)
        sc.view_settings.exposure = base["exp"] + LAMP_OFF_EV * (1 - lv)
        press = clamp01(1 - abs(t - (T_LAMP - 0.02)) / 0.07)
        sw.location = sw_rest - Vector((0, 0, 0.0018 * press))
        grid()
    sh.segments = [(sh.start, preset("night"))]
    sh.frame_fn = f2
    sh.no_probe = True
    shots[sh.id] = sh

    # the rendered s2 (79 frames, the first cut's timing) with the lamp fix: re-render its tail (frames 54-79)
    v1 = Shot("s2_key_lamp", 2, ["world/03_keys_night.png"], 38.04, 40.34)
    K2v1 = pushed(K, 640, 840, 1.2)
    T_LAMP1 = 39.79
    v1.notes = ("Theo's BACK OFFICE key drops in from above frame (frame 21) and lands on the keyboard at frame 26 "
                "with a small bounce; a slow push toward the key; the lamp clicks off at frame 56: 80% dark in that "
                "frame, a tungsten afterglow over 3-4 frames, monitor-lit from frame 60 (exposure -2.2 EV). Baked in: "
                "no brightness grade on top. 1920x1080, 16 samples.")
    v1.events = {"key": 38.59 - 0.235, "key_land": 38.59, "lamp_off": 37.54 + 55 / FPS}

    def f2v1(t):
        cam_between(K, K2v1, DRIFT(P(t, 38.04, 40.84 - 38.04)))
        key_pose(max(t, T_LAND + 0.8))                   # (tail only: the key has long settled)
        lamp_off_state(lamp_level(t, T_LAMP1))
        press = clamp01(1 - abs(t - (T_LAMP1 - 0.02)) / 0.07)
        sw.location = sw_rest - Vector((0, 0, 0.0018 * press))
        grid()
    v1.segments = [(v1.start, preset("night"))]
    v1.frame_fn = f2v1
    v1.no_probe = True
    v1.samples = 16
    shots["s2_key_lamp_v1"] = v1

    # ---------------------------------------------------------------- 4 · s3 time-lapse: Thursday night -> Monday
    sh = Shot("s3_timelapse", 3, ["world/02_medium_night.png", "world/04_medium_monday.png"], 40.34, 48.34,
              res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    Mm = pose("CAM_medium")
    Mm2 = Mm                                            # held (SHOTLIST 3.1): the film corner-pins into the screen
    T_DAWN, T_SWAP, T_SETTLE = 41.6, 43.6, 44.6
    sh.notes = (f"Held on the desk. Thursday night with the lamp off (as s2 ends) to frame {sh.frame(T_DAWN)}; a blue "
                f"dawn rakes in and blooms to white (props swap inside the bloom at frame {sh.frame(T_SWAP)}); Monday "
                f"08:52 settles by frame {sh.frame(T_SETTLE)} and holds to the end (the Monday desk, SHOTLIST 3.2). "
                f"Brightness and the light are baked in: no brightness grade or sweep overlay on top. 1600x900 at 12 "
                f"samples, upscaled. screen_quad = the monitor's picture on the last frame.")
    sh.active = [(T_DAWN - 0.1, T_SETTLE + 0.1)]
    sun = L["L_sun"]
    sweep = DM.light("A_sweep", "SUN", (0, 0, 3), 0.0, (1.0, 0.93, 0.82), "SET")
    sweep.data.angle = radians(2.5)
    d_mon = Vector((0.65, 0.55, -0.52))

    def sundir(u):
        """From a low raking dawn (barely over the sill) round to Monday's angle."""
        d0 = Vector((0.9, 0.05, -0.12))
        return d0.lerp(d_mon, u).normalized()

    def setup_night():
        preset("night")()
        base["lamp_off"] = True

    def f3(t):
        cam_between(Mm, Mm2, 0.0)
        RIG["flash"].default_value = sine(1 - abs(t - T_SWAP) / 0.45)   # a soft bloom to white and back
        if t < T_SWAP:
            rain(t)
            L["L_lamp"].data.energy = 0.0
            bulb.default_value = 0.0
            L["L_floor_spill"].data.energy = 2.5
            L["L_bounce"].data.energy = 2.0
            L["L_box_kick"].data.energy = 2.0
            dawn = sine(P(t, T_DAWN, T_SWAP - T_DAWN))
            sweep.data.energy = 30.0 * dawn
            sweep.rotation_euler = sundir(0.35 * dawn).to_track_quat("-Z", "Y").to_euler()
            sc.view_settings.exposure = base["exp"] + LAMP_OFF_EV + (5.0 - LAMP_OFF_EV) * dawn ** 2.2
        else:
            k = sine(P(t, T_SWAP, T_SETTLE - T_SWAP))
            sweep.data.energy = 0.0
            sun.rotation_euler = sundir(lerp(0.35, 1.0, k)).to_track_quat("-Z", "Y").to_euler()
            sc.view_settings.exposure = base["exp"] + 4.0 * (1 - k) ** 2.0
        grid()
    sh.segments = [(sh.start, setup_night), (T_SWAP, preset("monday"))]
    sh.frame_fn = f3
    sh3 = sh
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 5 · s3 shelf: drawer 1 slides open
    sh = Shot("s3_shelf", 3, ["world/x_shelf_monday.png"], 56.21, 56.21 + 8.0, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    S0 = pose("CAM_shelf")
    S1 = S0                                              # held (SHOTLIST 3.5)
    T_DR = 56.21 + 1.0
    sh.notes = (f"SHOTLIST 3.5: held on the approved frame; drawer 1 (BRAKE PADS) slides open from shut at frames "
                f"{sh.frame(T_DR)}-{sh.frame(T_DR + 0.85)}, one pair of pads inside; then holds on the approved "
                f"still's state. 1600x900 at 12 samples, upscaled.")
    sh.active = [(T_DR - 0.1, T_DR + 0.95)]
    dr = bpy.data.objects["drawer_BRAKE PADS"]
    dr_open = Vector(dr.location)
    dr_shut = Vector((dr_open.x, -0.008, dr_open.z))

    def f5(t):
        cam_between(S0, S1, 0.0)
        k = P(t, T_DR, 0.62)
        e = 1 - (1 - k) ** 3                            # pulled: quick start, soft stop
        over = 0.004 * sin(pi * P(t, T_DR + 0.5, 0.22)) if t > T_DR + 0.5 else 0.0
        dr.location = dr_shut.lerp(dr_open, e) + Vector((0, -over, 0))
    sh.segments = [(sh.start, preset("monday"))]
    sh.frame_fn = f5
    sh.no_probe = True
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 6 · s5 afternoon: the light slides across
    sh = Shot("s5_afternoon", 5, ["world/04_medium_monday.png"], 77.72, 77.72 + 8.0, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    Mo = pose("CAM_medium_monday")
    Mo2 = Mo                                             # held (SHOTLIST 5.1)
    d_aft0 = Vector((0.8, 1.0, -0.78))                   # a low winter sun through the window, its shaft sliding
    d_aft1 = Vector((1.7, 0.9, -0.72))                   # from the desk's left across toward the mug
    T_SUN = (77.72 + 0.8, 77.72 + 6.8)
    sh.notes = (f"SHOTLIST 5.1: held on the Monday desk, about 14:30: a low winter sun breaks through and its warm "
                f"shaft slides across the desk (frames {sh.frame(T_SUN[0])}-{sh.frame(T_SUN[1])}). The light is the "
                f"grade: no colour filter on top. 1600x900 at 12 samples, upscaled.")
    sh.active = [(T_SUN[0] - 0.05, T_SUN[1] + 0.05)]

    def f6(t):
        cam_between(Mo, Mo2, 0.0)
        k = CALM(P(t, T_SUN[0], T_SUN[1] - T_SUN[0]))
        sun.rotation_euler = d_aft0.lerp(d_aft1, k).normalized().to_track_quat("-Z", "Y").to_euler()
        sun.data.energy, sun.data.color = 26.0, (1.0, 0.8, 0.58)
        grid()
    sh.segments = [(sh.start, preset("monday"))]
    sh.frame_fn = f6
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 7 · s9 shop night: the PC goes to sleep
    sh = Shot("s9_shop_night", 9, ["world/x_close_night.png"], 199.7, 199.7 + 2 * 5.11, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    C0 = pose("CAM_medium")
    C1 = C0                                              # held (SHOTLIST 9.1)
    tue = DM.SCREEN_PATHS["tuesday"]
    T_DIM, T_OFF = 199.7 + 3.6, 199.7 + 5.2
    sh.notes = (f"18:40, Martin gone, lamp off. The monitor (Tuesday's jobs page) dims at frame {sh.frame(T_DIM)}, "
                f"goes dark at frame {sh.frame(T_OFF)}, then Barnaby's bell glows up in the corner (full by frame "
                f"{sh.frame(T_OFF + 2.2)}); the power LEDs go blue -> amber as it sleeps. Ends on the approved "
                f"still's state. Held. Rendered 1600x900 at 12 samples, upscaled.")
    sh.active = [(T_DIM - 0.1, T_OFF + 0.6 + 1.6 + 0.1)]

    def setup_awake():
        preset("close", 0.0)()
        DM.set_screen(tue, DM.SCREEN_FIT[0])
        base["mean_awake"] = DM.SCREEN.get("mean")
        for nm in ("tower_power_ring", "mon_led"):
            ob = bpy.data.objects.get(nm)
            if ob:
                ob.data.materials[0] = M["led_blue"]

    def setup_asleep():
        preset("close", 0.0)()

    def f7(t):
        cam_between(C0, C1, CALM(P(t, sh7.start, sh7.frames / FPS)))
        if t < T_OFF + 0.15:
            lvl = lerp(0.62, 0.24, sine(P(t, T_DIM, 0.35)))     # a dark room at 18:40: the page glows, not blazes
            lvl *= 1 - sine(P(t, T_OFF, 0.15))
            DM.SCREEN["bright"].outputs[0].default_value = lvl
            screen_light(lvl, base.get("mean_awake"))
        else:
            g = sine(P(t, T_OFF + 0.6, 1.6))
            DM.SCREEN["bright"].outputs[0].default_value = base["sbright"] * g
            screen_light(base["sbright"] * g)
        grid()
    sh.segments = [(sh.start, setup_awake), (T_OFF + 0.15, setup_asleep)]
    sh7 = sh
    sh.frame_fn = f7
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 9a · s9 two desks: the shop half
    sh = Shot("s9_two_desks_shop_half", 9, ["world/close_two_desks.png"], 208.34, 208.34 + 2 * 9.6, res=(800, 900))
    H0 = pose("CAM_close_half")
    H1 = pushed(H0, 480, 560, 1.06, res=(960, 1080))
    sh9 = sh

    def f9(t):
        cam_between(H0, H1, CALM(P(t, sh9.start, sh9.frames / FPS)))
        grid()
    sh.segments = [(sh.start, preset("close"))]
    sh.frame_fn = f9
    shots[sh.id] = sh

    # ================================================================ dusk: Mon 16:08 (a new lighting state)
    NIGHT_KEEP = ("L_lamp", "L_floor_spill", "L_bounce", "L_screen", "L_street")
    night_lights = [k for k, ob in L.items() if COLL_OF(ob) == "NIGHT"]

    def dusk(lamp):
        """Monday's props and screen; just after a late-November sunset: the window deep blue, rain stopped, the lit
        window opposite, the workshop strip on; the desk lamp at `lamp` (0 off .. 1 on, the 2700 K pool as at
        night); the wall clock at 16:08."""
        preset("monday")()
        DM.COLL["NIGHT"].hide_render = False
        for k in night_lights:
            if k not in NIGHT_KEEP:
                L[k].data.energy = 0.0
        L["L_sun"].data.energy = 0.0
        L["L_window_day"].data.energy, L["L_window_day"].data.color = 26.0, (0.42, 0.53, 0.95)
        L["L_room_fill"].data.energy, L["L_room_fill"].data.color = 5.0, (0.55, 0.65, 1.0)
        L["L_drawer_bounce"].data.energy = 1.2
        L["L_street"].data.energy = 6.0
        L["L_worklamp"].data.energy, L["L_pegboard"].data.energy = 30.0, 12.0
        sky = DM.principled(M["outside_sky"])
        sky.inputs["Emission Color"].default_value = DM.rgba("#20366a")
        sky.inputs["Emission Strength"].default_value = 1.5
        DM.principled(M["outside_win"]).inputs["Emission Strength"].default_value = 3.0
        bg = sc.world.node_tree.nodes["Background"]
        bg.inputs[0].default_value = DM.rgba("#28344f")
        bg.inputs[1].default_value = 0.32
        bpy.data.objects["rain_streaks"].hide_render = True
        DM.SCREEN["bright"].outputs[0].default_value = 0.95
        base["sbright"] = 0.95
        screen_light(0.95)
        L["L_screen_day"].data.energy = 0.0
        for bs, st in DM.REFLECT_EMIT:
            bs.inputs["Emission Strength"].default_value = st * 0.12
        sc.view_settings.exposure = 0.3
        base["exp"] = 0.3
        hands["hour"].rotation_euler = (0, 0, -2 * pi * (4 + 8 / 60) / 12)
        hands["minute"].rotation_euler = (0, 0, -2 * pi * 8 / 60)
        lamp_set(lamp)

    def lamp_set(lv):
        L["L_lamp"].data.energy = 40.0 * lv
        bulb.default_value = 20.0 * lv
        L["L_floor_spill"].data.energy = lerp(1.0, 9.0, lv)
        L["L_bounce"].data.energy = lerp(0.8, 7.0, lv)

    D0 = pose("CAM_medium_monday")
    sh = Shot("s6_lamp_on", 6, ["world/04_medium_monday.png"], 104.78, 104.78 + 6.0)
    T_CLICK = 104.78 + 0.5
    sh.notes = (f"NEW (SHOTLIST 6.1): dusk, Mon 16:08. Held on CAM_medium_monday's frame: a dim blue room, then the "
                f"desk lamp clicks on at frame {sh.frame(T_CLICK)} (0.5 s after the on-screen start, frame 13) and "
                f"the room warms; matches 06_medium_dusk from frame {sh.frame(T_CLICK + 0.3)}. 1920x1080, 12 "
                f"samples. 'replaces' is the nearest old still; start is scene 6's old start.")
    sh.active = [(T_CLICK - 0.1, T_CLICK + 0.35)]
    sw6 = bpy.data.objects["lamp_switch"]
    sw6_rest = Vector(sw6.location)

    def f6on(t):
        cam_between(D0, D0, 0.0)
        dt = t - T_CLICK
        lamp_set(0.0 if dt < 0 else 1.0 - exp(-dt / 0.045))
        press = clamp01(1 - abs(t - (T_CLICK - 0.02)) / 0.07)
        sw6.location = sw6_rest - Vector((0, 0, 0.0018 * press))
        grid()
    sh.segments = [(sh.start, lambda: dusk(0.0))]
    sh.frame_fn = f6on
    shots[sh.id] = sh

    shots["06_medium_dusk"] = Still("06_medium_dusk", 6, "06_medium_dusk.png", lambda: dusk(1.0), D0,
                                    notes="NEW (SHOTLIST 6.1/6.4): the dusk desk, lamp on, Mon 16:08; the same frame "
                                          "as s6_lamp_on's end and CAM_medium_monday. 2560x1440, 32 samples.")
    bpy.context.view_layer.update()
    note = bpy.data.objects["note_paper"]
    nc = sum((note.matrix_world @ Vector(c) for c in note.bound_box), Vector()) / 8
    nn = (note.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    if nn.y > 0:
        nn = -nn
    sticky_cam = dict(loc=nc + nn * 0.2 + Vector((-0.07, 0.0, 0.035)), tgt=nc, lens=75.0, fstop=2.0, focus=nc)
    # the WHOLE note sharp, only the room behind it soft: focus at the middle of the note's depth as framed (its curl,
    # seen at an angle; its top runs out of frame), stopped down to f/28. Compared by eye at 2560 wide: at f/28, f/36
    # and f/48 the ink and all four paper edges are equally crisp; f/28 keeps the most falloff on the desk and wall.
    from bpy_extras.object_utils import world_to_camera_view
    set_cam(sticky_cam["loc"], sticky_cam["tgt"], sticky_cam["lens"], sticky_cam["focus"], sticky_cam["fstop"])
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    sc.render.resolution_x, sc.render.resolution_y = 2560, 1440
    bpy.context.view_layer.update()
    fwd = (sticky_cam["tgt"] - sticky_cam["loc"]).normalized()
    ev_note = note.evaluated_get(bpy.context.evaluated_depsgraph_get())
    seen = [ev_note.matrix_world @ v.co for v in ev_note.data.vertices]
    seen = [w for w in seen if all(-0.01 <= c <= 1.01 for c in world_to_camera_view(sc, RIG["cam"], w)[:2])]
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    depths = [(w - sticky_cam["loc"]).dot(fwd) for w in seen]
    s_f = 2 * min(depths) * max(depths) / (min(depths) + max(depths))    # near and far blur equally
    sticky_cam["focus"] = sticky_cam["loc"] + fwd * s_f
    sticky_cam["fstop"] = 28.0
    print(f"x_sticky_dusk: note depth {min(depths):.3f}-{max(depths):.3f} m as framed, focus {s_f:.3f} m, "
          f"f/{sticky_cam['fstop']:.0f}")
    shots["x_sticky_dusk"] = Still("x_sticky_dusk", 6, "x_sticky_dusk.png", lambda: dusk(1.0), sticky_cam,
                                   notes=f"NEW (SHOTLIST 6.2): Theo's sticky note on the bezel at dusk, the lamp on; "
                                         f"the whole note sharp (f/{sticky_cam['fstop']:.0f}), only the room behind falls "
                                         f"off. 2560x1440, 32 samples.")
    gl = bpy.data.objects["glasses"]
    gc = gl.matrix_world.translation.copy() + Vector((0, 0, 0.006))
    glasses_cam = dict(loc=gc + Vector((0.2, -0.2, 0.11)), tgt=gc + Vector((0.0, 0.01, 0.0)), lens=65.0, fstop=2.0,
                       focus=gc)
    shots["x_glasses_dusk"] = Still("x_glasses_dusk", 6, "x_glasses_dusk.png", lambda: dusk(1.0), glasses_cam,
                                    notes="NEW (SHOTLIST 6.6): Martin's reading glasses on job card 4478 at dusk, in "
                                          "the lamp's pool, shallow focus. 2560x1440, 32 samples.")
    shots["x_close_half_shop_2x"] = Still("x_close_half_shop_2x", 9, "x_close_half_shop_2x.png", preset("close"),
                                          pose("CAM_close_half"), res=(1920, 2160),
                                          notes="SHOTLIST 9.3: the approved shop half at 2x (1920x2160) for the film's "
                                                "slow matched push; asleep, as approved. 32 samples.")
    scr = bpy.data.objects["screen"]
    RIG["grid"] = grid
    shots["quad_s1_open"] = Task(lambda: screen_quad(shots["s1_open"], shots["s1_open"].frames, scr))
    shots["quad_s3_timelapse"] = Task(lambda: screen_quad(sh3, sh3.frames, scr))
    shots["quads_s1_open"] = Task(lambda: screen_quads(shots["s1_open"], scr))
    shots["quads_s3_timelapse"] = Task(lambda: screen_quads(sh3, scr))

    def shop_still_quads():
        ap = "approved still (not re-rendered); screen_quad in 1920x1080 px of its frame"
        still_quad("02_medium_night", 2, "02_medium_night.png", pose("CAM_medium"), scr, (1920, 1080),
                   "approved still, re-rendered by desk.py (same camera and settings) without Theo's BACK OFFICE key: "
                   "the film shows it before he leaves the key (s2_key_lamp); screen_quad in 1920x1080 px of its frame",
                   True)
        still_quad("04_medium_monday", 3, "04_medium_monday.png", pose("CAM_medium_monday"), scr, (1920, 1080), ap,
                   True)
        still_quad("05_medium_tuesday", 7, "05_medium_tuesday.png", pose("CAM_medium_tuesday"), scr, (1920, 1080),
                   ap, True)
        still_quad("06_medium_dusk", 6, "06_medium_dusk.png", pose("CAM_medium_monday"), scr, (2560, 1440))
    shots["quad_stills_shop"] = Task(shop_still_quads)

    # ================================================================ v2.3: match cuts, a plate, a rack focus
    bpy.context.view_layer.update()
    mug = bpy.data.objects["mug"]
    mug_c = Vector(mug.location) + Vector((0, 0, 0.05))
    med = pose("CAM_medium")
    dh = med["loc"] - mug_c
    dh.z = 0.0
    dh.normalize()
    # ONE camera for the whole match cut (x_mug_night, x_mug_night_off, x_mug_dawn): the mug sits in exactly the same
    # place in all three. Martin's rag is moved out of this frame on Monday (rag_clear) instead of raising the camera.
    mug_cam = dict(loc=mug_c + dh * 0.52 + Vector((0, 0, 0.07)), tgt=mug_c + Vector((-0.03, 0.0, -0.01)),
                   lens=70.0, fstop=2.0, focus=mug_c + dh * 0.04)
    rag = bpy.data.objects["rag"]
    rag_home = Vector(rag.location)

    def rag_clear(cam):
        """The shortest slide along the desk top that takes the whole rag out of cam's 16:9 frame (with a margin)."""
        from bpy_extras.object_utils import world_to_camera_view
        set_cam(cam["loc"], cam["tgt"], cam["lens"], cam["focus"], cam["fstop"])
        rx, ry = sc.render.resolution_x, sc.render.resolution_y
        sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
        desk = bpy.data.objects["desk_top"]
        dx = [(desk.matrix_world @ Vector(c)) for c in desk.bound_box]
        x0, x1 = min(v.x for v in dx) + 0.03, max(v.x for v in dx) - 0.03
        y0, y1 = min(v.y for v in dx) + 0.01, max(v.y for v in dx) - 0.03
        best = None
        for dist in [0.01 * i for i in range(2, 61)]:
            for a in range(0, 360, 10):
                off = Vector((cos(radians(a)), sin(radians(a)), 0.0)) * dist
                rag.location = rag_home + off
                bpy.context.view_layer.update()
                ev = rag.evaluated_get(bpy.context.evaluated_depsgraph_get())
                cs = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
                if not all(x0 <= c.x <= x1 and y0 <= c.y <= y1 for c in cs):
                    continue
                vs = [world_to_camera_view(sc, RIG["cam"], c) for c in cs]
                m = 0.04
                if (all(v.x < -m for v in vs) or all(v.x > 1 + m for v in vs) or all(v.y < -m for v in vs) or
                        all(v.y > 1 + m for v in vs) or all(v.z < 0 for v in vs)):
                    best = off
                    break
            if best is not None:
                break
        rag.location = rag_home
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        print(f"rag_clear: {'moved ' + str(tuple(round(x, 3) for x in best)) if best is not None else 'NOT FOUND'}")
        return best if best is not None else Vector((0.0, 0.0, 0.0))
    rag_off = rag_clear(mug_cam)
    shots["x_mug_night"] = Still("x_mug_night", 2, "x_mug_night.png", preset("night"), mug_cam,
                                 notes="v2.3 match cut (Thu night -> Mon): Theo's WORLD'S OKAYEST NEPHEW mug in the "
                                       "lamp pool, cold coffee, shallow focus, the monitor's glow soft behind. "
                                       "2560x1440, 32 samples. Cut to x_mug_dawn (same framing).")

    sh = Shot("x_mug_night_off", 2, ["world/x_mug_night.png"], 39.29, 39.29 + 3.0)
    T_MOFF = 39.29 + 1.5
    sh.notes = (f"v2.3 match cut, first half: x_mug_night's frame, Theo's mug in the lamp pool; the lamp clicks off at "
                f"frame {sh.frame(T_MOFF)} (80% down in that frame, a 3-4 frame afterglow, then only the monitor's "
                f"glow, -2.2 EV) and holds in the dark. Cut to x_mug_dawn. Static camera. 1920x1080, 12 samples.")
    sh.events = {"lamp_off": T_MOFF + 1 / FPS}            # the first dark frame
    sh.active = [(T_MOFF - 0.1, T_MOFF + 0.3)]

    def f_moff(t):
        cam_between(mug_cam, mug_cam, 0.0)
        lamp_off_state(lamp_level(t, T_MOFF))
    sh.segments = [(sh.start, preset("night"))]
    sh.frame_fn = f_moff
    shots[sh.id] = sh

    sh = Shot("x_mug_dawn", 3, ["world/x_mug_night.png"], 40.34, 40.34 + 3.5)
    T_RISE = (40.34 + 0.4, 40.34 + 3.1)
    sh.notes = (f"v2.3 match cut: x_mug_night's framing on Monday morning: the lamp off, Martin's tea in the same "
                f"mug, daylight rising from pre-dawn blue (frames 1-{sh.frame(T_RISE[0])}) to Monday's morning light "
                f"(full by frame {sh.frame(T_RISE[1])}). Static camera (handheld is post). 1920x1080, 12 samples.")
    sh.active = [(T_RISE[0] - 0.05, T_RISE[1] + 0.05)]
    sky_m = DM.principled(M["outside_sky"])
    bgn = sc.world.node_tree.nodes["Background"]

    def setup_dawn():
        preset("monday")()
        rag.location = rag_home + rag_off                  # out of the match cut's frame (preset() puts it back)
        base["day"] = {k: L[k].data.energy for k in ("L_sun", "L_window_day", "L_room_fill", "L_strip",
                                                       "L_drawer_bounce", "L_screen_day")}
        base["sky"] = sky_m.inputs["Emission Strength"].default_value
        base["bg"] = bgn.inputs[1].default_value

    def f_dawn(t):
        cam_between(mug_cam, mug_cam, 0.0)
        k = sine(P(t, T_RISE[0], T_RISE[1] - T_RISE[0]))
        for nm, lo in (("L_sun", 0.0), ("L_window_day", 0.12), ("L_room_fill", 0.08), ("L_strip", 0.0),
                       ("L_drawer_bounce", 0.1), ("L_screen_day", 1.0)):
            L[nm].data.energy = base["day"][nm] * lerp(lo, 1.0, k)
        L["L_window_day"].data.color = tuple(lerp(a, b, k) for a, b in zip((0.4, 0.5, 0.95), (0.72, 0.84, 1.0)))
        sky_m.inputs["Emission Strength"].default_value = base["sky"] * lerp(0.15, 1.0, k)
        bgn.inputs[1].default_value = base["bg"] * lerp(0.15, 1.0, k)
        DM.principled(M["tube"]).inputs["Emission Strength"].default_value = 9.0 * k
    sh.segments = [(sh.start, setup_dawn)]
    sh.frame_fn = f_dawn
    shots[sh.id] = sh

    ch_cam = dict(loc=Vector((2.38, 0.72, 1.16)), tgt=Vector((1.3, 2.35, 0.86)), lens=32.0, fstop=2.8,
                  focus=Vector((1.75, 1.55, 0.92)))
    shots["x_chair_dusk"] = Still("x_chair_dusk", 6, "x_chair_dusk.png", lambda: dusk(1.0), ch_cam,
                                  notes="v2.3 match cut (Mon dusk -> Tue): the empty desk chair from behind and to one "
                                        "side, the monitor and lamp beyond, dusk with the lamp on. 2560x1440, 32 "
                                        "samples. Cut to x_chair_tuesday (same framing).")
    shots["x_chair_tuesday"] = Still("x_chair_tuesday", 7, "x_chair_tuesday.png", preset("tuesday"), ch_cam,
                                     notes="v2.3 match cut: x_chair_dusk's framing on Tuesday morning, crisp sun, "
                                           "Priya's helmet hanging on the chair (the chair is pushed in, as on "
                                           "Tuesday). 2560x1440, 32 samples.")
    wide = pose("CAM_wide")
    wide4 = dict(wide, lens=33.0, shift_x=-0.06)
    shots["01_wide_night_4k"] = Still("01_wide_night_4k", 1, "01_wide_night_4k.png", preset("night", 0.45, key=False),
                                      wide4, res=(3840, 2160),
                                      notes="v2.3 plate for 2D pans: the night wide at 3840x2160, a little wider (38 -> "
                                            "33 mm) with the extra on the window side; s1, before the key drop: no key "
                                            "on the keyboard. 32 samples.")
    key_w = bpy.data.objects["backoffice_key"].matrix_world.translation.copy()
    rk_tgt = scr_c.copy()
    rk_loc = key_w + Vector((0.05, -0.2, 0.075))
    dk, ds = (key_w - rk_loc).normalized(), (rk_tgt - rk_loc).normalized()
    half = math.acos(max(-1.0, min(1.0, dk.dot(ds)))) / 2           # key low in frame, the monitor high
    rk = dict(loc=rk_loc, tgt=rk_loc + (dk + ds).normalized() * 0.3,
              lens=max(24.0, 10.125 / math.tan(half / 0.72)), fstop=1.8, focus=key_w)
    sh = Shot("x_key_rack", 2, ["world/03_keys_night.png"], 38.04, 38.04 + 2.5)
    T_RACK = (38.04 + 0.7, 38.04 + 1.9)
    sh.notes = (f"v2.3 rack focus, night, lamp on: low over the keyboard, Theo's key sharp in the foreground, then "
                f"the focus racks to the monitor (frames {sh.frame(T_RACK[0])}-{sh.frame(T_RACK[1])}). Static camera. "
                f"1920x1080, 12 samples.")
    sh.active = [(T_RACK[0] - 0.05, T_RACK[1] + 0.05)]

    def f_rack(t):
        k = sine(P(t, T_RACK[0], T_RACK[1] - T_RACK[0]))
        set_cam(rk["loc"], rk["tgt"], rk["lens"], key_w.lerp(rk_tgt, k), rk["fstop"])
    sh.segments = [(sh.start, preset("night"))]
    sh.frame_fn = f_rack
    shots[sh.id] = sh

    EV = {"s1_open": {"light_up": T_LIT, "medium": T_GO, "screen": T_ARRIVE},
          "s2_key_lamp": {"key": T_LAND - T_FALL, "key_land": T_LAND, "lamp_off": T_LAMP},
          "s3_timelapse": {"timelapse": T_DAWN, "monday": T_SETTLE, "clock": T_SETTLE + 2.2},
          "s3_shelf": {"shelf": T_DR}, "s5_afternoon": {"afternoon": 77.72},
          "s6_lamp_on": {"late": 104.78, "lamp_on": T_CLICK},
          "s9_shop_night": {"shop_night": 199.7, "shop_sleep": T_OFF},
          "x_mug_dawn": {"timelapse": T_RISE[0], "monday": T_RISE[1]}}
    for k, v in EV.items():
        shots[k].events = v

    # ================================================================ Tier B
    def drift_shot(sid, scene, still, cam, t0, t1, px, py, s, preset_name, ev, notes, no_probe=True, extra=None):
        sh = Shot(sid, scene, [still], t0, t1, notes=notes)
        a = pose(cam)
        b = pushed(a, px, py, s)

        def fn(t):
            cam_between(a, b, DRIFT(P(t, t0, t1 + 0.5 - t0)))
            if extra:
                extra(t)
            grid()
        sh.segments = [(sh.start, preset(preset_name, ev))]
        sh.frame_fn = fn
        sh.no_probe = no_probe
        shots[sid] = sh
        return sh

    drift_shot("s2_board", 2, "world/x_board_night.png", "CAM_board", 12.8, 14.5, 430, 700, 1.3, "night", 0.2,
               "A slow pan down the corkboard onto the calendar (Friday circled). Starts on the approved still.")

    # the bell: Barnaby arrives (sfx 'bell' at 18.0): the plunger dips on its own, the dome quivers
    bell_names = ("bell_plunger", "bell_knob", "bell_dome", "bell_bead")
    bell_obs = {n: bpy.data.objects[n] for n in bell_names}
    bell_rest = {n: (Vector(o.location), o.rotation_euler.copy()) for n, o in bell_obs.items()}
    rest.extend((o, Vector(o.location), o.rotation_euler.copy()) for o in bell_obs.values())
    T_BELL = 18.0

    def bell(t):
        dt = t - T_BELL
        dip = 0.0
        if -0.06 < dt < 0:
            dip = sine(P(dt, -0.06, 0.06))
        elif dt >= 0:
            dip = exp(-dt / 0.025) - 0.12 * exp(-dt / 0.06) * sin(2 * pi * dt / 0.09)
        for n in ("bell_plunger", "bell_knob"):
            bell_obs[n].location = bell_rest[n][0] - Vector((0, 0, 0.0032 * max(dip, -0.2)))
        q = 0.0 if dt < 0 else exp(-dt / 0.35) * sin(2 * pi * dt / 0.045)
        for n in ("bell_dome", "bell_bead"):
            r = bell_rest[n][1].copy()
            r.x += radians(0.18) * q
            r.y += radians(0.12) * q * 0.7
            bell_obs[n].rotation_euler = r
    drift_shot("s2_bell", 2, "world/x_bell.png", "CAM_bell", 17.95, 19.35, 860, 660, 1.15, "night", 0.3,
               "Barnaby arrives: the bell's plunger dips on its own on the bell cue (18.0) and the dome quivers "
               "as it rings; slow push.", extra=bell)

    # the mouse: one click clip, reused for every click (align frame 13 to each mouse_click cue)
    mb = bpy.data.objects["mouse_body"]
    me = mb.data
    if not me.shape_keys:
        mb.shape_key_add(name="Basis")
    sk = mb.shape_key_add(name="click_L")
    wx = -0.0015
    for i, v in enumerate(me.vertices):
        x, y, z = v.co
        yb = 0.0105 + 7.8 * x * x
        if x < wx - 0.0008 and y > yb + 0.0008:
            w = clamp01((wx - 0.0008 - x) / 0.004) * clamp01((y - yb) / 0.03)
            sk.data[i].co = Vector((x, y, z - 0.0009 * w))
    sk.value = 0.0
    T_CLICK0 = 69.09

    def click(t):
        dt = t - T_CLICK0
        k = sine(P(dt, -0.05, 0.05)) if dt < 0 else 1.0 - sine(P(dt, 0.06, 0.07))
        sk.value = k
    sh = drift_shot("x_mouse_click", 4, "world/x_mouse_monday.png", "CAM_mouse", T_CLICK0 - 0.5 + 0.5, T_CLICK0 + 2.0,
                    960, 575, 1.08, "monday", 0.0,
                    "One click clip for every mouse_click: the left button dips on frame 13 (0.50 s after frame "
                    "0001). Start is s4's click (69.09); reuse it with frame 13 on s5's 84.59 and 84.99 and s6's "
                    "142.32. Slow push.", extra=click)

    drift_shot("s5_pot", 5, "world/x_pot_monday.png", "CAM_pot", 87.11, 88.93, 990, 540, 1.12, "monday", 0.0,
               "Slow push on the pen pot (Kwame's clunk).")
    drift_shot("s5_drawer", 5, "world/x_drawer_monday.png", "CAM_drawer", 88.93, 90.72, 930, 560, 1.12, "monday",
               0.2, "Slow push into drawer 2 (the BACKUP stick).")
    return shots


# ================================================================================================ Lisbon
def build_lisbon(args):
    import lisbon as LM
    DM = LM.D
    cap = {}
    bm, bo, ba = DM.build_materials, LM.build_outside, LM.build_arm_and_monitors

    def _bm():
        cap["M"] = bm()
        return cap["M"]

    def _bo(M):
        cap["lit_m"], cap["sky_m"] = bo(M)
        return cap["lit_m"], cap["sky_m"]

    DM.build_materials, LM.build_outside = _bm, _bo
    argv = sys.argv
    sys.argv = [argv[0], "--", "--no-render", "--samples", str(args.samples)]
    try:
        LM.main()
    finally:
        sys.argv = argv
    DM.build_materials, LM.build_outside = bm, bo
    make_rig(DM)
    return LM, DM, cap


def lisbon_shots(LM, DM, cap):
    sc = bpy.context.scene
    L = DM.LIGHTS
    M = cap["M"]
    shots = {}
    base = {}
    asleep = {"main": os.path.join(LM.SCREEN_DIR, "lisbon-main-asleep.png"),
              "studio": os.path.join(LM.SCREEN_DIR, "lisbon-black.png"),
              "laptop": os.path.join(LM.SCREEN_DIR, "lisbon-black.png")}
    aspects = {"main": 16 / 9, "studio": 16 / 9, "laptop": 16 / 10}
    ASLEEP_MAIN = 0.5                                   # the bell's glow level on the sleeping main monitor
    STREET, ADAPT = 140.0, 0.8
    street = DM.light("A_street", "SPOT", (-1.7, 1.15, 1.6), 0.0, (1.0, 0.64, 0.32), "NIGHT", spot=50, blend=0.85,
                      radius=0.35)
    DM.aim(street, (1.5, 2.45, 0.72))

    def night_extra():
        L["A_street"].data.energy = STREET

    def outside_for(cam_p, wide):
        for ob in LM.COLL["OUTSIDE"].objects:
            hide = False
            if wide:
                for c in ob.bound_box:
                    v = ob.matrix_world @ Vector(c)
                    tt = (-LM.SIDE_T - cam_p.x) / (v.x - cam_p.x) if v.x < -LM.SIDE_T else None
                    if tt is None or cam_p.y + tt * (v.y - cam_p.y) < 0.05 or cam_p.z + tt * (v.z - cam_p.z) > LM.LH:
                        hide = True
                        break
            if ob.name == "lx_sky_wide":
                hide = not wide
            ob.hide_render = hide

    def preset(name):
        def setup():
            LM.apply_preset(name, M, cap["sky_m"], cap["lit_m"])
            night_extra()
            outside_for(None, False)
            base.clear()
            base["exp"] = sc.view_settings.exposure
        return setup

    def glow(slot, bright):
        import numpy as np
        mean = LM.PANELS[slot].get("mean")
        if mean is None:
            return
        lum = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
        b0 = 1.5 if slot == "laptop" else 4.0
        L[f"LL_glow_{slot}"].data.energy = b0 * bright * max(lum, 0.01) / 0.08

    def sleep_setup():
        LM.apply_preset("night", M, cap["sky_m"], cap["lit_m"])
        night_extra()
        outside_for(None, False)
        for slot in ("main", "studio", "laptop"):
            LM.set_panel(slot, asleep[slot], aspects[slot])
        base.clear()
        base["exp"] = sc.view_settings.exposure

    # ---------------------------------------------------------------- 8 · s9 Lisbon night: the monitors sleep
    sh = Shot("s9_lisbon_night", 9, ["world/lisbon_03_medium_night.png"], 204.31, 204.31 + 2 * 4.73, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    sh8 = sh
    N0 = pose("LCAM_medium")
    N1 = N0                                              # held (SHOTLIST 9.2)
    T_DIM, T_DARK = 204.31 + 2.5, 204.31 + 5.0
    sh.notes = (f"20:07: starts on the approved still; from frame {sh.frame(T_DIM)} the two monitors and the "
                f"laptop dim and go dark (frame {sh.frame(T_DARK)}), then the main monitor shows Barnaby's bell, "
                f"small, bottom right (the shop's sleep screen's twin), full by frame {sh.frame(T_DARK + 1.95)}. "
                f"A sodium street lamp below the window rakes the desk and tiles, and the exposure adapts +{ADAPT} "
                f"EV as the monitors go out, so the room stays legible. Baked in: drop the CSS dimmer overlay. Held. "
                f"1600x900 at 12 samples, upscaled.")
    sh.active = [(T_DIM - 0.1, T_DARK + 0.35 + 1.6 + 0.1)]

    def f8(t):
        cam_between(N0, N1, CALM(P(t, sh8.start, sh8.frames / FPS)))
        sc.view_settings.exposure = base["exp"] + ADAPT * sine(P(t, T_DIM, T_DARK + 1.5 - T_DIM))
        if t < T_DARK:
            k = 1 - sine(P(t, T_DIM, T_DARK - T_DIM))
            for slot in ("main", "studio", "laptop"):
                b = LM.LBRIGHT["night"][slot] * k
                LM.PANELS[slot]["bright"].outputs[0].default_value = b
                glow(slot, b)
        else:
            g = sine(P(t, T_DARK + 0.35, 1.6))
            LM.PANELS["main"]["bright"].outputs[0].default_value = ASLEEP_MAIN * g
            glow("main", ASLEEP_MAIN * g)
            for slot in ("studio", "laptop"):
                LM.PANELS[slot]["bright"].outputs[0].default_value = 0.0
                L[f"LL_glow_{slot}"].data.energy = 0.0
    sh.segments = [(sh.start, preset("night")), (T_DARK, sleep_setup)]
    sh.frame_fn = f8
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 9b · s9 two desks: the Lisbon half
    sh = Shot("s9_two_desks_lisbon_half", 9, ["world/close_two_desks.png"], 208.34, 208.34 + 2 * 9.6,
              res=(800, 900))
    H0 = pose("LCAM_close_half")
    H1 = pushed(H0, 480, 560, 1.06, res=(960, 1080))
    sh9 = sh

    def f9(t):
        cam_between(H0, H1, CALM(P(t, sh9.start, sh9.frames / FPS)))
        sc.view_settings.exposure = base["exp"] + ADAPT
        LM.PANELS["main"]["bright"].outputs[0].default_value = ASLEEP_MAIN
        glow("main", ASLEEP_MAIN)
        for slot in ("studio", "laptop"):
            LM.PANELS[slot]["bright"].outputs[0].default_value = 0.0
            L[f"LL_glow_{slot}"].data.energy = 0.0
    sh.segments = [(sh.start, sleep_setup)]
    sh.frame_fn = f9
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 10 · s8 Lisbon day: a push into the desk
    sh = Shot("s8_lisbon_day", 8, ["world/lisbon_01_wide_day.png"], 176.97, 176.97 + 8.0, res=LONG_RES)
    sh.upscale_to = (1920, 1080)
    T8 = (177.6, 184.6)
    sh.notes = (f"Holds the approved wide, then one slow approach into the desk (frames {sh.frame(T8[0])}-"
                f"{sh.frame(T8[1])}) landing on lisbon_02_medium_day's framing. Full frame, no cam crop. 1600x900 "
                f"at 12 samples, upscaled.")
    W0, W1 = pose("LCAM_wide"), pose("LCAM_medium")
    mid_loc = W0["loc"].lerp(W1["loc"], 0.55) + Vector((0.1, 0, 0.25))
    path8 = Path([W0["loc"], mid_loc, W1["loc"]])

    def f10(t):
        u = bezier(0.45, 0.0, 0.3, 1.0)(P(t, T8[0], T8[1] - T8[0]))
        loc = path8.at(u)
        set_cam(loc, W0["tgt"].lerp(W1["tgt"], smoother(u)), lerp(W0["lens"], W1["lens"], u),
                W0["focus"].lerp(W1["focus"], u), lerp(W0["fstop"], W1["fstop"], u))

    def setup_wide():
        preset("day")()
        outside_for(W0["loc"], True)                    # the wide's outside, held for the whole move (no pops)
    sh.segments = [(sh.start, setup_wide)]
    sh.frame_fn = f10
    shots[sh.id] = sh
    sh8d = sh
    main_panel = next(o for o in bpy.data.objects if o.type == "MESH" and o.data.materials
                      and o.data.materials[0] == LM.PANELS["main"]["mat"])
    shots["quad_s8_lisbon_day"] = Task(lambda: screen_quad(sh8d, sh8d.frame(T8[1]), main_panel))
    shots["quads_s8_lisbon_day"] = Task(lambda: screen_quads(sh8d, main_panel))
    sh8d.events = {"lisbon_wide": 176.97, "realapp": T8[1]}
    sh8.events = {"lisbon_night": 204.31, "dim": T_DIM}

    def asleep_state():
        sleep_setup()
        LM.PANELS["main"]["bright"].outputs[0].default_value = ASLEEP_MAIN
        glow("main", ASLEEP_MAIN)
        for slot in ("studio", "laptop"):
            LM.PANELS[slot]["bright"].outputs[0].default_value = 0.0
            L[f"LL_glow_{slot}"].data.energy = 0.0
        sc.view_settings.exposure = base["exp"] + ADAPT

    shots["x_close_half_lisbon_2x"] = Still(
        "x_close_half_lisbon_2x", 9, "x_close_half_lisbon_2x.png", asleep_state, pose("LCAM_close_half"),
        res=(1920, 2160), notes="SHOTLIST 9.3: the Lisbon half at 2x (1920x2160) for the film's slow matched push, "
                                "the monitors asleep (bell glyph bottom right; laptop and studio dark). 32 samples.")
    shots["lisbon_03_medium_night_asleep"] = Still(
        "lisbon_03_medium_night_asleep", 9, "lisbon_03_medium_night_asleep.png", asleep_state, pose("LCAM_medium"),
        res=(1920, 1080), samples=64,
        notes="SHOTLIST 9.2: lisbon_03_medium_night with the monitors asleep (bell glyph bottom right; laptop and "
              "studio dark); crossfade from lisbon_03_medium_night.png (monitors on). 64 samples, as the approved still.")
    # the shop's CAM_medium_tuesday relative to its monitor (desk.py), scaled to the Lisbon main monitor's size
    bpy.context.view_layer.update()
    mp = main_panel
    lc = sum((mp.matrix_world @ Vector(c) for c in mp.bound_box), Vector()) / 8
    lw = max(mp.dimensions.x, mp.dimensions.y, mp.dimensions.z)
    shop_c, shop_cam, shop_tgt = Vector((1.0, 2.51, 0.995)), Vector((1.38, 0.3, 1.38)), Vector((1.26, 2.5, 0.97))
    k_sz = lw / 0.408                                   # same distance, a longer lens: the monitor the same size
    match = dict(loc=lc + (shop_cam - shop_c), tgt=lc + (shop_tgt - shop_c), lens=27.0 * k_sz, fstop=5.6,
                 focus=lc + Vector((0, -0.4, -0.1)))
    match["loc"].z = max(match["loc"].z, LM.DZ + 0.55)
    shots["lisbon_match_day"] = Still("lisbon_match_day", 8, "lisbon_match_day.png", preset("day"), match,
                                      notes="v2.3 match cut (Tue shop -> Lisbon): Theo's Lisbon desk by day framed "
                                            "like CAM_medium_tuesday (05_medium_tuesday): the main monitor at the same "
                                            "place and size in frame, the desk edge at the same height. 2560x1440, "
                                            "32 samples.")
    W0w = pose("LCAM_wide")

    def setup_wide4():
        preset("day")()
        outside_for(W0w["loc"], True)
    shots["quad_stills_lisbon"] = Task(lambda: (
        still_quad("lisbon_02_medium_day", 8, "lisbon_02_medium_day.png", pose("LCAM_medium"), main_panel,
                   (1920, 1080), "approved still (not re-rendered); screen_quad = the MAIN monitor, 1920x1080 px",
                   True),
        still_quad("lisbon_match_day", 8, "lisbon_match_day.png", match, main_panel, (2560, 1440))))
    shots["lisbon_01_wide_day_4k"] = Still("lisbon_01_wide_day_4k", 8, "lisbon_01_wide_day_4k.png", setup_wide4,
                                           W0w, res=(3840, 2160),
                                           notes="v2.3 plate for 2D pans: the approved Lisbon wide at 3840x2160 (same "
                                                 "framing). 32 samples.")
    shots["lisbon_03_medium_night_on"] = Still(
        "lisbon_03_medium_night_on", 9, "lisbon_03_medium_night_on.png", preset("night"), pose("LCAM_medium"),
        res=(1920, 1080), notes="SHOTLIST 9.2: lisbon_03_medium_night, monitors on, rendered with the same settings "
                                "as the asleep still so the crossfade is only the light. 32 samples.")

    # ---------------------------------------------------------------- Tier B · s8 the nata detail
    sh = Shot("s8_nata", 8, ["world/x_lisbon_detail_day.png"], 178.97, 180.47,
              notes="A slow push on the nata and the bica. Starts on the approved still.")
    D0 = pose("LCAM_detail")
    D1 = pushed(D0, 860, 600, 1.1)

    def f11(t):
        cam_between(D0, D1, DRIFT(P(t, 178.97, 180.97 - 178.97)))

    def setup_detail():
        preset("day")()
        sc.view_settings.exposure += -0.35
    sh.segments = [(sh.start, setup_detail)]
    sh.frame_fn = f11
    shots[sh.id] = sh
    return shots


# ================================================================================================ compose / main
def compose_two_desks():
    """Join the halves (shop left, Lisbon right) with the approved still's thin dark seam."""
    left = os.path.join(OUT_ANIM, "s9_two_desks_shop_half")
    right = os.path.join(OUT_ANIM, "s9_two_desks_lisbon_half")
    out = os.path.join(OUT_ANIM, "s9_two_desks")
    os.makedirs(out, exist_ok=True)
    n = len([f for f in os.listdir(left) if f.endswith(".jpg")])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(left, "%04d.jpg"),
           "-framerate", str(FPS), "-i", os.path.join(right, "%04d.jpg"), "-filter_complex",
           "[0][1]hstack=inputs=2,scale=1920:1080:flags=lanczos,drawbox=x=957:y=0:w=6:h=1080:color=0x040404:t=fill",
           "-q:v", "2", "-start_number", "1", os.path.join(out, "%04d.jpg")]
    subprocess.run(cmd, check=True)
    t0, t1 = 208.34, 208.34 + 2 * 9.6
    sh = Shot("s9_two_desks", 9, ["world/close_two_desks.png"], t0, t1,
              notes="A slow matched push on both halves (same timing, ~6%), long enough for the titles. Lisbon's "
                    "monitors stay asleep (bell glowing bottom right), continuing lisbon_03's dim; the shop is "
                    "asleep as approved. Halves rendered separately (800x900 each, 12 samples), joined with the "
                    "still's seam and upscaled to 1080p. ~20 s: trim to the new spans.")
    assert n == sh.frames, (n, sh.frames)
    sh.events = {"two_desks": t0}
    manifest_update(sh, "done")
    print("composed", n, "frames ->", out)


def profile(sh, args):
    """Time a few frames under different settings (render budget)."""
    sc = bpy.context.scene
    ee = sc.eevee
    sh.segments[0][1]()
    CUR["shot"], CUR["fn"] = sh, sh.frame_fn
    sc.camera = RIG["cam"]
    sc.render.image_settings.file_format = "JPEG"
    out = os.path.join(OUT_ANIM, "_test", "prof")
    os.makedirs(out, exist_ok=True)

    def run(label, n=3):
        sc.frame_start, sc.frame_end = 20, 19 + n
        sc.render.filepath = os.path.join(out, label + "_####")
        t = time.time()
        bpy.ops.render.render(animation=True)
        print(f"PROFILE {label}: {(time.time() - t) / n:.2f} s/frame")
    ee.taa_render_samples = 16
    run("warm", 2)
    run("s16")
    sc.render.use_compositing = False
    run("s16_nocomp")
    sc.render.use_compositing = True
    ee.taa_render_samples = 8
    run("s8")
    ee.taa_render_samples = 16
    ee.use_raytracing = False
    run("s16_nort")
    ee.use_raytracing = True
    ee.use_fast_gi = False
    run("s16_nofgi")
    ee.use_fast_gi = True
    ee.shadow_ray_count, ee.shadow_step_count = 1, 4
    run("s16_shadow1")
    ee.shadow_ray_count, ee.shadow_step_count = 2, 8
    pr = bpy.data.objects.get("screen_probe")
    if pr:
        pr.hide_render = True
        run("s16_noprobe")
        pr.hide_render = False


def parse():
    import argparse
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--set", default="shop")
    p.add_argument("--shots", default="")
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--scale", type=int, default=100)
    p.add_argument("--test", default="")
    p.add_argument("--compose", action="store_true")
    p.add_argument("--range", default="")
    p.add_argument("--profile", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--tmp", action="store_true")
    return p.parse_args(argv)


TIER_A = {"shop": "s1_open,s2_key_lamp,s3_timelapse,s3_shelf,s5_afternoon,s9_shop_night,s9_two_desks_shop_half",
          "lisbon": "s9_lisbon_night,s9_two_desks_lisbon_half,s8_lisbon_day"}


def main():
    args = parse()
    if args.compose:
        compose_two_desks()
        return
    t0 = time.time()
    if args.set == "shop":
        DM, M, hands = build_shop(args)
        shots = shop_shots(DM, M, hands)
    else:
        LM, DM, cap = build_lisbon(args)
        shots = lisbon_shots(LM, DM, cap)
    sc = bpy.context.scene
    sc.eevee.taa_render_samples = args.samples
    sc.render.use_lock_interface = True
    if _on_frame not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(_on_frame)
    print(f"ANIM build {args.set} in {time.time() - t0:.0f}s")
    if args.list:
        for s in shots.values():
            print(s.id, s.start, s.frames, s.seg_ranges())
        return
    if args.profile:
        profile(shots[args.shots.split(",")[0]], args)
        return
    test = [x for x in args.test.split(",") if x] or None
    for sid in [s for s in (args.shots or TIER_A[args.set]).split(",") if s]:
        try:
            it = shots[sid]
            if isinstance(it, Still):
                render_still(it, args, test)
            elif isinstance(it, Task):
                it.fn()
            else:
                render_shot(it, args, test)
        except Exception as e:                            # one bad shot must not stop the rest of the run
            import traceback
            traceback.print_exc()
            print(f"FAILED {sid}: {e!r}")
    print(f"ANIM total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
