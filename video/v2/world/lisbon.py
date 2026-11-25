"""Barnaby film v2: Theo's desk at the animation studio in Lisbon (scenes 8 and 9), the film's second set.

The same miniature as the shop desk (video/v2/world/desk.py): it imports desk.py's helpers, palette, LCD treatment and
Theo's props, so the plant from the moving box, the framed 2009 photo and his headphones are the exact same objects.

Run from the repo root (Git Bash):
    source scripts/env.sh
    "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
        --python video/v2/world/lisbon.py -- [options]

Options (after the `--`):
    --shots a,b,...    stills (default: wide_day,medium_day,medium_night; also close_half, pair (the two-desk close,
                       needs desk.py's out/x_close_half_shop.png), detail_day, and the hero props close: mouse_day,
                       stand_day)
    --scale N / --samples N / --save-blend / --no-render     as desk.py

Screens: video/v2/look/frames/lisbon-02-realapp-{main,studio,laptop}.png by day (Mon 23 Nov, 09:39, scene 8) and
lisbon-05-night-* at night (Tue 24 Nov, 20:07, scene 9), else placeholders from make_screens.py.
Collections: SET, OUTSIDE (the rooftops), DAY and NIGHT (lights), CAMS. dress_lisbon() wears the set after the build
(desk.py's weather machinery with LISBON_RULES: two days in, an old building).
"""
import argparse
import math
import os
import random
import sys
import time
from math import cos, pi, radians, sin

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import desk as D  # noqa: E402  (Blender runs this file as a script)
from desk import (COLL, LIGHTS, MATS, aim, annulus, box, boxmm, brick, camera, circ_pts, connector, curve,  # noqa: E402
                  cyl, disc, flat, finish, grp, lathe, light, link, mat, noisy, port, port_frame, principled,
                  prism, rect, rgba, sock, sphere, text, torus, tube, use, wood, _bump, _mix)

OUT = D.OUT
SCREEN_DIR = D.SCREEN_DIR
FRAMES = D.FRAMES

# room (metres; x right, y into the room, z up). Old Pombaline walls are thick: the window has a deep reveal.
LW, LD, LH, LWT, SIDE_T = 3.2, 2.62, 2.9, 0.14, 0.34
WIN = (1.22, 2.3, 0.95, 2.62)               # window in the left wall: y0, y1, z0, z1
DZ = 0.74                                   # desk top
DX0, DX1, DY0, DY1 = 0.42, 2.02, 1.86, 2.58

SHOTS = {
    "wide_day": ("LCAM_wide", "day", "lisbon_01_wide_day.png", 0.0),
    "medium_day": ("LCAM_medium", "day", "lisbon_02_medium_day.png", 0.0),
    "medium_night": ("LCAM_medium", "night", "lisbon_03_medium_night.png", 0.0),
    "detail_day": ("LCAM_detail", "day", "x_lisbon_detail_day.png", -0.35),
    "close_half": ("LCAM_close_half", "night", "x_close_half_lisbon.png", 0.0, (960, 1080)),
    # hero props, close (pass 4)
    "mouse_day": ("LCAM_mouse", "day", "x_lisbon_mouse_day.png", -0.25),
    "stand_day": ("LCAM_stand", "day", "x_lisbon_stand_day.png", -0.25),
}
DEFAULT_SHOTS = "wide_day,medium_day,medium_night"


def frame_or(name, placeholder):
    p = os.path.join(FRAMES, name)
    return p if os.path.exists(p) else os.path.join(SCREEN_DIR, placeholder)


LSCREENS = {
    "day": {"main": frame_or("lisbon-02-realapp-main.png", "lisbon-main-placeholder.png"),
            "studio": frame_or("lisbon-02-realapp-studio.png", "lisbon-second-placeholder.png"),
            "laptop": frame_or("lisbon-02-realapp-laptop.png", "lisbon-laptop-placeholder.png")},
    "night": {"main": frame_or("lisbon-05-night-main.png", "lisbon-main-asleep.png"),
              "studio": frame_or("lisbon-05-night-studio.png", "lisbon-black.png"),
              "laptop": frame_or("lisbon-05-night-laptop.png", "lisbon-black.png")},
}
# panel brightness: by day against Lisbon sun; at night dimmed to a glow (the closing cut)
LBRIGHT = {"day": {"main": 1.15, "studio": 1.1, "laptop": 1.15}, "night": {"main": 0.5, "studio": 0.2, "laptop": 0.22}}
# the day's level (v2.4, chosen from five test renders against 05_medium_tuesday, the shot it cuts from): world light
# (was 0.55), the sky's glow in the window (was 2.6, read white), exposure (was 0.15), bloom (threshold, strength)
DAY_WORLD, DAY_SKY, DAY_EV, DAY_BLOOM = 0.25, 1.3, 0.0, (2.0, 0.12)
PANELS = {}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default=DEFAULT_SHOTS)
    p.add_argument("--scale", type=int, default=100)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--save-blend", action="store_true")
    p.add_argument("--no-render", action="store_true")
    return p.parse_args(argv)


# ================================================================ materials of the new set
def birch_ply(name="birch_ply"):
    """Birch plywood desktop: pale grain on the faces, the laminations striped on the edges."""
    if name in MATS:
        return MATS[name]
    m = wood(name, "#d9bf94", "#c9ac7f", 0.42, grain=9.0, coat=0.25)
    nt, b = m.node_tree, principled(m)
    base = b.inputs["Base Color"].links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], ab.inputs[0])
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "LESS_THAN"
    nt.links.new(ab.outputs[0], edge.inputs[0])
    edge.inputs[1].default_value = 0.5
    pos = nt.nodes.new("ShaderNodeTexCoord")
    sz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos.outputs["Object"], sz.inputs[0])
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    nt.links.new(sz.outputs["Z"], st.inputs[0])
    st.inputs[1].default_value = 2 * pi / 0.0018              # a ply every 1.8 mm
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    nt.links.new(st.outputs[0], sn.inputs[0])
    plies = _mix(nt, sn.outputs[0], "#e2cfa8", "#9c7c52")
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(edge.outputs[0], sock(mx.inputs, "Factor_Float"))
    nt.links.new(base, sock(mx.inputs, "A_Color"))
    nt.links.new(plies, sock(mx.inputs, "B_Color"))
    nt.links.new(sock(mx.outputs, "Result_Color"), b.inputs["Base Color"])
    return m


def azulejo(name="azulejo", size=0.14):
    """Blue-and-white tiles: per tile a centre rosette, a cross and quarter circles meeting at the corners."""
    if name in MATS:
        return MATS[name]
    m = mat(name, "#eef0ea", 0.25, spec=0.6, coat=0.5)
    nt, b = m.node_tree, principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(mp.outputs["Vector"], sep.inputs[0])

    def M_(op, a, c=None):
        return D._math(nt, op, a, c)
    # tiles live on walls facing x or y: use (x + y) as the horizontal and z as the vertical
    u = M_("FRACT", M_("ADD", sep.outputs["X"], sep.outputs["Y"]))
    v = M_("FRACT", sep.outputs["Z"])
    du, dv = M_("SUBTRACT", u, 0.5), M_("SUBTRACT", v, 0.5)
    r = M_("SQRT", M_("ADD", M_("MULTIPLY", du, du), M_("MULTIPLY", dv, dv)))
    rosette = M_("SUBTRACT", M_("LESS_THAN", r, 0.17), M_("LESS_THAN", r, 0.08))
    dot = M_("LESS_THAN", r, 0.04)
    cu, cv = M_("SUBTRACT", 0.5, M_("ABSOLUTE", du)), M_("SUBTRACT", 0.5, M_("ABSOLUTE", dv))
    rc = M_("SQRT", M_("ADD", M_("MULTIPLY", cu, cu), M_("MULTIPLY", cv, cv)))
    corner = M_("SUBTRACT", M_("LESS_THAN", rc, 0.24), M_("LESS_THAN", rc, 0.16))
    cross = M_("MULTIPLY", M_("LESS_THAN", M_("MINIMUM", M_("ABSOLUTE", du), M_("ABSOLUTE", dv)), 0.025),
               M_("LESS_THAN", r, 0.33))
    ink = M_("MINIMUM", M_("ADD", M_("ADD", rosette, dot), M_("ADD", corner, cross)), 1.0)
    grout = M_("MAXIMUM", M_("LESS_THAN", M_("MINIMUM", u, v), 0.02), M_("GREATER_THAN", M_("MAXIMUM", u, v), 0.98))
    col = _mix(nt, ink, "#eef0ea", "#23508f")
    gm = nt.nodes.new("ShaderNodeMix")
    gm.data_type = "RGBA"
    nt.links.new(grout, sock(gm.inputs, "Factor_Float"))
    nt.links.new(col, sock(gm.inputs, "A_Color"))
    sock(gm.inputs, "B_Color").default_value = rgba("#c9c4b8")
    nt.links.new(sock(gm.outputs, "Result_Color"), b.inputs["Base Color"])
    _bump(nt, b, grout, 0.3, 0.002)
    return m


def roof_tiles(name="telha"):
    """Terracotta Roman tiles: rows of rounded channels with weathered variation."""
    if name in MATS:
        return MATS[name]
    m = mat(name, "#b5563a", 0.8)
    nt, b = m.node_tree, principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(_mix(nt, nz.outputs["Fac"], "#c2603e", "#8f3f2a"), b.inputs["Base Color"])
    _bump(nt, b, wave.outputs["Fac"], 0.6, 0.01)
    return m


def panel_material(slot):
    """A modern matte IPS panel: the image emitted (fitted to the panel), a faint veil, a dim IPS black level, and a
    satin anti-glare surface. One per screen slot; set_panel() swaps the picture per preset."""
    m = bpy.data.materials.new("panel_" + slot)
    m.use_nodes = True
    nt, b = m.node_tree, principled(m)
    b.inputs["Base Color"].default_value = rgba("#060607")
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Specular IOR Level"].default_value = 0.4
    uvn = nt.nodes.new("ShaderNodeUVMap")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(uvn.outputs["UV"], mp.inputs["Vector"])
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.interpolation = "Cubic"
    tx.extension = "CLIP"
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    hx = nt.nodes.new("ShaderNodeTexImage")
    hx.interpolation = "Linear"
    hx.extension = "CLIP"
    nt.links.new(mp.outputs["Vector"], hx.inputs["Vector"])
    veil = nt.nodes.new("ShaderNodeMix")
    veil.data_type = "RGBA"
    veil.blend_type = "ADD"
    sock(veil.inputs, "Factor_Float").default_value = 0.06
    nt.links.new(tx.outputs["Color"], sock(veil.inputs, "A_Color"))
    nt.links.new(hx.outputs["Color"], sock(veil.inputs, "B_Color"))
    blk = nt.nodes.new("ShaderNodeMix")
    blk.data_type = "RGBA"
    blk.blend_type = "ADD"
    sock(blk.inputs, "Factor_Float").default_value = 0.0015
    nt.links.new(sock(veil.outputs, "Result_Color"), sock(blk.inputs, "A_Color"))
    sock(blk.inputs, "B_Color").default_value = rgba("#cfd6e2")
    nt.links.new(sock(blk.outputs, "Result_Color"), b.inputs["Emission Color"])
    val = nt.nodes.new("ShaderNodeValue")
    val.outputs[0].default_value = 1.0
    nt.links.new(val.outputs[0], b.inputs["Emission Strength"])
    PANELS[slot] = dict(mat=m, tex=tx, halo=hx, mapping=mp, bright=val, aspect=None, path=None)
    return m


def set_panel(slot, path, aspect):
    p = PANELS[slot]
    if p["path"] == path:
        return
    img = bpy.data.images.load(path, check_existing=True)
    p["tex"].image = img
    w, h = img.size
    a = w / h
    sx = sy = 1.0
    if abs(a - aspect) > 0.01:                                # letterbox / pillarbox anything that doesn't fit
        if a > aspect:
            sy = a / aspect
        else:
            sx = aspect / a
    p["mapping"].inputs["Scale"].default_value = (sx, sy, 1)
    p["mapping"].inputs["Location"].default_value = (0.5 * (1 - sx), 0.5 * (1 - sy), 0)
    p["halo"].image = D.halation_image(img, "halation_" + os.path.basename(path))
    p["mean"] = D.SCREEN.get("mean")
    p["path"] = path
    print(f"panel {slot}: {os.path.basename(path)} {w}x{h}")


def screen_plane(name, w, h, m, parent, loc, rot=(0, 0, 0)):
    """A UV-mapped plane in the parent's XZ plane facing -Y."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = t
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    ob = finish(name, bm, m, parent, loc, rot, smooth=False)
    ob.visible_shadow = False
    return ob


# ================================================================ the room
def build_room(M):
    use("SET")
    boxmm("plinth", (-SIDE_T - 0.06, -0.09, -0.24), (LW + 0.06, LD + LWT + 0.03, -0.03), M["plinth"], bev=0.02, seg=3)
    oak = [wood(f"lx_floor{i}", a, b, 0.55, axis="Y", grain=5.0) for i, (a, b) in
           enumerate((("#c49a6c", "#ad8459"), ("#bd9264", "#a67d52"), ("#caa274", "#b38a5e")))]
    rng = random.Random(1755)                                 # the year Lisbon was rebuilt
    pw, x, i = 0.19, -SIDE_T, 0
    while x < LW - 0.001:
        x1 = min(x + pw, LW)
        cut = rng.uniform(0.4, 2.0)
        for j, (y0, y1) in enumerate([(-0.07, cut), (cut, LD + 0.02)]):
            boxmm(f"lx_board_{i}_{j}", (x + 0.0015, y0 + 0.0015, -0.03), (x1 - 0.0015, y1 - 0.0015, rng.uniform(-0.001,
                                                                                                         0.001)),
                  oak[rng.randrange(3)], bev=0.004, seg=1)
        x, i = x1, i + 1
    lime = noisy("lime", "#e6ddcc", "#dbd1bf", 0.92, scale=3.0, bump=0.06)
    wy0, wy1, wz0, wz1 = WIN
    for k, (a, b) in enumerate([((-SIDE_T, LD, 0), (LW, LD + LWT, LH)),
                                ((-SIDE_T, 0, 0), (0, wy0, LH)), ((-SIDE_T, wy1, 0), (0, LD, LH)),
                                ((-SIDE_T, wy0, 0), (0, wy1, wz0)), ((-SIDE_T, wy0, wz1), (0, wy1, LH))]):
        boxmm(f"lx_wall{k}", a, b, lime, bev=0)
    boxmm("lx_cap_back", (-SIDE_T, LD, LH), (LW, LD + LWT, LH + 0.008), M["section"], bev=0)
    boxmm("lx_cap_left", (-SIDE_T, -0.008, LH), (0, LD, LH + 0.008), M["section"], bev=0)
    boxmm("lx_cap_left_front", (-SIDE_T, -0.008, -0.03), (0, 0, LH + 0.008), M["section"], bev=0)
    boxmm("lx_cap_back_end", (LW, LD, -0.03), (LW + 0.008, LD + LWT, LH + 0.008), M["section"], bev=0)
    for nm, a, b in [("lx_shadow_ceiling", (-SIDE_T, -0.3, LH + 0.012), (LW + 0.3, 6.3, LH + 0.05)),
                     ("lx_shadow_front", (-SIDE_T, -0.34, 0.0), (LW + 0.3, -0.3, LH + 0.05)),
                     ("lx_shadow_right", (LW + 0.26, -0.3, 0.0), (LW + 0.3, LD + LWT, LH + 0.05))]:
        blk = boxmm(nm, a, b, M["section"], bev=0)
        blk.visible_camera = False
    # azulejo dado (blue-and-white tiles to 0.92 m) with a cream bullnose on top, round the back and left walls
    tiles = azulejo()
    boxmm("lx_tiles_back", (0, LD - 0.01, 0), (LW, LD, 0.92), tiles, bev=0)
    boxmm("lx_tiles_left_a", (0, 0, 0), (0.01, wy0 - 0.06, 0.92), tiles, bev=0)
    boxmm("lx_tiles_left_b", (0, wy1 + 0.06, 0), (0.01, LD - 0.01, 0.92), tiles, bev=0)
    boxmm("lx_tiles_left_c", (0, wy0 - 0.06, 0), (0.01, wy1 + 0.06, 0.92), tiles, bev=0)
    cream = mat("lx_cream", "#e8dfc9", 0.45)
    boxmm("lx_bullnose_back", (0, LD - 0.022, 0.92), (LW, LD, 0.945), cream, bev=0.008)
    boxmm("lx_bullnose_left", (0, 0, 0.92), (0.022, LD, 0.945), cream, bev=0.008)
    # the tall window: deep reveal, inner shutters folded back, two casements with glazing bars, a marble sill
    white = mat("lx_paint", "#f2efe7", 0.4, spec=0.5)
    marble = noisy("lx_marble", "#ece8df", "#d9d3c8", 0.25, scale=6.0)
    boxmm("lx_sill", (-SIDE_T + 0.05, wy0 - 0.04, wz0 - 0.04), (0.04, wy1 + 0.04, wz0), marble, bev=0.006)
    fx0, fx1 = -SIDE_T + 0.06, -SIDE_T + 0.1
    for nm, a, b in [("lx_frame_A", (fx0, wy0, wz0), (fx1, wy0 + 0.05, wz1)), ("lx_frame_B", (fx0, wy1 - 0.05, wz0),
                                                                                (fx1, wy1, wz1)),
                     ("lx_frame_T", (fx0, wy0, wz1 - 0.05), (fx1, wy1, wz1)), ("lx_frame_Bt", (fx0, wy0, wz0),
                                                                              (fx1, wy1, wz0 + 0.05)),
                     ("lx_meet", (fx0 - 0.005, (wy0 + wy1) / 2 - 0.025, wz0), (fx1 + 0.005, (wy0 + wy1) / 2 + 0.025, wz1))]:
        boxmm(nm, a, b, white, bev=0.005)
    for side, (y0, y1) in enumerate(((wy0 + 0.05, (wy0 + wy1) / 2 - 0.025), ((wy0 + wy1) / 2 + 0.025, wy1 - 0.05))):
        for k in range(1, 4):                                 # four panes high
            z = wz0 + 0.05 + k * (wz1 - wz0 - 0.1) / 4
            boxmm(f"lx_bar_h{side}{k}", (fx0 + 0.008, y0, z - 0.012), (fx1 - 0.008, y1, z + 0.012), white, bev=0.003)
    # v2.4: old window glass, a little hazy: once the day came down, the shop's sharp glass mirrored the sunlit floor
    # as a hard white ghost over the roofs; rougher, the room's reflection is a soft sheen
    lg = M["glass"].copy()
    lg.name = "lx_window_glass"
    principled(lg).inputs["Roughness"].default_value = 0.35
    boxmm("lx_glass", (fx0 + 0.018, wy0, wz0), (fx0 + 0.022, wy1, wz1), lg, bev=0).visible_shadow = False
    cyl("lx_espag", 0.007, wz1 - wz0 - 0.2, (fx1 + 0.012, (wy0 + wy1) / 2, (wz0 + wz1) / 2), M["brass"], n=8)
    for s, y in ((-1, wy0), (1, wy1)):                        # shutters folded into the reveal
        for k in range(2):
            yy = y + (-0.012 if s < 0 else 0.012)
            sh = boxmm(f"lx_shutter{s}{k}", (fx1 + 0.01 + k * 0.12, yy - 0.012, wz0 + 0.02),
                       (fx1 + 0.12 + k * 0.12, yy + 0.012, wz1 - 0.02), white, bev=0.006)
            for p in range(3):
                z0_ = wz0 + 0.12 + p * (wz1 - wz0 - 0.2) / 3
                boxmm(f"lx_shutter_panel{s}{k}{p}", (fx1 + 0.03 + k * 0.12, yy - s * 0.014, z0_),
                      (fx1 + 0.1 + k * 0.12, yy - s * 0.012, z0_ + (wz1 - wz0 - 0.3) / 3), white, bev=0.004)
    # Juliet balcony outside: black iron
    iron = mat("lx_iron", "#1d1e20", 0.5, metal=0.6)
    bx = -SIDE_T - 0.06
    tube("lx_rail_top", (bx, wy0 - 0.05, wz0 + 0.95), (bx, wy1 + 0.05, wz0 + 0.95), 0.012, iron, n=8)
    tube("lx_rail_bot", (bx, wy0 - 0.05, wz0 + 0.06), (bx, wy1 + 0.05, wz0 + 0.06), 0.01, iron, n=8)
    for k in range(13):
        y = wy0 - 0.03 + k * (wy1 - wy0 + 0.06) / 12
        tube(f"lx_baluster{k}", (bx, y, wz0 + 0.06), (bx, y, wz0 + 0.95), 0.006, iron, n=6)
    boxmm("lx_balcony_slab", (bx - 0.25, wy0 - 0.1, wz0 - 0.08), (-SIDE_T, wy1 + 0.1, wz0 - 0.02), marble, bev=0.01)
    # the wall socket under the desk (Portugal: Schuko) and a light switch by the window
    socket = mat("lx_socket", "#f4f2ec", 0.4)
    box("lx_wall_socket", (0.16, 0.012, 0.085), (1.55, LD - 0.016, 0.3), socket, bev=0.004)
    for k, x in enumerate((1.51, 1.59)):
        cyl(f"lx_socket_well{k}", 0.019, 0.006, (x, LD - 0.024, 0.3), mat("lx_socket_in", "#dedad0", 0.5),
            rot=(90, 0, 0), n=16)
    box("lx_switch", (0.012, 0.085, 0.085), (0.006, wy0 - 0.2, 1.2), socket, bev=0.004)


def build_outside(M):
    """Lisbon from the third floor: terracotta roofs and pastel façades falling away down the hill, a white church,
    the river and the far bank, the sky. Real blocks, so the view shifts as the camera moves."""
    use("OUTSIDE")
    rng = random.Random(23)
    telha = roof_tiles()
    facades = [mat(f"fac{i}", c, 0.85) for i, c in enumerate(("#e9c46e", "#e3a59c", "#f0e8d8", "#9fbfd4", "#d9b48a",
                                                               "#c7d2b0", "#efe1c0"))]
    win_m = mat("lx_win_dark", "#2a2c33", 0.3, spec=0.6)
    lit = mat("lx_win_lit", "#2a2c33", 0.3, spec=0.6, emit="#ffc070", estr=0.0)   # dark glass by day, lit at night
    obs = []

    def block(x, y, z, w, d, h, roof=True, lit_p=0.42):
        fm = facades[rng.randrange(len(facades))]
        obs.append(boxmm(f"bld_{len(obs)}", (x - d, y - w / 2, z), (x, y + w / 2, z + h), fm, bev=0.01))
        if roof:
            rh = rng.uniform(0.12, 0.22)
            r = prism(f"roof_{len(obs)}", [(-d / 2 - 0.03, 0), (d / 2 + 0.03, 0), (0, rh)], w + 0.04,
                      loc=(x - d / 2, y + w / 2 + 0.02, z + h), rot=(90, 0, 0), m=telha, bev=0.004)
            obs.append(r)
            if rng.random() < 0.6:
                obs.append(boxmm(f"chim_{len(obs)}", (x - d * 0.6, y + w * 0.2, z + h), (x - d * 0.6 + 0.06,
                                                                                           y + w * 0.2 + 0.08,
                                                                                           z + h + rh + 0.08),
                                 fm, bev=0.006))
        for fy in np.arange(y - w / 2 + 0.07, y + w / 2 - 0.05, 0.13):   # windows facing the camera side (+x)
            for fz in np.arange(z + 0.12, z + h - 0.08, 0.2):
                m_ = lit if rng.random() < lit_p else win_m
                obs.append(boxmm(f"w_{len(obs)}", (x - 0.002, fy - 0.025, fz), (x + 0.004, fy + 0.025, fz + 0.09),
                                 m_, bev=0))
    # near roofs, just below the window (we are three floors up)
    for k in range(9):
        y = -0.6 + k * 0.55 + rng.uniform(-0.05, 0.05)
        block(-0.75 - rng.uniform(0, 0.15), y, -0.2, rng.uniform(0.45, 0.6), rng.uniform(0.6, 0.9),
              rng.uniform(0.9, 1.2))
    # further down the hill
    for k in range(12):
        y = -1.6 + k * 0.5 + rng.uniform(-0.1, 0.1)
        block(-2.0 - rng.uniform(0, 0.3), y, -0.3 + rng.uniform(0.0, 0.3), rng.uniform(0.35, 0.5),
              rng.uniform(0.5, 0.8), rng.uniform(1.1, 1.5))
    for k in range(16):
        y = -3.0 + k * 0.6 + rng.uniform(-0.1, 0.1)
        block(-3.6 - rng.uniform(0, 0.4), y, -0.4 + rng.uniform(0.0, 0.5), rng.uniform(0.4, 0.6),
              rng.uniform(0.5, 0.8), rng.uniform(1.0, 1.6), lit_p=0.5)
    # the white church with its two towers and dome
    ch = mat("lx_church", "#f1ede4", 0.7)
    cx, cy = -3.0, 2.4
    obs.append(boxmm("church_body", (cx - 0.7, cy - 0.45, 0.4), (cx, cy + 0.45, 1.75), ch, bev=0.01))
    for s in (-1, 1):
        obs.append(boxmm(f"church_tower{s}", (cx - 0.25, cy + s * 0.38 - 0.13, 0.4), (cx, cy + s * 0.38 + 0.13, 2.3),
                         ch, bev=0.01))
        obs.append(cyl(f"church_spire{s}", 0.1, 0.25, (cx - 0.12, cy + s * 0.38, 2.42), ch, r2=0.01, n=8))
    obs.append(sphere("church_dome", 0.3, (cx - 0.45, cy, 1.75), mat("lx_dome", "#c9cdd0", 0.5), seg=16, rings=8,
                      scale=(1, 1, 0.9)))
    # river, far bank, sky
    river = mat("lx_river", "#7d9db5", 0.15, spec=0.7)
    obs.append(boxmm("river", (-9.0, -6.0, 0.55), (-4.6, 8.0, 0.6), river, bev=0))
    hills = mat("lx_hills", "#a8a49a", 0.9)
    obs.append(prism("far_bank", [(-6, 0), (-2, 0.25), (1, 0.18), (4, 0.32), (8, 0.2), (8, 0), (-6, 0)][:-1], 0.1,
                     loc=(-8.8, 0, 0.6), rot=(90, 0, 90), m=hills))
    sky = mat("lx_sky", "#bcd6ea", 1.0, emit="#bcd6ea", estr=2.5)
    obs.append(boxmm("lx_sky", (-11.0, -8.0, -1.0), (-10.9, 10.0, 6.0), sky, bev=0))
    # the wide shot's own sky, placed where the walls hide it except through the window (used only in the wide)
    obs.append(boxmm("lx_sky_wide", (-1.72, 2.5, 0.4), (-1.7, 6.5, 2.88), sky, bev=0))
    for ob in obs:
        ob.visible_shadow = ob.name.startswith(("bld", "roof", "chim"))
    return lit, sky


# ================================================================ furniture and kit
def build_desk(M):
    use("SET")
    ply = birch_ply()
    boxmm("lx_desk_top", (DX0, DY0, DZ - 0.025), (DX1, DY1, DZ), ply, bev=0.004, seg=2)
    steel = mat("lx_steel_blk", "#202124", 0.45, metal=0.3)
    for x in (DX0 + 0.12, DX1 - 0.12):
        boxmm(f"lx_leg{x}", (x - 0.035, 2.18, 0.03), (x + 0.035, 2.26, DZ - 0.08), steel, bev=0.006)
        boxmm(f"lx_motor{x}", (x - 0.04, 2.17, DZ - 0.12), (x + 0.04, 2.27, DZ - 0.06), steel, bev=0.008)
        boxmm(f"lx_foot{x}", (x - 0.035, DY0 + 0.02, 0.0), (x + 0.035, DY1 - 0.02, 0.035), steel, bev=0.01)
        boxmm(f"lx_arm{x}", (x - 0.03, DY0 + 0.06, DZ - 0.055), (x + 0.03, DY1 - 0.06, DZ - 0.025), steel, bev=0.005)
    boxmm("lx_crossbar", (DX0 + 0.12, 2.2, DZ - 0.075), (DX1 - 0.12, 2.24, DZ - 0.04), steel, bev=0.005)
    kp = grp("lx_keypad", (DX1 - 0.2, DY0 + 0.03, DZ - 0.025))
    box("lx_keypad_body", (0.1, 0.05, 0.018), (0, 0, -0.009), steel, bev=0.004, parent=kp)
    box("lx_keypad_disp", (0.026, 0.002, 0.011), (-0.02, -0.0255, -0.009), mat("lx_disp", "#10131a", 0.3), bev=0,
        parent=kp)
    text("lx_keypad_num", "74", "consolab.ttf", 0.008, (-0.02, -0.027, -0.0095), mat("lx_led_red", "#ff5a3a", 0.4,
                                                                                     emit="#ff5a3a", estr=3.0),
         rot=(90, 0, 0), parent=kp)
    for k, x in enumerate((0.012, 0.03)):
        box(f"lx_keypad_btn{k}", (0.012, 0.004, 0.009), (x, -0.026, -0.009), M["plastic_blk"], bev=0.002, parent=kp)
    # grommet behind the monitors, and the cable tray under the top with a Schuko strip in it
    g = grp("lx_grommet", (1.42, DY1 - 0.07, DZ))
    torus("lx_grommet_ring", 0.028, 0.004, (0, 0, 0.001), M["plastic_blk"], nR=24, nr=6, parent=g)
    cyl("lx_grommet_hole", 0.025, 0.002, (0, 0, -0.0005), M["hole"], n=24, parent=g)
    wire = mat("lx_tray", "#2a2b2e", 0.5, metal=0.5)
    tx0, tx1, ty0, ty1, tz0, tz1 = 0.9, 1.9, DY1 - 0.2, DY1 - 0.03, DZ - 0.17, DZ - 0.06
    for k in range(11):
        x = tx0 + k * (tx1 - tx0) / 10
        curve(f"lx_tray_u{k}", [(x, ty0, tz1), (x, ty0, tz0), (x, ty1, tz0), (x, ty1, tz1)], 0.0025, wire, res=2, bres=1)
    for z in (tz0, tz1):
        for y in (ty0, ty1):
            tube(f"lx_tray_rail{z}{y}", (tx0, y, z), (tx1, y, z), 0.003, wire, n=6)
    strip = grp("lx_strip", (1.4, (ty0 + ty1) / 2, tz0 + 0.022))
    box("lx_strip_body", (0.42, 0.06, 0.04), (0, 0, 0), mat("lx_strip_w", "#efece4", 0.45), bev=0.008, parent=strip)
    for k in range(5):
        cyl(f"lx_strip_sock{k}", 0.019, 0.004, (-0.16 + k * 0.08, 0, 0.02), mat("lx_socket_in", "#dedad0", 0.5), n=16,
            parent=strip)
    return (tx0, tx1, ty0, ty1, tz0, tz1)


def laptop_stand(M, lp, alu, th, w, t):
    """A one-piece bent aluminium laptop stand (in the laptop group's space: y forward-to-back, z up): a platform
    sloping up toward the back, rolling over into a column that curves forward into a foot on the desk, silicone
    strips on the platform and a lip at its front edge. Returns the platform's top front edge (y, z) as a Vector."""
    F = Vector((-0.104, 0.062))                               # (y, z) of the platform's top front edge
    u, n = Vector((cos(th), sin(th))), Vector((-sin(th), cos(th)))
    c0 = F - n * t / 2
    line = [c0 + u * s for s in np.linspace(0.0, 0.19, 9)]
    R, R2 = 0.022, 0.012
    O = line[-1] - n * R                                      # roll over at the back
    a0 = math.atan2((line[-1] - O).y, (line[-1] - O).x)
    col_dir = radians(-100)
    a1 = a0 - (th - col_dir)
    line += [O + Vector((cos(a), sin(a))) * R for a in np.linspace(a0, a1, 12)[1:]]
    Pa = line[-1]
    d = Vector((cos(col_dir), sin(col_dir)))
    zb = t / 2 + R2 - R2 * sin(radians(10))                   # where the column meets the bottom bend
    Pb = Pa + d * ((Pa.y - zb) / -d.y)
    line += [Pa + (Pb - Pa) * f for f in np.linspace(0, 1, 5)[1:]]
    O2 = Pb + Vector((d.y, -d.x)) * R2                         # (the right of the column's direction: forward)
    b0 = math.atan2((Pb - O2).y, (Pb - O2).x)
    line += [O2 + Vector((cos(a), sin(a))) * R2 for a in np.linspace(b0, -pi / 2, 9)[1:]]
    foot_end = Vector((-0.05, t / 2))
    line += [line[-1] + (foot_end - line[-1]) * f for f in np.linspace(0, 1, 6)[1:]]
    left, right = [], []
    for i, p in enumerate(line):
        a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
        dd = (b - a).normalized()
        nn = Vector((-dd.y, dd.x))
        left.append(p + nn * t / 2)
        right.append(p - nn * t / 2)
    outline = [(p.x, p.y) for p in left + right[::-1]]
    prism("stand_sheet", outline, w, loc=(-w / 2, 0, 0), rot=(90, 0, 90), m=alu, bev=0.0012, parent=lp)
    sil = mat("lx_silicone", "#2a2b2e", 0.7)
    Fv = Vector((0, F.x, F.y))
    U, N = Vector((0, u.x, u.y)), Vector((0, n.x, n.y))
    lip = grp("stand_lip_g", Fv + U * 0.004 + N * 0.003, (math.degrees(th), 0, 0), parent=lp)
    box("stand_lip", (w - 0.02, 0.0055, 0.006), (0, 0, 0), sil, bev=0.002, parent=lip)
    for s in (-1, 1):
        g = grp(f"stand_pad_g{s}", Fv + U * 0.1 + N * 0.0006 + Vector((s * 0.085, 0, 0)), (math.degrees(th), 0, 0),
                parent=lp)
        box(f"stand_pad{s}", (0.014, 0.15, 0.0013), (0, 0, 0), sil, bev=0.0004, parent=g)
    return Fv


def build_arm_and_monitors(M):
    """Two 27in 16:9 monitors on a dual arm clamped to the back edge (main straight ahead, studio angled in), and the
    docked laptop on an aluminium riser to the left."""
    use("SET")
    steel = mat("lx_arm_alu", "#c7c9cc", 0.3, metal=0.9)
    blk = mat("lx_mon", "#151618", 0.42)
    bez = mat("lx_bezel", "#0c0c0d", 0.5)
    px, py = 1.42, DY1 - 0.045
    box("lx_clamp", (0.07, 0.09, 0.05), (px, py, DZ + 0.025), steel, bev=0.006)
    box("lx_clamp_jaw", (0.06, 0.05, 0.02), (px, py, DZ - 0.04), steel, bev=0.004)
    cyl("lx_clamp_screw", 0.006, 0.05, (px, py, DZ - 0.075), steel, n=10)
    cyl("lx_pole", 0.018, 0.5, (px, py, DZ + 0.05), steel, n=16, base=True)
    cyl("lx_pole_cap", 0.02, 0.012, (px, py, DZ + 0.55), steel, n=16, base=True, bev=0.003)
    aw, ah = 0.597, 0.336
    mons = {"main": ((1.07, 2.29, DZ + 0.34), 4.0), "studio": ((1.76, 2.22, DZ + 0.34), -26.0)}
    heads = {}
    for slot, (c, yaw) in mons.items():
        c = Vector(c)
        g = grp(f"mon_{slot}", c, (0, 0, yaw))
        head = grp(f"mon_{slot}_head", (0, 0, 0), (-3, 0, 0), parent=g)
        box(f"mon_{slot}_body", (aw + 0.016, 0.014, ah + 0.03), (0, 0.0, -0.006), blk, bev=0.004, parent=head)
        box(f"mon_{slot}_back", (0.42, 0.03, 0.24), (0, 0.02, -0.02), blk, bev=0.012, seg=3, parent=head)
        box(f"mon_{slot}_chin", (aw + 0.016, 0.0145, 0.018), (0, -0.0003, -ah / 2 - 0.014), bez, bev=0.003, parent=head)
        disc(f"mon_{slot}_led", 0, 0, 0.0012, 0, M["led_green"] if slot == "main" else M["led_amber"], head, n=8,
             loc=(aw / 2 - 0.012, -0.0076, -ah / 2 - 0.014), rot=(90, 0, 0))
        screen_plane(f"mon_{slot}_screen", aw, ah, panel_material(slot), head, (0, -0.0073, 0.002))
        box(f"mon_{slot}_vesa", (0.1, 0.012, 0.1), (0, 0.04, -0.02), steel, bev=0.004, parent=head)
        heads[slot] = head
        port(f"{slot}_dp", (-0.05, 0.03, -0.14), (0, 0.3, -1), head)
        port(f"{slot}_pwr", (0.06, 0.03, -0.14), (0, 0.3, -1), head)
    bpy.context.view_layer.update()
    # the arms: pole -> elbow -> VESA plate, one each side
    top = Vector((px, py, DZ + 0.4))
    for slot, head in heads.items():
        v = head.matrix_world @ Vector((0, 0.046, -0.02))
        el = (top + v) / 2 + Vector((0, 0.09, 0.0))
        for a, b, nm in ((top, el, "a"), (el, v, "b")):
            tube(f"arm_{slot}_{nm}", a, b, 0.016, steel, n=12)
            sphere(f"arm_{slot}_{nm}_j", 0.02, a, steel, seg=12, rings=8)
        cyl(f"arm_{slot}_collar", 0.026, 0.04, top, steel, n=16)
    # the docked laptop on its stand
    lp = grp("laptop", (0.62, 2.3, DZ), (0, 0, 8))
    alu = mat("lx_alu", "#b9bcc1", 0.28, metal=0.9)
    plat_th, w_st, t_st = radians(16), 0.24, 0.006
    F = laptop_stand(M, lp, alu, plat_th, w_st, t_st)
    u = Vector((0, cos(plat_th), sin(plat_th)))
    nrm = Vector((0, -sin(plat_th), cos(plat_th)))
    tilt = grp("laptop_tilt", F + u * (0.009 + 0.109) + nrm * 0.0013, (16, 0, 0), parent=lp)
    box("laptop_base", (0.312, 0.218, 0.014), (0, 0, 0.007), alu, bev=0.004, parent=tilt)
    box("laptop_well", (0.276, 0.104, 0.0006), (0, 0.035, 0.0139), mat("lx_keys", "#25272b", 0.5), bev=0,
        parent=tilt)
    kb = bmesh.new()                                          # the keys, a 6-row chiclet grid with a space bar
    for r in range(6):
        cols = [(c, 1.0) for c in range(14)] if r < 5 else [(0, 1.0), (1, 1.0), (2, 1.0), (3, 5.0), (8, 1.0),
                                                              (9, 1.0), (10, 1.0), (11, 1.0), (12, 1.0), (13, 1.0)]
        for c, wk in cols:
            x0 = -0.1309 + c * 0.0187 + 0.0012
            x1 = x0 + wk * 0.0187 - 0.0024 - (0.0 if wk == 1.0 else 0.0)
            y1 = 0.0835 - r * 0.0172
            y0 = y1 - (0.0148 if r else 0.009)
            vs = [kb.verts.new(p) for p in ((x0, y0, 0.0140), (x1, y0, 0.0140), (x1, y1, 0.0140), (x0, y1, 0.0140),
                                            (x0, y0, 0.0149), (x1, y0, 0.0149), (x1, y1, 0.0149), (x0, y1, 0.0149))]
            for idx in ((4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                kb.faces.new([vs[i] for i in idx])
    D.bevel(finish("laptop_keys", kb, mat("lx_keycap", "#1f2023", 0.42), tilt, angle=30), 0.0006, 1, 30)
    box("laptop_pad", (0.11, 0.07, 0.0006), (0, -0.065, 0.0142), mat("lx_pad", "#aeb1b6", 0.3, metal=0.7), bev=0,
        parent=tilt)
    lid = grp("laptop_lid", (0, 0.109, 0.014), (-118, 0, 0), parent=tilt)
    box("laptop_lid_shell", (0.312, 0.218, 0.006), (0, -0.109, 0.003), alu, bev=0.003, parent=lid)
    sg = grp("laptop_screen_g", (0, -0.109, -0.0002), (90, 0, 0), parent=lid)
    box("laptop_bezel", (0.306, 0.004, 0.21), (0, 0.0, 0.0), bez, bev=0.001, parent=sg)
    screen_plane("laptop_screen", 0.296, 0.185, panel_material("laptop"), sg, (0, -0.0024, 0.004))
    port("laptop_usbc", (-0.156, 0.03, 0.006), (-1, 0, 0), tilt)
    return heads


def build_dock_and_cables(M, tray):
    """Every lead ends somewhere: the laptop's USB-C to the dock; the keyboard (coiled) and the tablet into the dock;
    the dock and both monitors (DisplayPort and power, clipped along the arm) down through the grommet into the tray
    and its strip; the strip to the wall socket."""
    use("SET")
    blk = M["plastic_blk"]
    tx0, tx1, ty0, ty1, tz0, tz1 = tray
    dock = grp("dock", (0.84, DY1 - 0.09, DZ), (0, 0, 4))
    box("dock_body", (0.12, 0.05, 0.022), (0, 0, 0.011), mat("lx_dock", "#3a3c40", 0.35, metal=0.4), bev=0.005,
        parent=dock)
    disc("dock_led", -0.045, -0.0252, 0.0012, 0, M["led_blue"], dock, n=8, loc=(0, 0, 0.011), rot=(90, 0, 0))
    for nm, x in (("kb", -0.02), ("tab", 0.01), ("rx", 0.035)):
        box(f"dock_port_{nm}", (0.009, 0.002, 0.004), (x, -0.0252, 0.011), M["hole"], bev=0, parent=dock)
        port(f"dock_{nm}", (x, -0.027, 0.011), (0, -1, 0), dock)
    port("dock_in", (-0.061, 0.0, 0.011), (-1, 0, 0), dock)
    port("dock_out", (0.061, 0.0, 0.011), (1, 0, 0), dock)
    box("rx_dongle", (0.012, 0.006, 0.005), (0.035, -0.03, 0.011), blk, bev=0.001, parent=dock)
    gz = Vector((1.42, DY1 - 0.07, DZ))
    lane = DZ + 0.003

    def into_grommet(p_list, dx):
        return p_list + [gz + Vector((dx, 0.0, 0.004)), gz + Vector((dx, 0.0, -0.05)),
                         Vector((gz.x + dx, (ty0 + ty1) / 2, tz0 + 0.06)), Vector((1.4 + dx * 3, (ty0 + ty1) / 2,
                                                                                    tz0 + 0.05))]
    # laptop -> dock
    at, d = port_frame("laptop_usbc")
    st = connector("laptop_usbc_plug", "usb", at, d, M)
    at2, d2 = port_frame("dock_in")
    st2 = connector("dock_in_plug", "usb", at2, d2, M)
    D.cable("usbc_laptop", [st, st + d * 0.015, (0.45, 2.38, lane), (0.55, 2.46, lane), (0.7, 2.5, lane),
                            st2 + d2 * 0.02, st2], 0.0022, blk)
    # dock -> grommet -> tray
    at, d = port_frame("dock_out")
    st = connector("dock_out_plug", "usb", at, d, M)
    D.cable("dock_cable", into_grommet([st, st + d * 0.02, (1.0, DY1 - 0.07, lane), (1.25, DY1 - 0.06, lane)], -0.01),
            0.0028, blk)
    # monitors: DisplayPort and power down the back, along the arm, into the grommet
    for slot in ("main", "studio"):
        for kind, off in (("dp", -0.006), ("pwr", 0.006)):
            at, d = port_frame(f"{slot}_{kind}")
            st = connector(f"{slot}_{kind}_plug", "usb" if kind == "dp" else "iec", at, d, M)
            mid = Vector((1.42 + off, DY1 - 0.045 + 0.022, DZ + 0.35))
            D.cable(f"{slot}_{kind}_cable", into_grommet([st, st + d * 0.03, st + d * 0.06 + Vector((0, 0.04, 0)),
                                                          (st + mid) / 2 + Vector((0, 0.05, -0.05)), mid,
                                                          Vector((1.42 + off, DY1 - 0.022, DZ + 0.1))], off),
                    0.0026, blk)
    # strip lead down to the wall socket
    st = Vector((1.18, (ty0 + ty1) / 2, tz0 + 0.022))
    D.cable("lx_strip_lead", [st, st + Vector((-0.02, 0, 0)), (1.1, ty1, tz0 - 0.05), (1.3, LD - 0.04, 0.45),
                              (1.51, LD - 0.04, 0.34), (1.51, LD - 0.035, 0.3)], 0.0035, blk)
    cyl("lx_schuko_plug", 0.02, 0.035, (1.51, LD - 0.04, 0.3), mat("lx_plug_w", "#efece4", 0.4), rot=(90, 0, 0), n=16,
        bev=0.004)


def build_keyboard75(M):
    """Theo's mechanical keyboard: 75% layout, cream alphas, grey mods, an orange Esc and Enter, in an anodised case,
    with a coiled cable to the dock."""
    use("SET")
    g = grp("mech_kb", (1.07, 2.0, DZ), (5, 0, 2))
    case = mat("lx_case", "#8e9196", 0.3, metal=0.8)
    box("mk_case", (0.33, 0.125, 0.026), (0, 0, 0.013), case, bev=0.006, seg=2, parent=g)
    box("mk_plate", (0.314, 0.11, 0.003), (0, 0.0, 0.0255), mat("lx_plate", "#2a2b2e", 0.4), bev=0, parent=g)
    u = 0.0187
    cream, grey, orange = mat("mk_cream", "#ece4d2", 0.45), mat("mk_grey", "#8b8f96", 0.45), mat("mk_orange",
                                                                                                "#d9663a", 0.45)
    rows = [
        [("Esc", 1, "o")] + [(f"F{i}", 1, "g") for i in range(1, 13)] + [("Del", 1, "g"), ("Ins", 1, "g")],
        [(c, 1, "c") for c in "`1234567890-="] + [("Bksp", 2, "g"), ("Home", 1, "g")],
        [("Tab", 1.5, "g")] + [(c, 1, "c") for c in "QWERTYUIOP[]"] + [("\\", 1.5, "g"), ("PgUp", 1, "g")],
        [("Caps", 1.75, "g")] + [(c, 1, "c") for c in "ASDFGHJKL;'"] + [("Enter", 2.25, "o"), ("PgDn", 1, "g")],
        [("Shift", 2.25, "g")] + [(c, 1, "c") for c in "ZXCVBNM,./"] + [("Shift", 1.75, "g"), ("Up", 1, "g"),
                                                                       ("End", 1, "g")],
        [("Ctrl", 1.25, "g"), ("Super", 1.25, "g"), ("Alt", 1.25, "g"), ("", 6.25, "c"), ("Alt", 1, "g"),
         ("Fn", 1, "g"), ("Ctrl", 1, "g"), ("Left", 1, "g"), ("Down", 1, "g"), ("Right", 1, "g")],
    ]
    mats = {"c": cream, "g": grey, "o": orange}
    bm_by = {k: bmesh.new() for k in mats}
    x0, y0 = -16 * u / 2, 0.05
    legs = []
    for r, row in enumerate(rows):
        x = x0
        y = y0 - r * u - (0.004 if r else 0.0)
        zb, zt = 0.027, 0.039 + 0.002 * (abs(r - 3))          # sculpted rows
        for lab, wu, c in row:
            w2, h2 = wu * u / 2 - 0.0008, u / 2 - 0.0008
            cx = x + wu * u / 2
            bm = bm_by[c]
            ins = 0.0024
            vs = [bm.verts.new(p) for p in ((cx - w2, y - h2, zb), (cx + w2, y - h2, zb), (cx + w2, y + h2, zb),
                                            (cx - w2, y + h2, zb), (cx - w2 + ins, y - h2 + ins, zt),
                                            (cx + w2 - ins, y - h2 + ins, zt), (cx + w2 - ins, y + h2 - ins, zt),
                                            (cx - w2 + ins, y + h2 - ins, zt))]
            for idx in ((4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                bm.faces.new([vs[i] for i in idx])
            if lab:
                legs.append((lab, cx, y, zt, c))
            x += wu * u
    for c, bm in bm_by.items():
        ob = finish(f"mk_caps_{c}", bm, mats[c], g, angle=30)
        D.bevel(ob, 0.0012, 1, 30)
    ink = mat("mk_ink", "#3a3632", 0.5)
    arrows = {"Up": "↑", "Down": "↓", "Left": "←", "Right": "→"}
    for i, (lab, cx, y, zt, c) in enumerate(legs):
        t = arrows.get(lab, lab)
        f = "tahoma.ttf" if lab in arrows else "verdana.ttf"
        sz = 0.0046 if len(t) == 1 else (0.0026 if len(t) <= 3 else 0.0021)
        text(f"mk_leg{i}", t, f, sz, (cx, y, zt + 0.0002), mat("mk_ink_w", "#f4efe4", 0.5) if c == "o" else ink,
             parent=g)
    port("mk_cable", (0.11, 0.064, 0.016), (0, 1, 0.2), g)
    return g


LX_MOUSE_OUTLINE = [(0.0, 0.064), (-0.012, 0.0625), (-0.022, 0.057), (-0.028, 0.047), (-0.031, 0.036),
                    (-0.036, 0.026), (-0.045, 0.016), (-0.053, 0.004), (-0.056, -0.01), (-0.053, -0.024),
                    (-0.044, -0.036), (-0.034, -0.048), (-0.022, -0.061), (-0.006, -0.067), (0.01, -0.065),
                    (0.022, -0.057), (0.029, -0.042), (0.032, -0.022), (0.033, 0.0), (0.032, 0.022), (0.029, 0.04),
                    (0.023, 0.053), (0.013, 0.061)]


def _lx_mouse_top(x, y):
    hy = D._spline(y, [-0.068, -0.054, -0.036, -0.016, 0.004, 0.024, 0.044, 0.065], [0.3, 0.6, 0.88, 1.0, 0.94, 0.78,
                                                                                    0.6, 0.44])
    qx = D._spline(x, [-0.058, -0.048, -0.038, -0.028, -0.014, 0.0, 0.016, 0.028, 0.036], [0.26, 0.28, 0.36, 0.62, 0.9,
                                                                                          1.0, 0.86, 0.6, 0.4])
    z = 0.046 * hy * qx
    return z - 0.006 * math.exp(-((x + 0.035) / 0.008) ** 2) * math.exp(-((y + 0.004) / 0.026) ** 2)


def lx_mouse_material():
    """Soft-touch graphite: the buttons a shade smoother than the palm, the thumb wing a slightly paler rubber."""
    if "lx_mouse_m" in MATS:
        return MATS["lx_mouse_m"]
    m = mat("lx_mouse_m", "#3a3c41", 0.55)
    nt, b = m.node_tree, principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    x, y, z = D._xyz(nt, tc.outputs["Object"])
    yb = D._math(nt, "ADD", 0.012, D._math(nt, "MULTIPLY", D._math(nt, "MULTIPLY", x, x), 6.0))
    btn = D._ramp(nt, D._math(nt, "SUBTRACT", y, yb), -0.0004, 0.0004)
    wing = D._math(nt, "MULTIPLY", D._ramp(nt, x, -0.034, -0.04), D._ramp(nt, z, 0.021, 0.016))
    col = D._mixc(nt, btn, "#3a3c41", "#33353a")
    col = D._mixc(nt, wing, col, "#46484d")
    r = D._lerp(nt, btn, 0.56, 0.42)
    r = D._lerp(nt, wing, r, 0.74)
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(r, b.inputs["Roughness"])
    return m


def build_modern_mouse(M, loc, yaw):
    """Theo's studio mouse (2026): a sculpted ergonomic wireless mouse, soft-touch graphite, the high back falling to
    the right, a broad low thumb wing with a scoop, a knurled steel scroll wheel in its well, a thumb wheel and two
    buttons on the side, the button seams, a USB-C charging port at the front. Wireless: the receiver is in the dock."""
    g = grp("lx_mouse", loc, (0, 0, yaw))
    sh = D.Shell(LX_MOUSE_OUTLINE, (-0.006, -0.004), _lx_mouse_top, lift=0.0012)
    sh.mesh("lx_mouse_body", lx_mouse_material(), g)
    seam = mat("lx_mouse_seam", "#1b1c1f", 0.6)
    wx, wy0, wy1 = -0.001, 0.016, 0.046
    yb = lambda x: 0.012 + 6.0 * x * x                                       # noqa: E731
    sh.line("lx_mouse_seam_split", [(wx, 0.064), (wx, wy1 + 0.001)], 0.00032, seam, g)
    sh.line("lx_mouse_seam_back", [(x, yb(x)) for x in np.linspace(-0.029, 0.031, 22)], 0.00032, seam, g)
    well = [(wx + 0.0068 * cos(a), (wy0 + wy1) / 2 + 0.0162 * sin(a)) for a in np.linspace(0, 2 * pi, 22,
                                                                                            endpoint=False)]
    sh.patch("lx_mouse_well", well, M["hole"], g)
    wz = sh.z(wx, 0.031)
    knurl = mat("lx_wheel_steel", "#a3a7ad", 0.3, metal=0.9)
    D.toothed_wheel("lx_mouse_wheel", 0.0088, 0.0072, 44, 0.0003, knurl, g, (wx, 0.031, wz - 0.0046))
    # the thumb wheel, set into the side above the wing, and the two side buttons behind it
    tx, ty = -0.0312, 0.016
    n = sh.normal(tx, ty)
    tg = D.framed("lx_mouse_thumb_g", D.frame_matrix(sh.at(tx, ty, -0.0042), n, (0, 0, 1)), parent=g)
    D.toothed_wheel("lx_mouse_thumbwheel", 0.0078, 0.0042, 26, 0.00035, mat("lx_thumbwheel", "#2a2c30", 0.5), tg,
                    (0, 0, 0), rot=(0, 0, 0))
    side = mat("lx_mouse_side", "#34363b", 0.45)
    sh.raised("lx_mouse_side_fwd", -0.0333, -0.0035, 0.0135, 0.0042, 0.0011, side, g, along=(0.25, 1.0))
    sh.raised("lx_mouse_side_back", -0.0349, -0.0185, 0.0135, 0.0042, 0.0011, side, g, along=(0.3, 1.0))
    box("lx_mouse_usbc", (0.0088, 0.003, 0.0031), (0.0, 0.0632, 0.0086), M["hole"], bev=0.0012, parent=g)
    return g


def build_desk_kit(M):
    """Mouse, drawing tablet and pen, headphones on their stand, the plant and the photo (the same props as the shop),
    the studio badge on its lanyard, a pastel de nata on a napkin and a bica."""
    use("SET")
    build_modern_mouse(M, (1.42, 2.012, DZ), -10)
    # drawing tablet and pen
    tb = grp("tablet", (1.69, 2.03, DZ), (0, 0, -6))
    tab_m = mat("lx_tablet", "#1a1b1e", 0.55)
    box("tablet_body", (0.35, 0.225, 0.009), (0, 0, 0.0045), tab_m, bev=0.004, parent=tb)
    box("tablet_area", (0.27, 0.17, 0.0005), (0.03, 0.0, 0.0092), mat("lx_tablet_area", "#202125", 0.75), bev=0,
        parent=tb)
    for cx_, cy_ in ((-0.105, 0.085), (0.165, 0.085), (-0.105, -0.085), (0.165, -0.085)):
        box(f"tablet_corner{cx_}{cy_}", (0.008, 0.008, 0.0004), (cx_, cy_, 0.0094), mat("lx_tab_mark", "#5a5d63", 0.5),
            bev=0, parent=tb)
    for k in range(4):
        box(f"tablet_key{k}", (0.026, 0.016, 0.002), (-0.15, 0.06 - k * 0.04, 0.0095), mat("lx_tab_key", "#2b2c30", 0.4),
            bev=0.002, parent=tb)
    disc("tablet_led", 0, 0, 0.0018, 0.0094, M["led_blue"], tb, n=8, loc=(-0.15, -0.1, 0))
    port("tablet_usb", (-0.175, 0.09, 0.0045), (-1, 0.2, 0), tb)
    pen = grp("tablet_pen", (0.02, -0.02, 0.0155), (0, 90, 28), parent=tb)
    cyl("pen_body", 0.0055, 0.15, (0, 0, 0), mat("lx_pen", "#2d2e32", 0.35), n=14, parent=pen)
    cyl("pen_grip", 0.006, 0.04, (0, 0, -0.05), M["rubber"], n=14, parent=pen)
    cyl("pen_cone", 0.0055, 0.012, (0, 0, -0.081), mat("lx_pen", "#2d2e32", 0.35), r2=0.0015, n=12, parent=pen)
    cyl("pen_nib", 0.0008, 0.004, (0, 0, -0.089), mat("lx_nib", "#d9d9d6", 0.5), n=6, parent=pen)
    box("pen_switch", (0.004, 0.003, 0.012), (0.0, 0.0055, -0.025), mat("lx_pen_sw", "#4a4c52", 0.4), bev=0.001,
        parent=pen)
    # headphones on a walnut stand, their lead wound round the stem, the jack resting on the base
    walnut = D.wood("walnut", "#5a3a26", "#3f281a", 0.38, grain=9.0, coat=0.4)
    hs = grp("hp_stand", (1.96, 2.44, DZ))
    cyl("hps_base", 0.06, 0.012, (0, 0, 0), walnut, n=24, base=True, bev=0.003, parent=hs)
    cyl("hps_stem", 0.011, 0.25, (0, 0, 0.012), walnut, n=12, base=True, parent=hs)
    torus("hps_cradle", 0.05, 0.012, (0, 0, 0.262), walnut, rot=(90, 0, 0), nR=16, nr=8, arc=(0, 180), parent=hs)
    hp = grp("headphones", (0, 0, 0), parent=hs)
    crown = D.build_headphones(M, hp, name="lhp", pose="stand")
    hp.location.z = 0.262 + 0.05 + 0.012 - crown               # the band's cushion rests on the cradle
    bpy.context.view_layer.update()
    # the lead: out of the left cup, down and round the stem a few turns, the jack resting on the base
    at, dl = port_frame("lhp_lead")
    p0 = connector("lhp_lead_bush", "relief", at, dl, M)
    inv = hs.matrix_world.inverted()
    q0 = inv @ p0
    spiral = [(0.0175 * cos(t), 0.0175 * sin(t), 0.075 - 0.04 * (t - pi) / (4 * pi)) for t in np.linspace(pi, 5 * pi,
                                                                                                         40)]
    pts = [q0, q0 + Vector((0, 0, -0.012)), q0 + Vector((0.012, -0.004, -0.03)), Vector((-0.03, -0.006, 0.08))]
    pts += [Vector(p) for p in spiral] + [Vector((0.026, -0.02, 0.03)), Vector((0.04, -0.03, 0.017)),
                                          Vector((0.046, -0.034, 0.0156))]
    curve("hps_lead", [tuple(p) for p in pts], 0.0016, M["plastic_blk"], parent=hs, res=4)
    cyl("hps_jack", 0.0035, 0.02, (0.056, -0.04, 0.0156), mat("jack_green", "#5aa55a", 0.45), rot=(0, 90, 32), n=10,
        parent=hs)
    # the plant (survived the flight) by the window, the 2009 photo by the monitors
    D.build_plant(M, grp("plant", (-0.14, 2.12, WIN[2])))     # on the sunny marble sill
    D.build_photo_frame(M, (1.95, 2.17, DZ), -32)
    # studio badge on its lanyard
    bg = grp("badge", (1.33, 1.93, DZ + 0.001), (0, 0, 18))
    box("badge_sleeve", (0.06, 0.092, 0.0012), (0, 0, 0.0006), mat("lx_sleeve", "#e9eef0", 0.1, spec=0.6, alpha=0.25),
        bev=0.002, parent=bg)
    box("badge_card", (0.054, 0.086, 0.0008), (0, 0, 0.0004), M["pin_white"], bev=0.0015, parent=bg)
    teal = mat("lx_teal", "#1f6f6a", 0.5)
    box("badge_band", (0.054, 0.022, 0.0002), (0, 0.032, 0.0009), teal, bev=0, parent=bg)
    sw = [(0.0, 0.0), (0.012, 0.004), (0.022, 0.012), (0.016, 0.004), (0.026, 0.002), (0.012, -0.002), (0.004, -0.008),
          (0.0, -0.016), (-0.004, -0.008), (-0.012, -0.002), (-0.026, 0.002), (-0.016, 0.004), (-0.022, 0.012),
          (-0.012, 0.004)]
    flat("badge_swallow", [(x * 0.42 - 0.018, y * 0.42 + 0.033) for x, y in sw], 0.001, M["pin_white"], bg)
    rect("badge_photo", -0.022, -0.012, -0.004, 0.012, 0.0009, mat("lx_photo_bg", "#c9d3d8", 0.6), bg)
    disc("badge_face", -0.013, 0.003, 0.004, 0.00095, mat("ph_skin_t", "#e3b28f", 0.55), bg, n=12)
    rect("badge_shoulders", -0.02, -0.012, -0.006, -0.003, 0.00095, mat("lx_jumper", "#5a6a7a", 0.6), bg)
    for k, (t, f, sz, x, y, ax) in enumerate((("ANDORINHA", "verdanab.ttf", 0.0036, 0.007, 0.033, "CENTER"),
                                              ("Theo Hartley", "verdanab.ttf", 0.0032, -0.001, 0.005, "LEFT"),
                                              ("Pipeline", "verdana.ttf", 0.0029, -0.001, -0.002, "LEFT"),
                                              ("DESK 14", "consolab.ttf", 0.0036, 0.0, -0.03, "CENTER"))):
        text(f"badge_t{k}", t, f, sz, (x, y, 0.001), M["ink"] if k else M["pin_white"], ax=ax, parent=bg,
             fit=0.046 if k == 0 else 0.026)
    clip = box("badge_clip", (0.012, 0.012, 0.003), (0, 0.05, 0.0015), M["chrome"], bev=0.001, parent=bg)
    lg = grp("lanyard_g", (0, 0, DZ + 0.0015))
    curve("lanyard", [(1.312, 1.976, 0), (1.288, 2.03, 0), (1.248, 2.1, 0), (1.268, 2.166, 0), (1.322, 2.172, 0),
                      (1.345, 2.115, 0), (1.333, 2.045, 0), (1.322, 1.99, 0)], 0.0055, teal, parent=lg, res=8, bres=1,
          flatz=0.18)
    # pastel de nata on a napkin, and a bica
    build_nata(M, (0.8, 1.99, DZ), 15)
    cup = grp("bica", (0.66, 2.1, DZ))
    lathe("bica_saucer", [(0.0, 0.0), (0.05, 0.0), (0.056, 0.008), (0.052, 0.009), (0.03, 0.004), (0.0, 0.004)], n=28,
          m=M["ceramic"], parent=cup)
    lathe("bica_cup", [(0.0, 0.004), (0.02, 0.004), (0.026, 0.012), (0.029, 0.045), (0.027, 0.046), (0.024, 0.014),
                       (0.0, 0.012)], n=24, m=M["ceramic"], parent=cup)
    cyl("bica_crema", 0.024, 0.001, (0, 0, 0.032), mat("crema", "#a8784a", 0.2), n=24, parent=cup)
    torus("bica_handle", 0.011, 0.0035, (0.033, 0, 0.03), M["ceramic"], rot=(90, 0, 0), nR=12, nr=6, arc=(-80, 80),
          parent=cup)
    tube("bica_spoon", (0.02, -0.035, 0.009), (-0.03, -0.042, 0.007), 0.0016, M["steel"], n=6, parent=cup)
    sphere("bica_spoon_bowl", 0.006, (0.026, -0.034, 0.009), M["steel"], seg=10, rings=6, parent=cup,
           scale=(1.4, 1, 0.35))
    sphere("sugar", 0.009, (-0.04, 0.02, 0.006), mat("sugar_pkt", "#f4efe1", 0.7), seg=8, rings=4, parent=cup,
           scale=(2.2, 0.9, 0.35))


def build_nata(M, loc, yaw):
    """A pastel de nata on a pastelaria napkin: a fluted puff-pastry cup whose layers show on the wall and flake at the
    browned rim, and a glossy egg custard with its blistered, caramelised, nearly black spots, a little cinnamon."""
    g = grp("nata", loc, (0, 0, yaw))
    nap = mat("napkin", "#f7f4ec", 0.85)
    box("napkin", (0.15, 0.15, 0.0008), (0, 0, 0.0004), nap, rot=(0, 0, 12), bev=0, parent=g)
    for k in range(2):
        rect(f"napkin_line{k}", -0.07, -0.066 + k * 0.004, 0.07, -0.0648 + k * 0.004, 0.0009,
             mat("napkin_blue", "#2f5fa8", 0.6), g).rotation_euler = (0, 0, radians(12))
    # pastry: golden at the foot, browner up the wall, dark at the rim; layer ridges every 2.4 mm
    pastry = mat("nata_pastry", "#c4873a", 0.62)
    nt, b = pastry.node_tree, principled(pastry)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    rz = nt.nodes.new("ShaderNodeMapRange")
    rz.inputs["From Min"].default_value = 0.004
    rz.inputs["From Max"].default_value = 0.026
    nt.links.new(sep.outputs["Z"], rz.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    shade = nt.nodes.new("ShaderNodeMath")
    shade.operation = "MULTIPLY_ADD"
    nt.links.new(rz.outputs["Result"], shade.inputs[0])
    shade.inputs[1].default_value = 0.8
    nt.links.new(nz.outputs["Fac"], shade.inputs[2])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.35, rgba("#e0aa48")
    els[1].position, els[1].color = 1.15 / 1.3, rgba("#7a4410")
    mid = els.new(0.62)
    mid.color = rgba("#c08024")
    sc_ = nt.nodes.new("ShaderNodeMath")
    sc_.operation = "MULTIPLY"
    nt.links.new(shade.outputs[0], sc_.inputs[0])
    sc_.inputs[1].default_value = 1 / 1.3
    nt.links.new(sc_.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 1.0 / 0.0024
    wave.inputs["Distortion"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    _bump(nt, b, wave.outputs["Fac"], 0.5, 0.0006)
    n = 42
    prof = [(0.025, 0.0), (0.028, 0.004), (0.031, 0.009), (0.0335, 0.015), (0.0355, 0.02), (0.0368, 0.0235),
            (0.0372, 0.0255), (0.0355, 0.0262), (0.0338, 0.0238)]
    bm = bmesh.new()
    grid = []
    for r, z in prof:
        row = []
        for i in range(n):
            t = 2 * pi * i / n
            rr = r + 0.0022 * cos(14 * t) + 0.0006 * sin(z * 2 * pi / 0.0024)   # flutes and layer ridges
            row.append(bm.verts.new((rr * cos(t), rr * sin(t), z + 0.001)))
        grid.append(row)
    for a_, b_ in zip(grid, grid[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a_[i], a_[j], b_[j], b_[i]))
    c0 = bm.verts.new((0, 0, 0.001))
    for i in range(n):
        bm.faces.new((grid[0][(i + 1) % n], grid[0][i], c0))
    finish("nata_shell", bm, pastry, g, angle=60)
    rng = random.Random(5)
    flake = mat("nata_flake", "#8f5418", 0.6)
    for k in range(4):                                       # the flaky, browned lip: loose rings of pastry
        torus(f"nata_flake_ring{k}", 0.0352 + rng.uniform(-0.0008, 0.0012), 0.0013 + 0.0004 * k,
              (rng.uniform(-0.0006, 0.0006), rng.uniform(-0.0006, 0.0006), 0.0262 + 0.0005 * k), flake,
              rot=(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(0, 90)), nR=40, nr=5, parent=g)
    # custard: glossy egg yellow, blistered to caramel and almost black in patches
    custard = mat("nata_custard", "#e8a81a", 0.22, spec=0.5)
    nt, b = custard.node_tree, principled(custard)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 55.0
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.4, rgba("#e8ac1c")
    els[1].position, els[1].color = 0.62, rgba("#1a0c05")
    for pos, c in ((0.47, "#c97d1c"), (0.52, "#7a3a0e"), (0.56, "#3a1806")):
        e = els.new(pos)
        e.color = rgba(c)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = 0.46
    rough.inputs["From Max"].default_value = 0.58
    rough.inputs["To Min"].default_value = 0.2
    rough.inputs["To Max"].default_value = 0.6
    nt.links.new(nz.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    _bump(nt, b, nz.outputs["Fac"], 0.55, 0.0012)
    lathe("nata_custard", [(0.0, 0.0258), (0.012, 0.0256), (0.024, 0.0249), (0.0322, 0.0238), (0.0338, 0.0228),
                           (0.0338, 0.02), (0.0, 0.02)], n=40, m=custard, parent=g)
    for k in range(34):                                       # a dusting of cinnamon, heavier in the middle
        a, r = rng.uniform(0, 2 * pi), 0.022 * rng.random() ** 1.6
        disc(f"cinn{k}", r * cos(a), r * sin(a), rng.uniform(0.0004, 0.0008), 0.0262, mat("cinnamon", "#5a2e14", 0.8),
             g, n=5)
    for k in range(6):                                        # a few flakes on the napkin
        sphere(f"flake{k}", rng.uniform(0.0012, 0.0022), (rng.uniform(0.04, 0.065), rng.uniform(-0.035, 0.02), 0.0012),
               flake, seg=6, rings=4, parent=g, scale=(1.6, 1.0, 0.35))


def build_chair(M):
    """A modern task chair, mesh back, pulled out from the desk."""
    use("SET")
    g = grp("lx_chair", (0.95, 1.22, 0), (0, 0, -24))
    blk = mat("lx_chair_blk", "#232427", 0.5)
    for i in range(5):
        a = 2 * pi * i / 5 + 0.3
        tube(f"lxc_leg{i}", (0, 0, 0.1), (0.32 * cos(a), 0.32 * sin(a), 0.06), 0.016, blk, parent=g)
        sphere(f"lxc_caster{i}", 0.027, (0.32 * cos(a), 0.32 * sin(a), 0.03), blk, seg=10, rings=6, scale=(0.7, 1, 1),
               parent=g)
    cyl("lxc_lift", 0.022, 0.32, (0, 0, 0.27), M["chrome"], n=12, parent=g)
    box("lxc_seat", (0.5, 0.48, 0.07), (0, 0.02, 0.48), mat("lx_seat", "#3d4752", 0.9), bev=0.03, seg=3, parent=g)
    box("lxc_spine", (0.06, 0.03, 0.4), (0, -0.25, 0.66), blk, rot=(-10, 0, 0), bev=0.008, parent=g)
    box("lxc_frame", (0.46, 0.04, 0.58), (0, -0.29, 0.95), blk, rot=(-12, 0, 0), bev=0.03, seg=3, parent=g)
    box("lxc_mesh", (0.42, 0.045, 0.53), (0, -0.287, 0.95), mat("lx_mesh", "#3a3f46", 0.95), rot=(-12, 0, 0),
        bev=0.02, parent=g)
    for s in (-1, 1):
        box(f"lxc_armpost{s}", (0.03, 0.04, 0.2), (s * 0.25, 0.0, 0.59), blk, bev=0.006, parent=g)
        box(f"lxc_armpad{s}", (0.07, 0.25, 0.028), (s * 0.25, 0.02, 0.7), blk, bev=0.012, parent=g)


def build_studio_corner(M):
    """The right of the room: a low bookcase of art books with the pigeon's clay maquette on it, the film's poster
    over it, a big monstera in a basket, an Arraiolos-style rug under the chair."""
    use("SET")
    oak = D.wood("lx_oak_case", "#b98f62", "#a37b52", 0.45, grain=7.0)
    x0, x1, y0, y1, h = 2.2, 3.08, LD - 0.34, LD - 0.01, 0.86
    boxmm("case_top", (x0, y0, h - 0.025), (x1, y1, h), oak, bev=0.004)
    boxmm("case_bot", (x0, y0, 0.06), (x1, y1, 0.085), oak, bev=0.004)
    boxmm("case_back", (x0, y1 - 0.012, 0.06), (x1, y1, h), oak, bev=0)
    for x in (x0, (x0 + x1) / 2 - 0.0125, x1 - 0.025):
        boxmm(f"case_side{x}", (x, y0, 0.0), (x + 0.025, y1, h), oak, bev=0.004)
    boxmm("case_shelf", (x0, y0, 0.45), (x1, y1, 0.47), oak, bev=0.003)
    rng = random.Random(27)
    cols = ["#b3392c", "#2f4d6b", "#e0b53a", "#3d5c3a", "#d9d2c3", "#262626", "#c95b36", "#6b4c8f", "#8a6a4e"]
    for zb, zt in ((0.085, 0.45), (0.47, h - 0.025)):
        for (a, b) in ((x0 + 0.03, (x0 + x1) / 2 - 0.015), ((x0 + x1) / 2 + 0.015, x1 - 0.03)):
            x = a
            while x < b - 0.03:
                w = rng.uniform(0.018, 0.045)
                hh = min(zt - zb - 0.01, rng.uniform(0.2, 0.33))
                if rng.random() < 0.1:
                    x += 0.03
                    continue
                book = boxmm(f"book{len(bpy.data.objects)}", (x, y0 + 0.03, zb), (x + w, y0 + rng.uniform(0.2, 0.26),
                                                                                  zb + hh),
                             mat("bk_" + cols[rng.randrange(len(cols))], cols[rng.randrange(len(cols))], 0.6),
                             bev=0.002)
                book.rotation_euler = (0, radians(rng.uniform(-2, 2)), 0)
                x += w + 0.002
    for k in range(3):                                        # big art books lying flat on top
        boxmm(f"artbook{k}", (x0 + 0.06 + k * 0.006, y0 + 0.05, h + k * 0.028),
              (x0 + 0.36 - k * 0.012, y0 + 0.3 - k * 0.01, h + 0.026 + k * 0.028),
              mat(f"artbook{k}", ("#1d1e20", "#e9e2d0", "#2f5fa8")[k], 0.5), bev=0.003)
    # the pigeon maquette, sculpted clay on a turned base
    mq = grp("maquette", (2.78, LD - 0.17, h))
    lathe("mq_base", [(0.0, 0.0), (0.06, 0.0), (0.062, 0.012), (0.055, 0.02), (0.0, 0.02)], n=24, m=M["oak"], parent=mq)
    clay = mat("clay", "#9ea3a8", 0.75)
    sphere("mq_body", 0.07, (0, 0, 0.085), clay, seg=18, rings=12, parent=mq, scale=(0.75, 1.15, 0.85))
    sphere("mq_head", 0.036, (0, -0.07, 0.15), clay, seg=14, rings=10, parent=mq)
    sphere("mq_neck", 0.04, (0, -0.045, 0.12), mat("clay_neck", "#7f8a86", 0.7), seg=14, rings=10, parent=mq,
           scale=(0.9, 0.9, 1.0))
    cyl("mq_beak", 0.008, 0.026, (0, -0.108, 0.148), mat("clay_beak", "#d6a35a", 0.6), r2=0.002, rot=(-95, 0, 0), n=8,
        parent=mq)
    for s in (-1, 1):
        sphere(f"mq_eye{s}", 0.006, (s * 0.022, -0.09, 0.158), mat("clay_eye", "#e88a2a", 0.3), seg=8, rings=6,
               parent=mq)
        tube(f"mq_leg{s}", (s * 0.02, -0.01, 0.03), (s * 0.02, -0.015, 0.02), 0.005, mat("clay_feet", "#d98a8a", 0.6),
             n=6, parent=mq)
    sphere("mq_tail", 0.03, (0, 0.085, 0.09), clay, seg=10, rings=6, parent=mq, scale=(0.9, 1.4, 0.4))
    # the film's poster
    pg = grp("poster", (2.64, LD - 0.016, 1.3), (90, 0, 0))
    frame = mat("poster_frame", "#1d1e20", 0.4)
    pw, ph = 0.6, 0.84
    for nm, a, b in (("t", (-pw / 2, ph - 0.02), (pw / 2, ph)), ("b", (-pw / 2, 0), (pw / 2, 0.02)),
                     ("l", (-pw / 2, 0), (-pw / 2 + 0.02, ph)), ("r", (pw / 2 - 0.02, 0), (pw / 2, ph))):
        box(f"poster_fr_{nm}", (b[0] - a[0], b[1] - a[1], 0.02), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.01), frame,
            bev=0.003, parent=pg)
    rect("poster_bg", -pw / 2 + 0.02, 0.02, pw / 2 - 0.02, ph - 0.02, 0.004, mat("poster_sky", "#a9c8dd", 0.8), pg)
    flat("poster_roofs", [(-0.28, 0.02), (-0.28, 0.2), (-0.2, 0.26), (-0.12, 0.2), (-0.12, 0.28), (-0.02, 0.34),
                          (0.06, 0.26), (0.06, 0.3), (0.16, 0.36), (0.28, 0.27), (0.28, 0.02)], 0.005,
         mat("poster_roof", "#c2603e", 0.8), pg)
    sw = [(0.0, 0.0), (0.06, 0.05), (0.13, 0.06), (0.08, 0.02), (0.12, -0.01), (0.05, -0.02), (0.02, -0.06),
          (-0.01, -0.02), (-0.06, -0.04), (-0.03, 0.0), (-0.06, 0.03), (-0.02, 0.02)]
    flat("poster_bird", [(x * 1.3 + 0.0, y * 1.3 + 0.52) for x, y in sw], 0.006, mat("poster_bird", "#2f3a48", 0.7), pg)
    text("poster_title", "POMBO", "georgiab.ttf", 0.085, (0, 0.7, 0.006), mat("poster_ink", "#f6f1e4", 0.6), parent=pg)
    text("poster_credit", "ANDORINHA ANIMAÇÃO  ·  2027", "verdana.ttf", 0.014, (0, 0.06, 0.006), M["pin_white"],
         parent=pg, fit=0.5)
    # a big monstera in a woven basket, front right
    pl = grp("monstera", (2.95, 1.0, 0))
    lathe("basket", [(0.0, 0.0), (0.16, 0.0), (0.19, 0.34), (0.2, 0.36), (0.18, 0.36), (0.0, 0.3)], n=24,
          m=D.noisy("seagrass", "#b9a16f", "#8f7a4f", 0.9, scale=90.0, bump=0.4), parent=pl)
    leaf_m = [mat("monstera_a", "#3f6b38", 0.55), mat("monstera_b", "#355c30", 0.55)]
    for k in range(9):
        a = 2 * pi * k / 9 + rng.uniform(-0.2, 0.2)
        L = rng.uniform(0.5, 0.95)
        tip = Vector((cos(a) * L * 0.45, sin(a) * L * 0.45, 0.36 + L))
        tube(f"monstera_stem{k}", (0, 0, 0.32), tip, 0.006, mat("monstera_stem", "#5f7f45", 0.6), n=6, parent=pl)
        lf = grp(f"monstera_leaf{k}", tip, (rng.uniform(-50, -20), 0, math.degrees(a) - 90), parent=pl)
        sz = rng.uniform(0.18, 0.28)
        pts = [(sz * 0.5 * sin(t) * (1.0 if abs(sin(3 * t)) > 0.25 else 0.78), sz * (0.5 - 0.5 * cos(t)))
               for t in np.linspace(0, 2 * pi, 28, endpoint=False)]
        f_ = flat(f"monstera_blade{k}", pts, 0, leaf_m[k % 2], lf)
        sd = f_.modifiers.new("Solid", "SOLIDIFY")
        sd.thickness = 0.003
    # an Arraiolos-style wool rug under the chair
    rug = D.noisy("arraiolos", "#cdbd9f", "#a86450", 0.95, scale=16.0, bump=0.2, lo=0.42, hi=0.62)
    boxmm("rug", (0.55, 0.55, 0.0), (2.05, 1.7, 0.008), rug, bev=0.003)
    boxmm("rug_border", (0.52, 0.52, 0.0), (2.08, 1.73, 0.006), mat("rug_border", "#2f4d6b", 0.95), bev=0.002)


def build_storyboard(M):
    """A pinboard over the desk with the pigeon's storyboard (the studio's film: "pombo", sc014), the new desk's echo
    of the shop's corkboard."""
    use("SET")
    x0, x1, z0, z1 = 0.95, 1.95, 1.48, 2.02
    boxmm("sb_board", (x0, LD - 0.02, z0), (x1, LD, z1), D.noisy("felt_grey", "#5d6268", "#555a60", 0.95, scale=80.0),
          bev=0.004)
    ink = mat("sb_ink", "#2f3135", 0.6)
    rng = random.Random(14)
    for k in range(8):
        r, c = divmod(k, 4)
        x, z = x0 + 0.13 + c * 0.24, z1 - 0.12 - r * 0.24
        p = grp(f"sb_card{k}", (x, LD - 0.0205, z), (90, rng.uniform(-3, 3), 0))
        rect(f"sb_paper{k}", -0.1, -0.065, 0.1, 0.065, 0, M["paper"], p)
        rect(f"sb_frame{k}", -0.09, -0.042, 0.09, 0.055, 0.0002, mat("sb_panel", "#f6f3ea", 0.8), p)
        # the pigeon: body, head, beak, eye, a hint of a wing, in pencil
        bx, by = rng.uniform(-0.03, 0.03), rng.uniform(-0.01, 0.015)
        pts = [(bx + 0.03 * cos(t), by + 0.017 * sin(t), 0.0004) for t in np.linspace(0, 2 * pi, 18)]
        curve(f"sb_body{k}", pts, 0.0007, ink, parent=p, res=3, bres=1, cyclic=True)
        hx, hy = bx + 0.03, by + 0.02
        curve(f"sb_head{k}", [(hx + 0.01 * cos(t), hy + 0.009 * sin(t), 0.0004) for t in np.linspace(0, 2 * pi, 12)],
              0.0007, ink, parent=p, res=3, bres=1, cyclic=True)
        curve(f"sb_beak{k}", [(hx + 0.009, hy + 0.002, 0.0004), (hx + 0.018, hy - 0.001, 0.0004),
                              (hx + 0.009, hy - 0.003, 0.0004)], 0.0006, ink, parent=p, res=2, bres=1)
        disc(f"sb_eye{k}", hx + 0.003, hy + 0.003, 0.0012, 0.0005, ink, p, n=6)
        curve(f"sb_wing{k}", [(bx - 0.015, by + 0.008, 0.0004), (bx + 0.005, by - 0.002, 0.0004),
                              (bx + 0.018, by + 0.004, 0.0004)], 0.0006, ink, parent=p, res=4, bres=1)
        text(f"sb_num{k}", f"sc014 · {k + 1:02d}", "consola.ttf", 0.0065, (-0.088, -0.056, 0.0004), ink, ax="LEFT",
             parent=p)
        D.pushpin(f"sb_pin{k}", p, 0, 0.058, M["pin_red"] if k % 3 else M["pin_yellow"])


# ================================================================ wear and tear (Theo's second day; the building is old)
LISBON_RULES = [
    (D.PRINT_SKIP + ("lx_led_red", "lx_disp", "lx_win_*", "lx_sky", "lx_river", "lx_hills", "telha", "fac*",
                     "lx_church", "lx_dome", "bk_*", "artbook*", "monstera*", "seagrass", "lx_keycap"), None),
    (("birch_ply",), dict(rv=0.06, scratch=0.22, edge=0.5, edge_val=1.12, edge_w=0.004)),
    (("lx_floor*",), dict(rv=0.1, scratch=0.55, scuff=0.3, edge=1.0, edge_val=0.55, edge_sat=1.05, edge_rough=0.85,
                          edge_w=0.004)),
    (("lime",), dict(rv=0.06, cv=0.04, scuff=0.18)),
    (("azulejo",), dict(rv=0.04)),
    (("lx_marble",), dict(rv=0.05, scratch=0.25)),
    (("lx_paint", "lx_cream", "lx_socket*"), dict(rv=0.06, scuff=0.2, edge=0.55, edge_val=1.1, edge_w=0.004)),
    (("lx_mon", "lx_bezel", "lx_case", "lx_tablet", "lx_dock", "lx_chair_blk", "lx_steel_blk", "lx_pen",
      "lx_tab_key"), dict(rv=0.06, smudge=0.45, scratch=0.12)),
    (("lx_alu", "lx_arm_alu", "lx_pad", "lx_wheel_steel"), dict(rv=0.05, smudge=0.55, scratch=0.18)),
    (("lx_mouse_m", "lx_mouse_side", "lx_thumbwheel"), dict(rv=0.04, smudge=0.35)),
    (("mk_*",), dict(rv=0.04, smudge=0.15)),
    (("lx_tablet_area", "lx_silicone", "lx_mesh", "lx_seat", "arraiolos", "rug_border"), dict(rv=0.05)),
] + D.WEAR_RULES
LISBON_PROPS = [
    ("case_top", {"dust": 0.5}), ("artbook*", {"dust": 0.4}), ("lx_sill", {"dust": 0.35}),
    ("mon_*_body", {"dust": 0.35}), ("mon_*_back", {"dust": 0.45}), ("lx_pole_cap", {"dust": 0.6}),
    ("poster_fr_t", {"dust": 0.7}), ("lx_bullnose_*", {"dust": 0.45}), ("sb_board", {"dust": 0.3}),
    ("lx_frame_*", {"dust": 0.4}), ("lx_bar_h*", {"dust": 0.5}), ("lx_shutter*", {"dust": 0.4}),
    ("lx_wall_socket", {"dust": 0.3}), ("mq_base", {"dust": 0.5}), ("hps_base", {"dust": 0.2}),
    ("sb_paper*", {"age": 0.02}), ("badge_card", {"age": 0.0}), ("napkin", {"age": 0.0}),
]


def tile_craze(m):
    """Old azulejos: a fine crackle in the glaze and the odd chipped corner showing the biscuit."""
    nt, b, col, r = D._bsdf_io(m)
    p, p0 = D._wcoords(nt)
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = "DISTANCE_TO_EDGE"
    v.inputs["Scale"].default_value = 55.0
    nt.links.new(p, v.inputs["Vector"])
    crack = D._math(nt, "MULTIPLY", D._ramp(nt, v.outputs["Distance"], 0.014, 0.0),
                    D._ramp(nt, D._nz(nt, p, 6.0, 3.0), 0.45, 0.6))
    col = D._mixc(nt, D._math(nt, "MULTIPLY", crack, 0.35), col, "#6d6656")
    dv, dc = D._vor(nt, p, 7.0)
    chip = D._math(nt, "MULTIPLY", D._ramp(nt, dv, 0.11, 0.07), D._ramp(nt, dc, 0.9, 0.92))
    col = D._mixc(nt, chip, col, "#d9c9a8")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(D._lerp(nt, chip, r, 0.85), b.inputs["Roughness"])


def tablet_sheen(m):
    """The drawing surface polished where the side of his hand rests (a right-hander, lower right), a few nib trails."""
    nt, b, col, r = D._bsdf_io(m)
    p, p0 = D._wcoords(nt)
    x, y, z = D._xyz(nt, p0)
    hand = D._math(nt, "MULTIPLY", D._ramp(nt, D._dist2(nt, x, y, 0.06, -0.035, 1.4, 1.0), 0.07, 0.02),
                   D._ramp(nt, D._nz(nt, p, 30.0, 3.0), 0.3, 0.6))
    nt.links.new(D._lerp(nt, hand, r, 0.42), b.inputs["Roughness"])
    nt.links.new(D._mixc(nt, D._math(nt, "MULTIPLY", hand, 0.4), col, "#2a2b30"), b.inputs["Base Color"])


def dress_lisbon(M):
    D.set_props(LISBON_PROPS)
    D.weather_all(LISBON_RULES)
    for m in [x for x in bpy.data.materials if x.name.startswith("lx_floor")]:
        D.floor_wear(m, path=(1.9, -0.05, 1.05, 1.05, 0.3), chair=(0.95, 1.22, 0.45), walls=(0.0, LD))
    nt, b, col, r = D._bsdf_io(MATS["birch_ply"])           # yesterday's bica left a faint ring
    pos, x, y, z = D._world_xy(nt)
    col, r = D.ring_marks(nt, col, r, x, y, [(0.742, 2.168, 0.0215, 0.62)], stain="#8a6a48")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(r, b.inputs["Roughness"])
    tile_craze(MATS["azulejo"])
    tablet_sheen(MATS["lx_tablet_area"])
    D.cork_marks(MATS["felt_grey"], ghosts=[], old_pins=[(-0.4, 0.2), (0.33, -0.18), (0.05, 0.22)], hole_k=0.55,
                 hole_rgb="#2c2f33")


# ================================================================ lights, cameras, presets
def build_lights(M, heads):
    bpy.context.view_layer.update()
    wy0, wy1, wz0, wz1 = WIN
    wc = Vector((0.0, (wy0 + wy1) / 2, (wz0 + wz1) / 2))
    # day: Lisbon sun through the window, the sky in the window, warm bounce. v2.4 (film review, 26 Nov): the day read
    # overblown next to the shop it cuts from (median luma ~200 vs 126, blacks lifted by bloom, ~4% clipped), so the
    # daylight is lower in the scene itself (less of the room crosses the bloom threshold) and the fills come down
    # more than the sun, for contrast: sun x0.7, window sky x0.4, bounce x0.35 (with DAY_* in apply_preset)
    sun = light("LL_sun", "SUN", (-3, 1.0, 4), 18.2, (1.0, 0.9, 0.74), "DAY")
    sun.data.angle = radians(2.0)
    sun.rotation_euler = Vector((0.8, 0.36, -0.46)).to_track_quat("-Z", "Y").to_euler()
    light("LL_window_sky", "AREA", (-0.12, wc.y, wc.z), 64.0, (0.78, 0.86, 1.0), "DAY", target=(1.6, 1.9, 0.8),
          size=1.0, size_y=1.6)
    light("LL_bounce", "AREA", (1.7, 0.5, 2.7), 19.25, (1.0, 0.9, 0.78), "DAY", target=(1.3, 2.2, 0.7), size=2.2,
          size_y=1.6)
    # night: city light and moon through the window, the panels' glow, a warm street lamp far below
    light("LL_moon", "SPOT", (-2.6, 0.9, 3.6), 160.0, (0.55, 0.66, 1.0), "NIGHT", target=(1.0, 2.0, 0.4), spot=28,
          blend=0.4, radius=0.25)
    light("LL_city", "AREA", (-0.12, wc.y, wc.z - 0.3), 5.0, (1.0, 0.72, 0.5), "NIGHT", target=(1.6, 1.9, 1.2),
          size=1.0, size_y=1.2)
    light("LL_night_fill", "AREA", (1.6, 0.6, 2.6), 1.6, (0.6, 0.68, 0.9), "NIGHT", target=(1.3, 2.2, 0.7), size=2.0)
    for slot, head in heads.items():
        mw = head.matrix_world
        n = (mw.to_3x3() @ Vector((0, -1, 0))).normalized()
        c = mw @ Vector((0, -0.02, 0))
        light(f"LL_glow_{slot}", "AREA", c + n * 0.01, 4.0, (0.8, 0.85, 1.0), "SHARED", target=c + n, size=0.6,
              size_y=0.34)
    lc = bpy.data.objects["laptop_screen"].matrix_world
    n = (lc.to_3x3() @ Vector((0, -1, 0))).normalized()
    light("LL_glow_laptop", "AREA", lc.translation + n * 0.01, 1.5, (0.95, 0.95, 1.0), "SHARED",
          target=lc.translation + n, size=0.3, size_y=0.19)


def build_cameras():
    camera("LCAM_wide", (2.25, -4.6, 2.55), (1.25, 1.45, 0.95), 36, 1.6, (1.2, 2.2, 1.0))
    camera("LCAM_medium", (2.3, 0.55, 1.5), (0.92, 2.32, 1.02), 26, 2.8, (1.1, 2.15, 0.9))
    camera("LCAM_detail", (1.05, 1.45, 1.05), (0.85, 2.1, 0.76), 40, 2.8, (0.8, 2.0, 0.76))
    camera("LCAM_close_half", (1.55, 0.95, 1.38), (1.07, 2.5, 1.02), 30, 2.8, (1.07, 2.2, 0.9))
    camera("LCAM_mouse", (1.31, 2.13, 0.895), (1.423, 2.014, 0.768), 55, 13.0, (1.423, 2.014, 0.772))
    camera("LCAM_stand", (0.99, 1.99, 0.9), (0.63, 2.31, 0.82), 40, 5.6, (0.63, 2.3, 0.82))


def apply_preset(name, M, sky_m, lit_m):
    day = name == "day"
    COLL["DAY"].hide_render = not day
    COLL["NIGHT"].hide_render = day
    sc = bpy.context.scene
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = rgba("#c7d8e6") if day else rgba("#141b2b")
    bg.inputs[1].default_value = DAY_WORLD if day else 0.12
    sk = principled(sky_m)
    sk.inputs["Emission Color"].default_value = rgba("#bcd6ea") if day else rgba("#16213a")
    sk.inputs["Emission Strength"].default_value = DAY_SKY if day else 1.0
    principled(lit_m).inputs["Emission Strength"].default_value = 0.0 if day else 4.0
    aspects = {"main": 16 / 9, "studio": 16 / 9, "laptop": 16 / 10}
    for slot in ("main", "studio", "laptop"):
        set_panel(slot, LSCREENS[name][slot], aspects[slot])
        PANELS[slot]["bright"].outputs[0].default_value = LBRIGHT[name][slot]
        mean = PANELS[slot].get("mean")
        if mean is not None:
            lum = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
            ln = LIGHTS[f"LL_glow_{slot}"]
            base = 1.5 if slot == "laptop" else 4.0
            ln.data.energy = base * LBRIGHT[name][slot] * max(lum, 0.01) / 0.08
            ln.data.color = tuple(float(c) for c in (mean / max(mean.max(), 1e-6)) * 0.7 + 0.3)
    sc.view_settings.exposure = DAY_EV if day else 0.42
    # the shared bloom (desk.py build_compositor: threshold 1.0, strength 0.22) veiled the whole sunlit room; by day
    # only real highlights bloom (the night keeps the approved glow on the panels)
    gl = next((n for n in sc.compositing_node_group.nodes if n.bl_idname == "CompositorNodeGlare"), None)
    if gl is not None:
        gl.inputs["Threshold"].default_value = DAY_BLOOM[0] if day else 1.0
        gl.inputs["Strength"].default_value = DAY_BLOOM[1] if day else 0.22


def main():
    args = parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for name in ("SET", "OUTSIDE", "DAY", "NIGHT", "SHARED", "CAMS"):
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    D.setup_render(args)
    # the same diorama presentation as the shop: the camera sees a dark surround, the room keeps its daylight. v2.4:
    # near-black, as the film's opening keys the shop's (no indigo void at the frame's edges)
    wn = bpy.context.scene.world.node_tree
    lp = wn.nodes.new("ShaderNodeLightPath")
    dark = wn.nodes.new("ShaderNodeBackground")
    dark.inputs[0].default_value = rgba("#060709")
    dark.inputs[1].default_value = 0.5
    mix = wn.nodes.new("ShaderNodeMixShader")
    wn.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    wn.links.new(wn.nodes["Background"].outputs[0], mix.inputs[1])
    wn.links.new(dark.outputs[0], mix.inputs[2])
    wn.links.new(mix.outputs[0], wn.nodes["World Output"].inputs["Surface"])
    M = D.build_materials()
    D.ensure_photo(M)
    build_room(M)
    lit_m, sky_m = build_outside(M)
    tray = build_desk(M)
    heads = build_arm_and_monitors(M)
    build_keyboard75(M)
    build_desk_kit(M)
    build_dock_and_cables(M, tray)
    # the keyboard's coiled cable and the tablet's lead, into the dock's front ports
    at, d = port_frame("mk_cable")
    coil = [at + d * 0.01]
    for k in range(90):
        t = k / 89
        p = at + d * (0.02 + 0.1 * t) + Vector((-0.12 * t, 0.06 * t, 0.0))
        coil.append(p + Vector((0.0045 * cos(k * 0.9), 0, 0.0045 * sin(k * 0.9) + 0.004)))
    ad, dd = port_frame("dock_kb")
    stp = connector("kb_dock_plug", "usb", ad, dd, M)
    coil += [Vector((0.86, 2.3, DZ + 0.003)), stp + dd * 0.02, stp]
    D.cable("mk_coil", coil, 0.0022, mat("mk_cable", "#d9663a", 0.45), res=4)
    at, d = port_frame("tablet_usb")
    ad, dd = port_frame("dock_tab")
    stp = connector("tab_dock_plug", "usb", ad, dd, M)
    D.cable("tablet_lead", [at, at + d * 0.02, (1.48, 2.2, DZ + 0.002), (1.2, 2.34, DZ + 0.002),
                            (0.95, 2.36, DZ + 0.002), stp + dd * 0.02, stp], 0.0018, M["plastic_blk"])
    connector("tablet_usb_plug", "relief", at, d, M)
    build_chair(M)
    build_storyboard(M)
    build_studio_corner(M)
    D.apply_fits()
    dress_lisbon(M)
    build_lights(M, heads)
    build_cameras()
    print(f"built {len(bpy.data.objects)} objects in {time.time() - t0:.1f}s")
    if args.save_blend:
        apply_preset("day", M, sky_m, lit_m)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "lisbon.blend"), compress=True)
    if args.no_render:
        return
    sc = bpy.context.scene
    for shot in [s.strip() for s in args.shots.split(",") if s.strip()]:
        if shot == "pair":
            make_pair()
            continue
        cam, preset, fname, ev = SHOTS[shot][:4]
        sc.render.resolution_x, sc.render.resolution_y = SHOTS[shot][4] if len(SHOTS[shot]) > 4 else (1920, 1080)
        apply_preset(preset, M, sky_m, lit_m)
        wide = shot == "wide_day"
        cam_p = Vector(bpy.data.objects[cam].location)         # (cameras are unparented)
        for ob in COLL["OUTSIDE"].objects:                    # in the wide, keep only what hides behind the wall
            hide = False
            if wide:
                for c in ob.bound_box:
                    v = ob.matrix_world @ Vector(c)
                    t = (-SIDE_T - cam_p.x) / (v.x - cam_p.x) if v.x < -SIDE_T else None
                    if t is None or cam_p.y + t * (v.y - cam_p.y) < 0.05 or cam_p.z + t * (v.z - cam_p.z) > LH:
                        hide = True
                        break
            if ob.name == "lx_sky_wide":
                hide = not wide
            ob.hide_render = hide
        sc.view_settings.exposure += ev
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = os.path.join(OUT, fname)
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {shot} -> {fname} in {time.time() - t1:.1f}s")


def make_pair():
    """The close: the shop desk at night (left, the old) and Theo's Lisbon desk at night (right, the new), side by
    side, a thin dark seam between them."""
    left, right = os.path.join(OUT, "x_close_half_shop.png"), os.path.join(OUT, "x_close_half_lisbon.png")
    if not (os.path.exists(left) and os.path.exists(right)):
        print("pair: render desk.py --shots close_half and lisbon.py --shots close_half first")
        return
    ims = [bpy.data.images.load(p, check_existing=False) for p in (left, right)]
    halves = [np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4) for im in ims]
    h, w = halves[0].shape[:2]
    out = np.zeros((h, 2 * w, 4), np.float32)
    out[..., 3] = 1
    out[:, :w] = halves[0]
    out[:, w:] = halves[1]
    seam = 3
    out[:, w - seam:w + seam, :3] = 0.015
    im = bpy.data.images.new("close_two_desks", 2 * w, h, alpha=False)
    im.pixels.foreach_set(out.ravel())
    im.filepath_raw = os.path.join(OUT, "close_two_desks.png")
    im.file_format = "PNG"
    im.save()
    print("RENDERED pair -> close_two_desks.png")


if __name__ == "__main__":
    main()
