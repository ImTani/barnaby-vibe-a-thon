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
        self.segments = []          # [(time the segment starts, setup())]
        self.frame_fn = None        # (t) -> None, continuous state for film time t
        self.out_dir = os.path.join(OUT_ANIM, sid)

    def time(self, f):
        return self.start + (f - 1) / FPS

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
    out_dir = os.path.join(OUT_ANIM, "_test", sh.id) if args.range else sh.out_dir
    os.makedirs(out_dir, exist_ok=True)
    if not args.range:
        manifest_update(sh, "rendering")
    for fa, fb, setup in sh.seg_ranges():
        fa, fb = max(fa, lo), min(fb, hi)
        if fb < fa:
            continue
        setup()
        sc.frame_start, sc.frame_end = fa, fb
        sc.frame_set(fa)
        sc.render.filepath = os.path.join(out_dir, "####")
        bpy.ops.render.render(animation=True)
    if args.range:
        dt = time.time() - t1
        print(f"RANGE {sh.id} {lo}-{hi}: {dt:.0f}s ({dt / (hi - lo + 1):.2f} s/frame)")
        return
    dt = time.time() - t1
    print(f"RENDERED {sh.id}: {sh.frames} frames in {dt:.0f}s ({dt / sh.frames:.2f} s/frame)")
    with open(os.path.join(OUT_ANIM, "_log.txt"), "a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} {sh.id} {sh.frames}f {dt:.0f}s {dt / sh.frames:.2f}s/f "
                 f"samples={args.samples} scale={args.scale}\n")
    if not sh.id.endswith("_half"):
        manifest_update(sh, "done")


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
    e = dict(id=sh.id, scene=sh.scene, replaces=sh.replaces[0] if len(sh.replaces) == 1 else sh.replaces,
             start=round(sh.start, 4), frames=sh.frames, status=status, notes=sh.notes)
    m["shots"] = [s for s in m["shots"] if s["id"] != sh.id] + [e]
    m["shots"].sort(key=lambda s: s["start"])
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


def shop_shots(DM, M, hands):
    L = DM.LIGHTS
    sc = bpy.context.scene
    bulb = DM.principled(M["bulb"]).inputs["Emission Strength"]
    shots = {}
    base = {}
    rest = [(ob, Vector(ob.location), ob.rotation_euler.copy()) for ob in
            (bpy.data.objects[n] for n in ("backoffice_key", "key_tag", "lamp_switch", "drawer_BRAKE PADS"))]

    def preset(name, ev=0.0):
        def setup():
            for ob, lc, rt in rest:                        # every animated prop back to its approved place
                ob.location, ob.rotation_euler = Vector(lc), rt.copy()
            if "A_sweep" in L:
                L["A_sweep"].data.energy = 0.0
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

    # ---------------------------------------------------------------- 1 · s1 opening: up from black, one push
    sh = Shot("s1_open", 1, ["world/01_wide_night.png", "world/02_medium_night.png"], 0.0, 4.45,
              notes="Up from black (light_up 0.70 -> 2.50, baked in: drop the still's brightness grade), then one "
                    "continuous push from the wide into the desk, landing framed on the monitor for the cut to "
                    "the full-screen PC at 'screen'. Covers both s1 stills; play full frame, no cam crop.")
    A, B = pose("CAM_wide"), pose("CAM_medium")
    C = dict(loc=scr_c + (B["loc"] - scr_c).normalized() * 0.8, tgt=scr_c.copy(), lens=50.0, fstop=2.8,
             focus=scr_c.copy())
    path_loc = [A["loc"], B["loc"].lerp(C["loc"], 0.15), C["loc"]]
    path_tgt = [A["tgt"], B["tgt"].lerp(C["tgt"], 0.3), C["tgt"]]
    path_foc = [A["focus"], B["focus"], C["focus"]]

    def f1(t):
        u = sine(P(t, 0.55, 4.55 - 0.55))
        set_cam(catmull(path_loc, u), catmull(path_tgt, u), lerp(A["lens"], C["lens"], smoother(u)),
                catmull(path_foc, u), lerp(1.6, 2.8, u))
        b = sine(P(t, 0.7, 1.8))
        sc.view_settings.exposure = base["exp"] + lerp(0.45, 0.0, smoother(u)) + 2.2 * math.log2(max(b, 1e-4))
        grid()
    sh.segments = [(sh.start, preset("night"))]
    sh.frame_fn = f1
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 2+3 · s2: the key lands, the lamp clicks off
    sh = Shot("s2_key_lamp", 2, ["world/03_keys_night.png"], 38.04, 40.34,
              notes="Theo's BACK OFFICE key drops in from above frame and lands on the keyboard on the key_tap "
                    "(38.59) with a small bounce, the tag settling after; the desk lamp clicks off on lamp_click "
                    "(39.79) and the room drops to the monitor's glow (baked in: drop the still's brightness "
                    "grade). Slow push toward the key.")
    K = pose("CAM_keys")
    K2 = pushed(K, 640, 840, 1.2)
    key = bpy.data.objects["backoffice_key"]
    tag = bpy.data.objects["key_tag"]
    sw = bpy.data.objects["lamp_switch"]
    key_rest = (Vector(key.location), key.rotation_euler.copy())
    tag_rest = (Vector(tag.location), tag.rotation_euler.copy())
    sw_rest = Vector(sw.location)
    T_LAND, T_LAMP = 38.59, 39.79
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

    def lamp_level(t):
        """1 = lamp on, 0 = off: the switch clicks at T_LAMP; a tungsten filament dies in ~0.1 s."""
        dt = t - T_LAMP
        return 1.0 if dt < 0 else exp(-dt / 0.035)

    def f2(t):
        cam_between(K, K2, DRIFT(P(t, 38.04, 40.84 - 38.04)))
        key_pose(t)
        lv = lamp_level(t)
        L["L_lamp"].data.energy = 40.0 * lv
        bulb.default_value = 20.0 * lv
        L["L_floor_spill"].data.energy = lerp(2.5, 9.0, lv)
        L["L_bounce"].data.energy = lerp(2.0, 7.0, lv)
        L["L_box_kick"].data.energy = lerp(2.0, 7.0, lv)
        press = clamp01(1 - abs(t - (T_LAMP - 0.02)) / 0.07)
        sw.location = sw_rest - Vector((0, 0, 0.0018 * press))
        grid()
    sh.segments = [(sh.start, preset("night"))]
    sh.frame_fn = f2
    sh.no_probe = True
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 4 · s3 time-lapse: Thursday night -> Monday
    sh = Shot("s3_timelapse", 3, ["world/02_medium_night.png", "world/04_medium_monday.png"], 40.34, 43.24,
              notes="Thursday night (lamp off, as s2 ends) -> daylight rakes across the desk and blows out -> "
                    "Monday 08:52 (props swapped inside the white flash, ~41.35) -> push toward the screen's clock "
                    "for the cut to shop-pc-04 at 'clock'. Brightness and the light sweep are baked in: drop the "
                    "still's brightness grade and the CSS sweep overlay.")
    Mm = pose("CAM_medium")
    Mm2 = pushed(Mm, 1040, 690, 1.5)                    # toward the taskbar clock: the cut is to the screen clock
    T_SWAP = 41.35
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
        u = DRIFT(P(t, 40.34, 43.3 - 40.34))
        cam_between(Mm, Mm2, u * u * (1.6 - 0.6 * u))   # creeps first, then pushes in toward the clock
        flash = clamp01(1 - abs(t - T_SWAP) / 0.32)
        RIG["flash"].default_value = smoother(flash) ** 1.4
        if t < T_SWAP:
            L["L_lamp"].data.energy = 0.0
            bulb.default_value = 0.0
            L["L_floor_spill"].data.energy = 2.5
            L["L_bounce"].data.energy = 2.0
            L["L_box_kick"].data.energy = 2.0
            dawn = sine(P(t, 40.45, T_SWAP - 40.45))
            sweep.data.energy = 30.0 * dawn
            sweep.rotation_euler = sundir(0.35 * dawn).to_track_quat("-Z", "Y").to_euler()
            sc.view_settings.exposure = base["exp"] + 5.0 * dawn ** 2.2
        else:
            k = sine(P(t, T_SWAP, 42.15 - T_SWAP))
            sweep.data.energy = 0.0
            sun.rotation_euler = sundir(lerp(0.35, 1.0, k)).to_track_quat("-Z", "Y").to_euler()
            sc.view_settings.exposure = base["exp"] + 4.0 * (1 - k) ** 2.0
        grid()
    sh.segments = [(sh.start, setup_night), (T_SWAP, preset("monday"))]
    sh.frame_fn = f3
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 5 · s3 shelf: drawer 1 slides open
    sh = Shot("s3_shelf", 3, ["world/x_shelf_monday.png"], 56.21, 58.56,
              notes="Drawer 1 (BRAKE PADS) slides open from shut, one pair inside; ends on the approved still's "
                    "state. Slow push toward the open drawer.")
    S0 = pose("CAM_shelf")
    S1 = pushed(S0, 560, 340, 1.25)
    dr = bpy.data.objects["drawer_BRAKE PADS"]
    dr_open = Vector(dr.location)
    dr_shut = Vector((dr_open.x, -0.008, dr_open.z))

    def f5(t):
        cam_between(S0, S1, DRIFT(P(t, 56.21, 58.9 - 56.21)))
        k = P(t, 56.45, 0.62)
        e = 1 - (1 - k) ** 3                            # pulled: quick start, soft stop
        over = 0.004 * sin(pi * P(t, 56.95, 0.22)) if t > 56.95 else 0.0
        dr.location = dr_shut.lerp(dr_open, e) + Vector((0, -over, 0))
    sh.segments = [(sh.start, preset("monday"))]
    sh.frame_fn = f5
    sh.no_probe = True
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 6 · s5 afternoon: the light slides across
    sh = Shot("s5_afternoon", 5, ["world/04_medium_monday.png"], 77.72, 80.99,
              notes="Monday afternoon: the window sun slides slowly across the desk; slow push toward the monitor. "
                    "Colour as approved (keep the film's AFT grade on top; drop the CSS sweep overlay).")
    Mo = pose("CAM_medium_monday")
    Mo2 = pushed(Mo, 900, 620, 1.2)
    d_aft0 = Vector((0.65, 0.55, -0.52))
    d_aft1 = Vector((0.80, 0.30, -0.44))

    def f6(t):
        cam_between(Mo, Mo2, DRIFT(P(t, 77.72, 81.49 - 77.72)))
        k = sine(P(t, 77.22, 81.49 - 77.22))
        sun.rotation_euler = d_aft0.lerp(d_aft1, k).normalized().to_track_quat("-Z", "Y").to_euler()
        grid()
    sh.segments = [(sh.start, preset("monday"))]
    sh.frame_fn = f6
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 7 · s9 shop night: the PC goes to sleep
    sh = Shot("s9_shop_night", 9, ["world/x_close_night.png"], 199.7, 204.81,
              notes="18:40, Martin gone (keys_jingle 200.7), lamp off. The monitor (Tuesday's jobs page) dims at "
                    "201.5, goes dark at 202.6, then Barnaby's bell glows up in the corner; the power LEDs go "
                    "blue -> amber as it sleeps. Ends on the approved still. Slow push.")
    C0 = pose("CAM_medium")
    C1 = pushed(C0, 900, 600, 1.15)
    tue = DM.SCREEN_PATHS["tuesday"]
    T_DIM, T_OFF = 201.5, 202.6

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
        cam_between(C0, C1, DRIFT(P(t, 199.7, 205.31 - 199.7)))
        if t < T_OFF + 0.15:
            lvl = lerp(0.88, 0.34, sine(P(t, T_DIM, 0.35)))
            lvl *= 1 - sine(P(t, T_OFF, 0.15))
            DM.SCREEN["bright"].outputs[0].default_value = lvl
            screen_light(lvl, base.get("mean_awake"))
        else:
            g = sine(P(t, T_OFF + 0.55, 1.3))
            DM.SCREEN["bright"].outputs[0].default_value = base["sbright"] * g
            screen_light(base["sbright"] * g)
        grid()
    sh.segments = [(sh.start, setup_awake), (T_OFF + 0.15, setup_asleep)]
    sh.frame_fn = f7
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 9a · s9 two desks: the shop half
    sh = Shot("s9_two_desks_shop_half", 9, ["world/close_two_desks.png"], 208.34, 217.94, res=(960, 1080))
    H0 = pose("CAM_close_half")
    H1 = pushed(H0, 480, 560, 1.06, res=(960, 1080))

    def f9(t):
        cam_between(H0, H1, DRIFT(P(t, 207.84, 218.44 - 207.84)))
        grid()
    sh.segments = [(sh.start, preset("close"))]
    sh.frame_fn = f9
    shots[sh.id] = sh
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
        outside_for(None, False)
        for slot in ("main", "studio", "laptop"):
            LM.set_panel(slot, asleep[slot], aspects[slot])
        base.clear()
        base["exp"] = sc.view_settings.exposure

    # ---------------------------------------------------------------- 8 · s9 Lisbon night: the monitors sleep
    sh = Shot("s9_lisbon_night", 9, ["world/lisbon_03_medium_night.png"], 204.31, 209.04,
              notes="20:07: starts on the approved still; on 'dim' (204.81) the two monitors and the laptop dim "
                    "and go dark, then the main monitor shows Barnaby's bell, small, bottom right (the shop's "
                    "sleep screen's twin). Baked in: drop the CSS dimmer overlay. Slow push.")
    N0 = pose("LCAM_medium")
    N1 = pushed(N0, 1040, 540, 1.18)
    T_DIM, T_DARK = 204.81, 206.25

    def f8(t):
        cam_between(N0, N1, DRIFT(P(t, 204.31, 209.54 - 204.31)))
        if t < T_DARK:
            k = 1 - sine(P(t, T_DIM, T_DARK - T_DIM))
            for slot in ("main", "studio", "laptop"):
                b = LM.LBRIGHT["night"][slot] * k
                LM.PANELS[slot]["bright"].outputs[0].default_value = b
                glow(slot, b)
        else:
            g = sine(P(t, T_DARK + 0.35, 1.2))
            LM.PANELS["main"]["bright"].outputs[0].default_value = ASLEEP_MAIN * g
            glow("main", ASLEEP_MAIN * g)
            for slot in ("studio", "laptop"):
                LM.PANELS[slot]["bright"].outputs[0].default_value = 0.0
                L[f"LL_glow_{slot}"].data.energy = 0.0
    sh.segments = [(sh.start, preset("night")), (T_DARK, sleep_setup)]
    sh.frame_fn = f8
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 9b · s9 two desks: the Lisbon half
    sh = Shot("s9_two_desks_lisbon_half", 9, ["world/close_two_desks.png"], 208.34, 217.94, res=(960, 1080))
    H0 = pose("LCAM_close_half")
    H1 = pushed(H0, 480, 560, 1.06, res=(960, 1080))

    def f9(t):
        cam_between(H0, H1, DRIFT(P(t, 207.84, 218.44 - 207.84)))
        LM.PANELS["main"]["bright"].outputs[0].default_value = ASLEEP_MAIN
        glow("main", ASLEEP_MAIN)
        for slot in ("studio", "laptop"):
            LM.PANELS[slot]["bright"].outputs[0].default_value = 0.0
            L[f"LL_glow_{slot}"].data.energy = 0.0
    sh.segments = [(sh.start, sleep_setup)]
    sh.frame_fn = f9
    shots[sh.id] = sh

    # ---------------------------------------------------------------- 10 · s8 Lisbon day: a push into the desk
    sh = Shot("s8_lisbon_day", 8, ["world/lisbon_01_wide_day.png"], 176.97, 179.37,
              notes="Starts on the approved wide, one eased push into the desk toward lisbon_02_medium_day's "
                    "framing (the detail crossfades in at 'nata', mid-landing). Play full frame, no cam crop.")
    W0, W1 = pose("LCAM_wide"), pose("LCAM_medium")
    mid_loc = W0["loc"].lerp(W1["loc"], 0.55) + Vector((0.1, 0, 0.25))

    def f10(t):
        u = SLOW_SETTLE(P(t, 176.97, 179.75 - 176.97))
        loc = catmull([W0["loc"], mid_loc, W1["loc"]], u)
        set_cam(loc, W0["tgt"].lerp(W1["tgt"], smoother(u)), lerp(W0["lens"], W1["lens"], u),
                W0["focus"].lerp(W1["focus"], u), lerp(W0["fstop"], W1["fstop"], u))

    def setup_wide():
        preset("day")()
        outside_for(W0["loc"], True)                    # the wide's outside, held for the whole move (no pops)
    sh.segments = [(sh.start, setup_wide)]
    sh.frame_fn = f10
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
           "[0][1]hstack=inputs=2,drawbox=x=957:y=0:w=6:h=1080:color=0x040404:t=fill",
           "-q:v", "2", "-start_number", "1", os.path.join(out, "%04d.jpg")]
    subprocess.run(cmd, check=True)
    t0, t1 = 208.34, 217.94
    sh = Shot("s9_two_desks", 9, ["world/close_two_desks.png"], t0, t1,
              notes="A slow matched push on both halves (same timing, ~6%), long enough for the titles. Lisbon's "
                    "monitors stay asleep (bell glowing bottom right), continuing lisbon_03's dim; the shop is "
                    "asleep as approved. Halves rendered separately and joined with the still's seam.")
    assert n == sh.frames, (n, sh.frames)
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
            render_shot(shots[sid], args, test)
        except Exception as e:                            # one bad shot must not stop the rest of the run
            import traceback
            traceback.print_exc()
            print(f"FAILED {sid}: {e!r}")
    print(f"ANIM total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
