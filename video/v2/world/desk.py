"""Barnaby film v2: the back-office desk diorama at Spokes & Sprockets.

Builds the whole set procedurally (no external assets except Windows fonts and the screen PNG) and renders stills
with Eevee. Everything is reproducible from this file. See video/v2/WORLD.md for the world it depicts.

Run from the repo root (Git Bash):
    source scripts/env.sh
    "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \
        --python video/v2/world/desk.py -- [options]

Options (after the `--`):
    --shots a,b,...    which stills to render (default: the four in DEFAULT_SHOTS; also board_night, shelf_monday)
    --scale N          resolution percentage of 1920x1080 (default 100; use 40 for quick looks)
    --samples N        Eevee render samples (default 64)
    --screen PATH      PNG to show on the monitor (default: screen_placeholder.png, generated if missing)
    --regen-screen     rebuild screen_placeholder.png
    --save-blend       also save out/desk.blend (for animation work)
    --no-render        build only

Collections: SET (the room, desk, PC, corkboard, shelf), WORKSHOP (through the doorway), THEO (night-only props),
MARTIN (Monday-only props), NIGHT and MONDAY (each preset's lights), CAMS. apply_preset() swaps them.
Handwriting: Segoe Print is Theo's hand (the one sticky note, the box), Ink Free is Martin's (calendar, labels, job card).
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
OUT = os.path.join(HERE, "out")
PLACEHOLDER = os.path.join(HERE, "screen_placeholder.png")
FONT_DIR = r"C:\Windows\Fonts"

# shot name -> (camera, lighting preset, output file)
SHOTS = {
    "wide_night": ("CAM_wide", "night", "01_wide_night.png", 0.45),
    "medium_night": ("CAM_medium", "night", "02_medium_night.png", 0.0),
    "keys_night": ("CAM_keys", "night", "03_keys_night.png", 0.0),
    "medium_monday": ("CAM_medium_monday", "monday", "04_medium_monday.png", 0.0),
    # optional detail stills (not in the default set): the corkboard and the brake-pads drawer
    "board_night": ("CAM_board", "night", "x_board_night.png", 0.2),
    "shelf_monday": ("CAM_shelf", "monday", "x_shelf_monday.png", 0.0),
}
DEFAULT_SHOTS = "wide_night,medium_night,keys_night,medium_monday"

# ---------------------------------------------------------------- room layout (metres; x right, y into room, z up)
W, D, H, WT = 3.9, 2.8, 2.45, 0.14          # office width, depth to back wall, wall height, wall thickness
DOOR = (2.62, 3.42, 2.08)                     # doorway in back wall: x0, x1, top
WIN = (1.05, 1.95, 1.05, 2.0)                 # window in left wall: y0, y1, z0, z1
DZ = 0.75                                     # desk top height
WS_H = 2.38                                   # workshop ceiling (kept under the office wall tops)

RNG = random.Random(1987)                     # the shop's founding year; every run is identical


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default=DEFAULT_SHOTS)
    p.add_argument("--scale", type=int, default=100)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--screen", default=None)
    p.add_argument("--regen-screen", action="store_true")
    p.add_argument("--save-blend", action="store_true")
    p.add_argument("--no-render", action="store_true")
    return p.parse_args(argv)


# ================================================================ colour and materials
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgba(c, a=1.0):
    """'#rrggbb' (sRGB) or an (r,g,b[,a]) linear tuple -> linear RGBA."""
    if isinstance(c, str):
        h = c.lstrip("#")
        return tuple(_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (a,)
    return tuple(c[:3]) + ((c[3],) if len(c) > 3 else (a,))


MATS = {}


def principled(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def sock(coll, ident):
    return next(s for s in coll if s.identifier == ident)


def mat(name, color, rough=0.6, metal=0.0, spec=0.5, coat=0.0, emit=None, estr=0.0, alpha=None):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    b.inputs["Base Color"].default_value = rgba(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    if emit is not None:
        b.inputs["Emission Color"].default_value = rgba(emit)
        b.inputs["Emission Strength"].default_value = estr
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
        m.use_transparent_shadow = True
    m.diffuse_color = rgba(color)
    MATS[name] = m
    return m


def _coords(m, space="Object", scale=(1, 1, 1)):
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs[space], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _mix(nt, fac_out, a, b, blend="MIX"):
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = blend
    nt.links.new(fac_out, sock(mx.inputs, "Factor_Float"))
    sock(mx.inputs, "A_Color").default_value = rgba(a)
    sock(mx.inputs, "B_Color").default_value = rgba(b)
    return sock(mx.outputs, "Result_Color")


def _bump(nt, b, height_out, strength=0.2, dist=0.002):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    nt.links.new(height_out, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])


def wood(name, c1, c2, rough=0.5, axis="X", grain=7.0, coat=0.0):
    """Low-key wood: wave bands along the grain axis plus noise mottling."""
    if name in MATS:
        return MATS[name]
    m = mat(name, c1, rough, coat=coat)
    nt = m.node_tree
    b = principled(m)
    sc = {"X": (1.0, 60.0, 60.0), "Y": (60.0, 1.0, 60.0)}[axis]
    streak = nt.nodes.new("ShaderNodeTexNoise")
    streak.inputs["Scale"].default_value = grain * 0.4
    streak.inputs["Detail"].default_value = 6.0
    streak.inputs["Roughness"].default_value = 0.62
    nt.links.new(_coords(m, scale=sc), streak.inputs["Vector"])
    blot = nt.nodes.new("ShaderNodeTexNoise")
    blot.inputs["Scale"].default_value = 2.2
    blot.inputs["Detail"].default_value = 2.0
    nt.links.new(_coords(m, scale=(sc[0] * 0.08 + 1, sc[1] * 0.08 + 1, 2.0)), blot.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY_ADD"
    nt.links.new(streak.outputs["Fac"], mx.inputs[0])
    mx.inputs[1].default_value = 0.8
    nt.links.new(blot.outputs["Fac"], mx.inputs[2])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mx.outputs[0], ramp.inputs["Value"])
    ramp.inputs["From Min"].default_value = 0.72
    ramp.inputs["From Max"].default_value = 1.18
    nt.links.new(_mix(nt, ramp.outputs["Result"], c1, c2), b.inputs["Base Color"])
    _bump(nt, b, streak.outputs["Fac"], 0.03, 0.001)
    return m


def noisy(name, c1, c2, rough=0.6, scale=8.0, bump=0.0, detail=3.0, space="Object", metal=0.0, lo=0.3, hi=0.7):
    """Two-tone procedural mottling (plaster, concrete, cork, cardboard, felt)."""
    if name in MATS:
        return MATS[name]
    m = mat(name, c1, rough, metal=metal)
    nt = m.node_tree
    b = principled(m)
    v = _coords(m, space)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(v, nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = lo
    mr.inputs["From Max"].default_value = hi
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(_mix(nt, mr.outputs["Result"], c1, c2), b.inputs["Base Color"])
    if bump:
        _bump(nt, b, nz.outputs["Fac"], bump, 0.002)
    return m


def brick(name, c1, c2, mortar, scale=6.0, rough=0.85, row=0.25, width=0.5):
    if name in MATS:
        return MATS[name]
    m = mat(name, c1, rough)
    nt = m.node_tree
    b = principled(m)
    v = _coords(m)
    bk = nt.nodes.new("ShaderNodeTexBrick")
    bk.inputs["Color1"].default_value = rgba(c1)
    bk.inputs["Color2"].default_value = rgba(c2)
    bk.inputs["Mortar"].default_value = rgba(mortar)
    bk.inputs["Scale"].default_value = scale
    bk.inputs["Mortar Size"].default_value = 0.018
    bk.inputs["Brick Width"].default_value = width
    bk.inputs["Row Height"].default_value = row
    nt.links.new(v, bk.inputs["Vector"])
    nt.links.new(bk.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, b, bk.outputs["Fac"], 0.25, 0.003)
    return m


def dots(name, c1, c2, pitch=0.025, r=0.22, rough=0.8):
    """Pegboard: a dot grid of holes (object space, board facing -y)."""
    if name in MATS:
        return MATS[name]
    m = mat(name, c1, rough)
    nt = m.node_tree
    b = principled(m)
    v = _coords(m, scale=(1 / pitch, 1 / pitch, 1 / pitch))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(v, sep.inputs[0])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], cmb.inputs["X"])
    nt.links.new(sep.outputs["Z"], cmb.inputs["Y"])
    fr = nt.nodes.new("ShaderNodeVectorMath")
    fr.operation = "FRACTION"
    nt.links.new(cmb.outputs[0], fr.inputs[0])
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    nt.links.new(fr.outputs[0], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(sub.outputs[0], ln.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    nt.links.new(ln.outputs["Value"], lt.inputs[0])
    lt.inputs[1].default_value = r
    nt.links.new(_mix(nt, lt.outputs[0], c1, c2), b.inputs["Base Color"])
    return m


def stripes(name, c1, c2, freq=400.0, rough=0.3, metal=0.6):
    """Bands along Z (the edge of a stack of CDs)."""
    if name in MATS:
        return MATS[name]
    m = mat(name, c1, rough, metal=metal)
    nt = m.node_tree
    b = principled(m)
    v = _coords(m)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(v, sep.inputs[0])
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "SINE"
    sc = nt.nodes.new("ShaderNodeMath")
    sc.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Z"], sc.inputs[0])
    sc.inputs[1].default_value = freq
    nt.links.new(sc.outputs[0], mth.inputs[0])
    nt.links.new(_mix(nt, mth.outputs[0], c1, c2), b.inputs["Base Color"])
    return m


# ---------------------------------------------------------------- palette (warm, slightly desaturated)
def build_materials():
    M = {}
    M["plinth"] = wood("plinth", "#2c231d", "#1f1814", 0.45, coat=0.3)
    M["section"] = mat("section", "#3a3431", 0.9)
    M["wall"] = noisy("wall", "#d3c3a3", "#c7b693", 0.9, scale=4.0, bump=0.05)
    M["panel"] = mat("panel", "#5d7466", 0.55, spec=0.45)
    M["trim"] = mat("trim", "#e4d9c1", 0.42, spec=0.5)
    for i, (a, b) in enumerate([("#6d4e37", "#57392a"), ("#62452f", "#4d3424"), ("#77583f", "#5c412e"),
                                ("#6a4a33", "#523727")]):
        M[f"floor{i}"] = wood(f"floor{i}", a, b, 0.68, axis="Y", grain=5.0)
    M["oak"] = wood("oak", "#ab7b4c", "#8a5c37", 0.42, coat=0.25)
    M["oak_lt"] = wood("oak_lt", "#b88a5a", "#996c43", 0.45)
    M["oak_y"] = wood("oak_y", "#ab7b4c", "#8a5c37", 0.42, axis="Y")
    M["pc"] = mat("pc", "#1b1b1d", 0.45, spec=0.45)
    M["pc_dk"] = mat("pc_dk", "#121213", 0.3, spec=0.55)
    M["gloss"] = mat("gloss", "#0a0a0b", 0.1, spec=0.75, coat=0.6)
    M["hole"] = mat("hole", "#050505", 0.9)
    M["steel"] = mat("steel", "#a9adb1", 0.32, metal=1.0)
    M["steel_dk"] = mat("steel_dk", "#6d7174", 0.35, metal=1.0)
    M["chrome"] = mat("chrome", "#c9ccd0", 0.12, metal=1.0)
    M["brass"] = mat("brass", "#c69c55", 0.24, metal=1.0)
    M["brass_old"] = mat("brass_old", "#a98546", 0.38, metal=1.0)
    M["cork"] = noisy("cork", "#b98d5c", "#91673e", 0.9, scale=140.0, bump=0.35, detail=4.0)
    M["paper"] = mat("paper", "#f1ebdd", 0.75, spec=0.35)
    M["paper_back"] = mat("paper_back", "#ddd5c4", 0.8, spec=0.3)
    M["manila"] = mat("manila", "#e4d0a2", 0.75, spec=0.3)
    M["ink"] = mat("ink", "#23252c", 0.5)
    M["print_grey"] = mat("print_grey", "#8d8a84", 0.7)
    M["red_ink"] = mat("red_ink", "#b3392c", 0.45)
    M["blue_ink"] = mat("blue_ink", "#2a3f86", 0.45)
    M["sticky"] = mat("sticky", "#ebd062", 0.7, spec=0.35)
    M["card"] = noisy("card", "#b88f61", "#a27a4f", 0.85, scale=25.0, bump=0.04)
    M["tape"] = mat("tape", "#cdb27e", 0.25, spec=0.6)
    M["marker"] = mat("marker", "#1c1d22", 0.4)
    M["mustard"] = mat("mustard", "#b98b2f", 0.32, spec=0.55, coat=0.3)
    M["shade_in"] = mat("shade_in", "#efe4c9", 0.5)
    M["ceramic"] = mat("ceramic", "#eee5d3", 0.18, spec=0.6, coat=0.4)
    M["navy"] = mat("navy", "#2b3b5e", 0.3)
    M["fabric"] = noisy("fabric", "#3b414a", "#30353d", 0.95, scale=300.0, bump=0.2)
    M["plastic_blk"] = mat("plastic_blk", "#1d1d1f", 0.4)
    M["rubber"] = mat("rubber", "#161616", 0.85)
    M["led_blue"] = mat("led_blue", "#4d8cff", 0.4, emit="#4d8cff", estr=6.0)
    M["led_amber"] = mat("led_amber", "#ff9a2e", 0.4, emit="#ff9a2e", estr=5.0)
    M["led_green"] = mat("led_green", "#5cff7a", 0.4, emit="#5cff7a", estr=4.0)
    M["led_off"] = mat("led_off", "#2b2f2b", 0.3)
    M["glass"] = mat("glass", "#c9d6dc", 0.04, spec=0.9, alpha=0.1)
    M["water"] = mat("water", "#8fa6bd", 0.12, spec=0.55, alpha=0.5)
    M["clear"] = mat("clear", "#eef3f5", 0.08, spec=0.7, alpha=0.1)
    M["dome"] = mat("dome", "#e6ecef", 0.03, spec=0.9, coat=1.0, alpha=0.07)
    M["radiator"] = mat("radiator", "#ddd3bc", 0.35, spec=0.5)
    M["teal"] = mat("teal", "#3e7c74", 0.3, coat=0.5)
    M["bikered"] = mat("bikered", "#9b4532", 0.3, coat=0.5)
    M["tyre"] = mat("tyre", "#1c1b1a", 0.8)
    M["saddle"] = mat("saddle", "#2a2321", 0.5)
    M["concrete"] = noisy("concrete", "#8e8b85", "#7a7771", 0.8, scale=3.0, bump=0.05)
    M["ws_brick"] = brick("ws_brick", "#d9d4c9", "#cdc7bb", "#bdb6a9", scale=5.5)
    M["pegboard"] = dots("pegboard", "#a07e57", "#3a2c1f", pitch=0.025)
    M["counter_paint"] = mat("counter_paint", "#3f5a4b", 0.45, coat=0.2)
    M["drawer_body"] = mat("drawer_body", "#4f6b85", 0.4, spec=0.5)
    M["binder_navy"] = mat("binder_navy", "#2f4a6b", 0.4)
    M["binder_red"] = mat("binder_red", "#7b302a", 0.4)
    M["binder_green"] = mat("binder_green", "#3d5c3a", 0.4)
    M["binder_black"] = mat("binder_black", "#262626", 0.4)
    M["skin"] = mat("skin", "#d9a785", 0.6)
    M["cd"] = stripes("cd", "#c4cbcf", "#9fb4b2", freq=420.0, rough=0.35, metal=0.5)
    M["cd_top"] = mat("cd_top", "#d7dadc", 0.25, metal=0.8)
    M["tea"] = mat("tea", "#7b4d2c", 0.05, spec=0.8)
    M["coffee"] = mat("coffee", "#2a170c", 0.05, spec=0.8)
    M["rag"] = noisy("rag", "#9b4a3d", "#33261f", 0.95, scale=14.0, bump=0.3, lo=0.4, hi=0.6)
    M["plant"] = mat("plant", "#4f7a45", 0.55)
    M["plant_dk"] = mat("plant_dk", "#3c5f37", 0.55)
    M["terracotta"] = mat("terracotta", "#b2684a", 0.8)
    M["hoodie"] = noisy("hoodie", "#6b6a3e", "#5d5c35", 0.95, scale=60.0, bump=0.15)
    M["kraft"] = mat("kraft", "#a98557", 0.8)
    M["lens"] = mat("lens", "#dfe8ea", 0.03, spec=1.0, alpha=0.15)
    M["tortoise"] = noisy("tortoise", "#5a3520", "#2a170d", 0.25, scale=40.0)
    M["cord"] = mat("cord", "#1e1e22", 0.6)
    M["pencil"] = mat("pencil", "#d9a52c", 0.4, coat=0.3)
    M["pencil_wood"] = mat("pencil_wood", "#d8b98a", 0.7)
    M["eraser"] = mat("eraser", "#d98c8a", 0.8)
    M["pad_compound"] = noisy("pad_compound", "#3a3633", "#24211f", 0.9, scale=200.0, bump=0.3)
    M["mousepad"] = noisy("mousepad", "#566579", "#6f7d8e", 0.95, scale=5.0, lo=0.35, hi=0.65)
    M["clock_face"] = mat("clock_face", "#f0e9da", 0.5)
    M["outside_sky"] = mat("outside_sky", "#0b1220", 1.0, emit="#0b1220", estr=1.0)
    M["outside_brick"] = brick("outside_brick", "#6c4537", "#5b3a2e", "#8a8178", scale=9.0)
    M["outside_win"] = mat("outside_win", "#ffc985", 0.5, emit="#ffc985", estr=3.0)
    M["bulb"] = mat("bulb", "#fff1d6", 0.3, emit="#ffd9a0", estr=20.0)
    M["tube"] = mat("tube", "#f5f8ff", 0.3, emit="#f2f6ff", estr=0.0)
    M["radio_dial"] = mat("radio_dial", "#ffb35c", 0.4, emit="#ffb35c", estr=2.5)
    M["rain"] = mat("rain", "#9fb3c8", 0.5, emit="#9fb3c8", estr=0.6, alpha=0.25)
    for k, c in {"red": "#b3392c", "blue": "#2f5fa8", "yellow": "#e0b53a", "green": "#3f8a4f",
                 "white": "#f2efe8"}.items():
        M["pin_" + k] = mat("pin_" + k, c, 0.25, coat=0.5)
    return M


# ================================================================ object helpers
COLL = {}
CUR = ["SET"]


def use(name):
    CUR[0] = name


def link(ob, parent=None, coll=None):
    COLL[coll or CUR[0]].objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def _rot(r):
    return [radians(a) for a in r]


def grp(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, coll=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = loc
    e.rotation_euler = _rot(rot)
    return link(e, parent, coll)


def finish(name, bm, m=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, angle=40, coll=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mm in (m if isinstance(m, (list, tuple)) else [m]):
        if mm is not None:
            me.materials.append(mm)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=radians(angle))
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = _rot(rot)
    return link(ob, parent, coll)


def bevel(ob, w, seg=2, angle=35):
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = w
    md.segments = seg
    md.limit_method = "ANGLE"
    md.angle_limit = radians(angle)
    md.harden_normals = True
    md.use_clamp_overlap = True
    return ob


def box(name, size, loc=(0, 0, 0), m=None, rot=(0, 0, 0), bev=0.003, seg=2, parent=None, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    ob = finish(name, bm, m, parent, loc, rot, coll=coll)
    if bev > 0:
        bevel(ob, bev, seg)
    return ob


def boxmm(name, mn, mx, m=None, **kw):
    return box(name, [b - a for a, b in zip(mn, mx)], [(a + b) / 2 for a, b in zip(mn, mx)], m, **kw)


def cyl(name, r, h, loc=(0, 0, 0), m=None, rot=(0, 0, 0), n=16, r2=None, bev=0.0, seg=1, base=False,
        parent=None, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r,
                          radius2=r if r2 is None else r2, depth=h)
    if base:
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    ob = finish(name, bm, m, parent, loc, rot, coll=coll)
    if bev > 0:
        bevel(ob, bev, seg)
    return ob


def lathe(name, prof, n=20, loc=(0, 0, 0), m=None, rot=(0, 0, 0), seg_mats=None, parent=None, angle=50,
          coll=None):
    """Revolve a (radius, z) profile around Z. Radius 0 makes a pole."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-7:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * cos(2 * pi * i / n), r * sin(2 * pi * i / n), z)) for i in range(n)])
    for k, (a, b) in enumerate(zip(rings, rings[1:])):
        mi = seg_mats[k] if seg_mats else 0
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(n):
            j = (i + 1) % n
            if len(a) == 1:
                f = bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                f = bm.faces.new((a[i], a[j], b[0]))
            else:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(name, bm, m, parent, loc, rot, angle=angle, coll=coll)


def torus(name, R, r, loc=(0, 0, 0), m=None, rot=(0, 0, 0), nR=24, nr=8, arc=None, parent=None, coll=None,
          scale=None):
    bm = bmesh.new()
    a0, a1 = (0.0, 2 * pi) if arc is None else (radians(arc[0]), radians(arc[1]))
    closed = arc is None
    cnt = nR if closed else nR + 1
    grid = []
    for i in range(cnt):
        a = a0 + (a1 - a0) * i / nR
        grid.append([bm.verts.new(((R + r * cos(2 * pi * j / nr)) * cos(a), (R + r * cos(2 * pi * j / nr)) * sin(a),
                                   r * sin(2 * pi * j / nr))) for j in range(nr)])
    for i in range(nR):
        i2 = (i + 1) % cnt
        for j in range(nr):
            j2 = (j + 1) % nr
            bm.faces.new((grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = finish(name, bm, m, parent, loc, rot, angle=60, coll=coll)
    if scale:
        ob.scale = scale
    return ob


def sphere(name, r, loc=(0, 0, 0), m=None, seg=12, rings=8, scale=None, parent=None, coll=None, ico=0):
    bm = bmesh.new()
    if ico:
        bmesh.ops.create_icosphere(bm, subdivisions=ico, radius=r)
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    ob = finish(name, bm, m, parent, loc, angle=70, coll=coll)
    if scale:
        ob.scale = scale
    return ob


def tube(name, p1, p2, r, m=None, n=8, parent=None, coll=None, r2=None):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = cyl(name, r, d.length, loc=(p1 + p2) / 2, m=m, n=n, r2=r2, parent=parent, coll=coll)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return ob


def prism(name, pts, depth, loc=(0, 0, 0), m=None, rot=(0, 0, 0), bev=0.0, seg=1, parent=None, coll=None):
    """Extrude a 2D outline (XY) by depth along +Z."""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=[g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = finish(name, bm, m, parent, loc, rot, coll=coll)
    if bev > 0:
        bevel(ob, bev, seg)
    return ob


def flat(name, pts, z=0.0, m=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), coll=None):
    """A single flat polygon in XY facing +Z (paper prints, illustrations)."""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts])
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return finish(name, bm, m, parent, loc, rot, smooth=False, coll=coll)


def rect(name, x0, y0, x1, y1, z, m, parent=None):
    return flat(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z, m, parent)


def circ_pts(cx, cy, rx, ry=None, n=20, a0=0.0):
    ry = rx if ry is None else ry
    return [(cx + rx * cos(a0 + 2 * pi * i / n), cy + ry * sin(a0 + 2 * pi * i / n)) for i in range(n)]


def disc(name, cx, cy, r, z, m, parent=None, n=20, ry=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    return flat(name, circ_pts(cx, cy, r, ry, n), z, m, parent, loc, rot)


def annulus(name, outer, inner, z=0.0, m=None, parent=None, thick=0.0, loc=(0, 0, 0), rot=(0, 0, 0), bev=0.0):
    """Ring-shaped flat mesh between two loops with the same vertex count, optionally solidified."""
    bm = bmesh.new()
    o = [bm.verts.new((x, y, z)) for x, y in outer]
    i = [bm.verts.new((x, y, z)) for x, y in inner]
    n = len(o)
    for k in range(n):
        bm.faces.new((o[k], o[(k + 1) % n], i[(k + 1) % n], i[k]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    ob = finish(name, bm, m, parent, loc, rot, angle=50)
    if thick:
        sd = ob.modifiers.new("Solid", "SOLIDIFY")
        sd.thickness = thick
        sd.offset = 0
    if bev:
        bevel(ob, bev, 1)
    return ob


FONTS = {}
FIT = []


def font(fname):
    if fname not in FONTS:
        FONTS[fname] = bpy.data.fonts.load(os.path.join(FONT_DIR, fname), check_existing=True)
    return FONTS[fname]


def text(name, body, fname, size, loc=(0, 0, 0), m=None, rot=(0, 0, 0), ax="CENTER", ay="CENTER", parent=None,
         fit=None, line=1.0, char=1.0, extrude=0.0, coll=None, shear=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font(fname)
    cu.size = size
    cu.align_x = ax
    cu.align_y = ay
    cu.space_line = line
    cu.space_character = char
    cu.extrude = extrude
    cu.shear = shear
    if m is not None:
        cu.materials.append(m)
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = _rot(rot)
    link(ob, parent, coll)
    if fit:
        FIT.append((ob, fit))
    return ob


def apply_fits():
    bpy.context.view_layer.update()
    for ob, w in FIT:
        dx = ob.dimensions.x
        if dx > w:
            ob.scale = (w / dx,) * 3
    FIT.clear()


def curve(name, pts, r, m=None, parent=None, cyclic=False, order=3, res=6, bres=2, coll=None, flatz=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = bres
    cu.resolution_u = res
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    sp.use_cyclic_u = cyclic
    sp.use_endpoint_u = not cyclic
    sp.order_u = min(order, len(pts))
    if m is not None:
        cu.materials.append(m)
    ob = bpy.data.objects.new(name, cu)
    if flatz:
        ob.scale = (1, 1, flatz)
    return link(ob, parent, coll)


def no_shadow(*obs):
    for ob in obs:
        ob.visible_shadow = False


def aim(ob, target):
    d = Vector(target) - ob.matrix_world.translation if ob.parent else Vector(target) - Vector(ob.location)
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ================================================================ the screen PNG
def make_placeholder(path, w=1440, h=900):
    """A mid-blue 2009-style desktop with a glass taskbar, generic icons and a dial gadget. No logos."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h                                   # v = 0 at the top
    top, bot = np.array([0.22, 0.49, 0.80]), np.array([0.07, 0.23, 0.50])
    img = top * (1 - v[..., None]) + bot * v[..., None]
    for c, amp, wid, col in [(0.58, 0.22, 0.07, (0.10, 0.17, 0.22)), (0.70, 0.16, 0.05, (0.06, 0.12, 0.18)),
                             (0.46, 0.12, 0.035, (0.07, 0.10, 0.12))]:
        centre = c - amp * np.sin(u * 2.9 + c * 4.0)
        band = np.exp(-((v - centre) / wid) ** 2)
        img += band[..., None] * np.array(col)
    glow = np.exp(-(((u - 0.3) / 0.35) ** 2 + ((v - 0.35) / 0.3) ** 2))
    img += glow[..., None] * np.array([0.05, 0.07, 0.08])

    def box_(x0, y0, x1, y1, col, a=1.0):
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + np.array(col) * a

    # desktop icons, left column
    for i, col in enumerate([(0.93, 0.80, 0.42), (0.80, 0.86, 0.92), (0.95, 0.55, 0.25), (0.55, 0.80, 0.45)]):
        y0 = 24 + i * 96
        box_(30, y0, 78, y0 + 44, col)
        box_(30, y0, 78, y0 + 8, tuple(min(1, c * 1.12) for c in col))
        box_(22, y0 + 54, 86, y0 + 62, (0.93, 0.95, 0.97), 0.85)
    # dial gadget, top right
    cx, cy, r = w - 110, 120, 62
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    disc_ = d < r
    img[disc_] = img[disc_] * 0.35 + np.array([0.12, 0.14, 0.17]) * 0.65
    ring = (d > r - 5) & (d < r)
    img[ring] = np.array([0.78, 0.82, 0.86])
    ang = np.arctan2(yy - cy, xx - cx)
    arc = (d > r - 18) & (d < r - 10) & (ang > 0.2) & (ang < 2.6)
    img[arc] = np.array([0.35, 0.75, 0.45])
    red = (d > r - 18) & (d < r - 10) & (ang > -0.4) & (ang <= 0.2)
    img[red] = np.array([0.85, 0.30, 0.25])
    nd = np.abs((xx - cx) * np.sin(-0.15) - (yy - cy) * np.cos(-0.15))
    needle = (nd < 2.2) & (d < r - 12) & ((xx - cx) * np.cos(-0.15) + (yy - cy) * np.sin(-0.15) > 0)
    img[needle] = np.array([0.95, 0.95, 0.95])
    # glass taskbar
    tb = 40
    y0 = h - tb
    bar = img[y0:h].copy()
    grad = np.linspace(0.0, 1.0, tb)[:, None, None]
    img[y0:h] = bar * 0.35 + (np.array([0.15, 0.22, 0.30]) * (1 - grad) + np.array([0.06, 0.10, 0.15]) * grad) * 0.65
    img[y0:y0 + 1] = np.array([0.62, 0.72, 0.82])
    img[y0 + 1:y0 + tb // 2] += 0.05
    # round start orb (no logo)
    ocx, ocy, orr = 30, h - tb // 2, 17
    d = np.sqrt((xx - ocx) ** 2 + (yy - ocy) ** 2)
    orb = d < orr
    shade = np.clip(1.0 - (yy - (ocy - orr)) / (2 * orr), 0, 1)
    img[orb] = (np.array([0.10, 0.36, 0.62]) * (0.6 + 0.6 * shade[..., None]))[orb]
    hl = (np.sqrt((xx - ocx) ** 2 + ((yy - (ocy - 6)) * 1.6) ** 2) < 10) & orb
    img[hl] = img[hl] * 0.5 + 0.5
    # pinned buttons + one open window
    for i, col in enumerate([(0.93, 0.80, 0.42), (0.45, 0.70, 0.85), (0.95, 0.55, 0.25)]):
        x0 = 62 + i * 58
        box_(x0, y0 + 4, x0 + 52, h - 4, (0.75, 0.85, 0.95), 0.18 if i == 1 else 0.08)
        box_(x0 + 16, y0 + 10, x0 + 36, h - 10, col)
    # tray
    box_(w - 150, y0 + 2, w, h, (0.02, 0.05, 0.09), 0.35)
    for i in range(4):
        box_(w - 140 + i * 18, y0 + 14, w - 128 + i * 18, y0 + 26, (0.80, 0.85, 0.90), 0.7)
    box_(w - 62, y0 + 12, w - 14, y0 + 17, (0.92, 0.94, 0.96), 0.9)
    box_(w - 58, y0 + 23, w - 18, y0 + 28, (0.92, 0.94, 0.96), 0.7)

    img = np.clip(img, 0, 1)[::-1]                          # Blender pixel rows start at the bottom
    rgba_ = np.concatenate([img, np.ones((h, w, 1), np.float32)], axis=2).astype(np.float32)
    im = bpy.data.images.new("screen_placeholder", w, h, alpha=False)
    im.pixels.foreach_set(rgba_.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


SCREEN = {}


def screen_material(path):
    img = bpy.data.images.load(path, check_existing=True)
    m = bpy.data.materials.new("screen")
    m.use_nodes = True
    nt = m.node_tree
    b = principled(m)
    b.inputs["Base Color"].default_value = rgba("#050506")
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.4
    b.inputs["Coat Roughness"].default_value = 0.03
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.interpolation = "Cubic"
    tx.extension = "EXTEND"
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    SCREEN.update(img=img, bsdf=b, tex=tx)
    return m


# ================================================================ the room
def build_room(M):
    use("SET")
    # diorama plinth and floorboards (running into the room, toward the desk)
    boxmm("plinth", (-WT - 0.06, -0.09, -0.24), (W + 0.06, D + WT + 0.03, -0.03), M["plinth"], bev=0.02, seg=3)
    pw, x = 0.16, -WT
    i = 0
    while x < W - 0.001:
        x1 = min(x + pw, W)
        cut = RNG.uniform(0.5, 2.3)
        for j, (y0, y1) in enumerate([(-0.07, cut), (cut, D + 0.02)]):
            dz = RNG.uniform(-0.0015, 0.0015)
            boxmm(f"floorboard_{i}_{j}", (x + 0.0015, y0 + 0.0015, -0.03), (x1 - 0.0015, y1 - 0.0015, dz),
                  M[f"floor{RNG.randrange(4)}"], bev=0.004, seg=1)
        x, i = x1, i + 1

    # walls
    dx0, dx1, dtop = DOOR
    wy0, wy1, wz0, wz1 = WIN
    walls = [
        ((-WT, D, 0), (dx0, D + WT, H)), ((dx1, D, 0), (W, D + WT, H)), ((dx0, D, dtop), (dx1, D + WT, H)),
        ((-WT, 0, 0), (0, wy0, H)), ((-WT, wy1, 0), (0, D, H)), ((-WT, wy0, 0), (0, wy1, wz0)),
        ((-WT, wy0, wz1), (0, wy1, H)),
    ]
    for k, (a, b) in enumerate(walls):
        boxmm(f"wall_{k}", a, b, M["wall"], bev=0)
    # diorama section caps (the cut edges of the model, painted dark)
    boxmm("cap_back", (-WT, D, H), (W, D + WT, H + 0.008), M["section"], bev=0)
    boxmm("cap_left", (-WT, -0.008, H), (0, D, H + 0.008), M["section"], bev=0)
    boxmm("cap_left_front", (-WT, -0.008, -0.03), (0, 0, H + 0.008), M["section"], bev=0)
    boxmm("cap_back_end", (W, D, -0.03), (W + 0.008, D + WT, H + 0.008), M["section"], bev=0)
    # invisible ceiling: casts shadows (so window light only enters through the window), never seen by camera
    for nm, a, b in [("shadow_ceiling", (-WT, -0.3, H + 0.012), (W + 0.3, 6.3, H + 0.05)),
                     ("shadow_front", (-WT, -0.34, 0.0), (W + 0.3, -0.3, H + 0.05)),
                     ("shadow_right", (W + 0.26, -0.3, 0.0), (W + 0.3, D + WT, H + 0.05))]:
        blk = boxmm(nm, a, b, M["section"], bev=0)
        blk.visible_camera = False
        blk.visible_diffuse = False
        blk.visible_glossy = False
        blk.visible_transmission = False

    # tongue-and-groove dado panelling, rail and skirting
    x = 0.0
    k = 0
    while x < W - 0.05:
        if not (dx0 - 0.09 < x + 0.095 and x < dx1 + 0.09):
            boxmm(f"tg_back_{k}", (x, D - 0.012, 0), (x + 0.093, D, 0.98), M["panel"], bev=0.003, seg=1)
        x += 0.095
        k += 1
    y = 0.0
    k = 0
    while y < D - 0.05:
        boxmm(f"tg_left_{k}", (0, y, 0), (0.012, min(y + 0.093, D - 0.012), 0.98), M["panel"], bev=0.003, seg=1)
        y += 0.095
        k += 1
    for nm, a, b in [("rail_bL", (0, D - 0.032, 0.965), (dx0 - 0.085, D, 1.01)),
                     ("rail_bR", (dx1 + 0.085, D - 0.032, 0.965), (W, D, 1.01)),
                     ("rail_L", (0, 0, 0.965), (0.032, D - 0.032, 1.01)),
                     ("skirt_bL", (0, D - 0.03, 0), (dx0 - 0.085, D, 0.1)),
                     ("skirt_bR", (dx1 + 0.085, D - 0.03, 0), (W, D, 0.1)),
                     ("skirt_L", (0, 0, 0), (0.03, D - 0.03, 0.1))]:
        boxmm(nm, a, b, M["trim"], bev=0.006, seg=2)

    # doorway: architrave, linings, threshold
    for nm, a, b in [("door_cas_L", (dx0 - 0.085, D - 0.024, 0), (dx0, D, dtop + 0.085)),
                     ("door_cas_R", (dx1, D - 0.024, 0), (dx1 + 0.085, D, dtop + 0.085)),
                     ("door_cas_T", (dx0 - 0.085, D - 0.024, dtop), (dx1 + 0.085, D, dtop + 0.095)),
                     ("door_lin_L", (dx0, D, 0), (dx0 + 0.022, D + WT, dtop)),
                     ("door_lin_R", (dx1 - 0.022, D, 0), (dx1, D + WT, dtop)),
                     ("door_lin_T", (dx0, D, dtop - 0.022), (dx1, D + WT, dtop))]:
        boxmm(nm, a, b, M["trim"], bev=0.006, seg=2)
    boxmm("threshold", (dx0, D - 0.012, -0.002), (dx1, D + WT + 0.012, 0.012), M["oak_y"], bev=0.004)

    # window: board, linings, architrave, sash with glazing bars, glass
    for nm, a, b in [("win_board", (-WT, wy0 - 0.05, wz0 - 0.032), (0.07, wy1 + 0.05, wz0)),
                     ("win_apron", (0, wy0 - 0.04, wz0 - 0.11), (0.02, wy1 + 0.04, wz0 - 0.032)),
                     ("win_lin_A", (-WT, wy0, wz0), (0, wy0 + 0.02, wz1)),
                     ("win_lin_B", (-WT, wy1 - 0.02, wz0), (0, wy1, wz1)),
                     ("win_lin_T", (-WT, wy0, wz1 - 0.02), (0, wy1, wz1)),
                     ("win_cas_A", (0, wy0 - 0.075, wz0), (0.022, wy0, wz1 + 0.075)),
                     ("win_cas_B", (0, wy1, wz0), (0.022, wy1 + 0.075, wz1 + 0.075)),
                     ("win_cas_T", (0, wy0 - 0.075, wz1), (0.022, wy1 + 0.075, wz1 + 0.085))]:
        boxmm(nm, a, b, M["trim"], bev=0.006, seg=2)
    zm, ym = (wz0 + wz1) / 2, (wy0 + wy1) / 2
    fx0, fx1 = -0.09, -0.05
    for nm, a, b in [("sash_bot", (fx0, wy0, wz0), (fx1, wy1, wz0 + 0.055)),
                     ("sash_top", (fx0, wy0, wz1 - 0.04), (fx1, wy1, wz1)),
                     ("sash_A", (fx0, wy0, wz0), (fx1, wy0 + 0.045, wz1)),
                     ("sash_B", (fx0, wy1 - 0.045, wz0), (fx1, wy1, wz1)),
                     ("sash_meet", (fx0 - 0.01, wy0, zm - 0.022), (fx1 + 0.012, wy1, zm + 0.022)),
                     ("sash_bar", (fx0 + 0.008, ym - 0.011, wz0), (fx1 - 0.008, ym + 0.011, wz1))]:
        boxmm(nm, a, b, M["trim"], bev=0.005, seg=2)
    sash_lock = cyl("sash_lock", 0.012, 0.01, (fx1 + 0.016, ym, zm + 0.022), M["brass"], base=True)
    glass = boxmm("glass", (-0.072, wy0, wz0), (-0.068, wy1, wz1), M["glass"], bev=0)
    no_shadow(glass, sash_lock)

    # cast-iron column radiator under the window
    ry0 = ym - 0.36
    for c in range(12):
        yy = ry0 + c * 0.062
        boxmm(f"rad_col{c}", (0.035, yy, 0.17), (0.105, yy + 0.05, 0.72), M["radiator"], bev=0.016, seg=2)
    for zz in (0.2, 0.69):
        cyl(f"rad_hdr{zz}", 0.018, 0.74, (0.07, ym, zz), M["radiator"], rot=(90, 0, 0), n=10)
    tube("rad_pipe", (0.06, ry0 - 0.04, 0.2), (0.06, ry0 - 0.04, 0.0), 0.011, M["radiator"])
    cyl("rad_valve", 0.016, 0.03, (0.06, ry0 - 0.04, 0.21), M["brass_old"], n=10, base=True)


def build_outside(M):
    """What's seen through the window: a card-like alley (kept below the wall tops so the diorama silhouette
    stays clean), the building opposite with one lit window, a strip of sky, rain at night."""
    use("SET")
    wy0, wy1, wz0, wz1 = WIN
    xb, ya, yb = -0.62, 1.02, 3.4
    wall = boxmm("opp_wall", (xb - 0.1, ya, -0.3), (xb, yb, 1.95), M["outside_brick"], bev=0)
    sky = boxmm("opp_sky", (xb - 0.12, ya, 1.95), (xb - 0.1, yb, H - 0.02), M["outside_sky"], bev=0)
    sill = boxmm("opp_sill", (xb - 0.02, 2.05, 1.12), (xb + 0.03, 2.55, 1.15), M["outside_brick"], bev=0.004)
    win = boxmm("opp_window", (xb - 0.005, 2.1, 1.16), (xb + 0.002, 2.5, 1.62), M["outside_win"], bev=0)
    frame = []
    for nm, a, b in [("opp_frame_v", (xb - 0.004, 2.295, 1.16), (xb + 0.006, 2.305, 1.62)),
                     ("opp_frame_h", (xb - 0.004, 2.1, 1.385), (xb + 0.006, 2.5, 1.395))]:
        frame.append(boxmm(nm, a, b, M["section"], bev=0))
    pipe = cyl("opp_downpipe", 0.022, 2.3, (xb + 0.03, 0.75, 0.85), M["section"], n=8)
    roof = boxmm("opp_gutter", (xb - 0.02, ya, 1.93), (xb + 0.06, yb, 1.97), M["section"], bev=0.005)
    ground = boxmm("alley", (xb, ya, -0.3), (-WT, yb, 0.6), M["section"], bev=0)
    no_shadow(wall, sky, sill, win, pipe, roof, ground, *frame)

    use("NIGHT")
    bm = bmesh.new()
    for _ in range(170):
        r = RNG.uniform(0.0012, 0.0032) if RNG.random() < 0.85 else RNG.uniform(0.0035, 0.0055)
        streak = RNG.random() < 0.12
        geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        vs = geom["verts"]
        sz = RNG.uniform(2.5, 6.0) if streak else RNG.uniform(1.0, 1.3)
        y = RNG.uniform(wy0 + 0.04, wy1 - 0.04)
        z = RNG.uniform(wz0 + 0.06, wz1 - 0.04)
        for v in vs:
            v.co.x *= 0.35
            v.co.z *= sz
            v.co += Vector((-0.075, y, z))
    for _ in range(16):                                      # rivulets running down the pane
        y = RNG.uniform(wy0 + 0.05, wy1 - 0.05)
        z = RNG.uniform(wz0 + 0.25, wz1 - 0.05)
        ln = RNG.uniform(0.08, 0.3)
        prev = None
        for k in range(7):
            zz = z - ln * k / 6
            yy = y + 0.004 * sin(k * 1.7 + y * 40)
            w = 0.0011 * (1.25 - k / 8)
            vs = (bm.verts.new((-0.0745, yy - w, zz)), bm.verts.new((-0.0745, yy + w, zz)))
            if prev:
                bm.faces.new((prev[0], prev[1], vs[1], vs[0]))
            prev = vs
    drops = finish("rain_drops", bm, M["water"], angle=80)
    bm = bmesh.new()
    for _ in range(90):
        x = RNG.uniform(xb + 0.05, -0.18)
        y = RNG.uniform(wy0 - 0.3, wy1 + 0.6)
        z = RNG.uniform(0.7, 2.3)
        ln = RNG.uniform(0.05, 0.11)
        v = [bm.verts.new(p) for p in ((x, y - 0.0008, z), (x, y + 0.0008, z), (x, y + 0.0008, z + ln),
                                       (x, y - 0.0008, z + ln))]
        bm.faces.new(v)
    rain = finish("rain_streaks", bm, M["rain"], smooth=False)
    no_shadow(drops, rain)


# ================================================================ the workshop, glimpsed through the doorway
def wheel(name, parent, loc, R=0.33, m_rim=None, M=None, spokes=24, axis_y=True):
    g = grp(name, loc, (90, 0, 0) if axis_y else (0, 0, 0), parent=parent)
    torus(name + "_tyre", R, 0.017, m=M["tyre"], nR=32, nr=8, parent=g)
    torus(name + "_rim", R - 0.02, 0.008, m=m_rim or M["steel"], nR=32, nr=6, parent=g)
    cyl(name + "_hub", 0.018, 0.08, m=M["steel"], n=10, parent=g)
    for i in range(spokes):
        a = 2 * pi * i / spokes
        side = 0.03 if i % 2 else -0.03
        tube(f"{name}_sp{i}", (0.015 * cos(a), 0.015 * sin(a), side),
             ((R - 0.025) * cos(a + 0.18), (R - 0.025) * sin(a + 0.18), 0), 0.0012, M["steel"], n=4, parent=g)
    return g


def bike(name, loc, yaw, frame_m, M, lift=0.0):
    g = grp(name, (loc[0], loc[1], loc[2] + lift), (0, 0, yaw))
    R = 0.34
    rear, front = Vector((-0.5, 0, R)), Vector((0.52, 0, R))
    bb = Vector((-0.06, 0, 0.3))
    st = Vector((-0.2, 0, 0.86))
    ht, hb = Vector((0.36, 0, 0.84)), Vector((0.4, 0, 0.7))
    t = 0.017
    for nm, a, b, r in [("seat", bb, st, t), ("top", st, ht, t), ("down", bb, hb, t * 1.2), ("head", hb, ht + Vector((-0.01, 0, 0.04)), t * 1.25)]:
        tube(f"{name}_{nm}", a, b, r, frame_m, n=10, parent=g)
    for s in (-0.055, 0.055):
        tube(f"{name}_cs{s}", bb + Vector((0, s * 0.5, 0)), rear + Vector((0, s, 0)), 0.01, frame_m, n=8, parent=g)
        tube(f"{name}_ss{s}", st + Vector((0, s * 0.3, -0.05)), rear + Vector((0, s, 0)), 0.009, frame_m, n=8, parent=g)
        tube(f"{name}_fk{s}", hb + Vector((0, s * 0.6, 0)), front + Vector((0, s * 0.8, 0)), 0.011, M["steel_dk"], n=8, parent=g)
    tube(f"{name}_post", st, st + Vector((-0.04, 0, 0.14)), 0.012, M["steel"], n=8, parent=g)
    prism(f"{name}_saddle", [(-0.13, -0.03), (0.08, -0.012), (0.12, 0), (0.08, 0.012), (-0.13, 0.03), (-0.15, 0)],
          0.035, loc=st + Vector((-0.03, 0, 0.13)), m=M["saddle"], bev=0.008, parent=g)
    stem = ht + Vector((0.0, 0, 0.06))
    tube(f"{name}_stem", ht, stem + Vector((0.07, 0, 0.0)), 0.012, M["steel"], n=8, parent=g)
    tube(f"{name}_bar", stem + Vector((0.07, -0.22, 0)), stem + Vector((0.07, 0.22, 0)), 0.012, M["steel_dk"], n=8, parent=g)
    for s in (-0.2, 0.2):
        tube(f"{name}_grip{s}", stem + Vector((0.07, s, 0)), stem + Vector((0.07, s * 1.12, 0)), 0.016, M["rubber"], n=8, parent=g)
    wheel(f"{name}_wr", g, rear, R - 0.02, M=M)
    wheel(f"{name}_wf", g, front, R - 0.02, M=M)
    teeth = 32
    pts = []
    for k in range(teeth):
        a = 2 * pi * k / teeth
        for da, rr in ((-0.035, 0.092), (-0.012, 0.1), (0.012, 0.1), (0.035, 0.092)):
            pts.append(((rr) * cos(a + da), (rr) * sin(a + da)))
    inner = [(0.03 * x / math.hypot(x, y), 0.03 * y / math.hypot(x, y)) for x, y in pts]
    annulus(f"{name}_ring", pts, inner, thick=0.004, m=M["steel"], parent=g, loc=bb + Vector((0, -0.07, 0)),
            rot=(90, 0, 0))
    tube(f"{name}_crank", bb + Vector((0, -0.08, 0)), bb + Vector((0.12, -0.08, -0.12)), 0.009, M["steel"], n=6, parent=g)
    box(f"{name}_pedal", (0.05, 0.09, 0.015), bb + Vector((0.12, -0.13, -0.12)), M["plastic_blk"], parent=g)
    return g


def tool_shape(name, parent, kind, x, z, M, col=None):
    y = -0.012
    if kind == "spanner":
        L = col or 0.2
        boxmm(name + "_h", (x - 0.006, y - 0.004, z - L / 2), (x + 0.006, y, z + L / 2), M["chrome"], bev=0.002, parent=parent)
        cyl(name + "_e1", 0.016, 0.004, (x, y - 0.002, z + L / 2), M["chrome"], rot=(90, 0, 0), n=12, parent=parent)
        torus(name + "_e2", 0.011, 0.004, (x, y - 0.002, z - L / 2), M["chrome"], rot=(90, 0, 0), nR=12, nr=6, parent=parent)
    elif kind == "driver":
        cyl(name + "_h", 0.012, 0.09, (x, y - 0.014, z + 0.04), col or M["pin_red"], n=8, bev=0.004, parent=parent)
        cyl(name + "_s", 0.003, 0.12, (x, y - 0.014, z - 0.06), M["chrome"], n=6, parent=parent)
    elif kind == "lever":
        boxmm(name, (x - 0.008, y - 0.005, z - 0.06), (x + 0.008, y, z + 0.06), col or M["pin_blue"], bev=0.003, parent=parent)
    elif kind == "hammer":
        cyl(name + "_h", 0.011, 0.28, (x, y - 0.014, z), M["oak_lt"], n=8, parent=parent)
        box(name + "_hd", (0.1, 0.025, 0.03), (x, y - 0.014, z + 0.15), M["steel_dk"], bev=0.004, parent=parent)
    tube(name + "_hook", (x, y, z + 0.11), (x, 0.0, z + 0.11), 0.002, M["steel"], n=6, parent=parent)


def build_workshop(M):
    use("WORKSHOP")
    y0, y1, x0, x1 = D + WT, 6.0, 1.35, W
    boxmm("ws_floor", (x0, y0, -0.06), (x1, y1, 0.0), M["concrete"], bev=0)
    boxmm("ws_back", (x0, y1, 0), (x1, y1 + 0.12, WS_H), M["ws_brick"], bev=0)
    boxmm("ws_left", (x0 - 0.12, y0, 0), (x0, y1, WS_H), M["ws_brick"], bev=0)
    boxmm("ws_right", (x1, y0, 0), (x1 + 0.12, y1, WS_H), M["ws_brick"], bev=0)
    boxmm("ws_ceiling", (x0 - 0.12, y0, WS_H), (x1 + 0.12, y1 + 0.12, WS_H + 0.05), M["ws_brick"], bev=0)

    # pegboard with shadow-board tools, workbench, vice, truing stand, radio, strip light
    pb = grp("pegboard_g", (0, y1 - 0.01, 0))
    boxmm("pegboard", (2.2, -0.012, 0.98), (3.75, 0.0, 1.95), M["pegboard"], bev=0.003, parent=pb)
    tools = [("spanner", 2.32, 1.55, 0.16), ("spanner", 2.38, 1.55, 0.19), ("spanner", 2.44, 1.55, 0.22),
             ("driver", 2.56, 1.5, M["pin_red"]), ("driver", 2.62, 1.5, M["pin_yellow"]),
             ("driver", 2.68, 1.5, M["pin_blue"]), ("hammer", 2.82, 1.45, None), ("lever", 3.02, 1.6, M["pin_blue"]),
             ("lever", 3.05, 1.6, M["pin_yellow"]), ("lever", 3.08, 1.6, M["pin_blue"]),
             ("spanner", 3.25, 1.5, 0.26), ("spanner", 3.32, 1.5, 0.24)]
    for i, (k, x, z, c) in enumerate(tools):
        tool_shape(f"tool{i}", pb, k, x, z, M, c)
    # inner tube hanging on the pegboard
    torus("inner_tube", 0.2, 0.011, (3.56, y1 - 0.04, 1.55), M["tyre"], rot=(90, 0, 0), nR=28, nr=6,
          scale=(0.55, 1.0, 1.0))
    tube("tube_hook", (3.56, y1 - 0.01, 1.74), (3.56, y1 - 0.06, 1.74), 0.004, M["steel"])
    # bench
    boxmm("bench_top", (2.05, y1 - 0.62, 0.86), (3.85, y1 - 0.02, 0.92), M["oak_lt"], bev=0.008)
    for bx in (2.1, 3.78):
        for by in (y1 - 0.58, y1 - 0.08):
            boxmm(f"bench_leg{bx}{by}", (bx - 0.03, by - 0.03, 0), (bx + 0.03, by + 0.03, 0.86), M["oak_lt"], bev=0.005)
    boxmm("bench_shelf", (2.08, y1 - 0.6, 0.2), (3.82, y1 - 0.04, 0.23), M["oak_lt"], bev=0.004)
    boxmm("vice", (2.15, y1 - 0.66, 0.92), (2.3, y1 - 0.5, 1.0), M["teal"], bev=0.008)
    # truing stand with a wheel (Priya's wheel builds come later)
    ts = grp("truing", (2.9, y1 - 0.3, 0.92))
    boxmm("ts_base", (-0.12, -0.06, 0), (0.12, 0.06, 0.03), M["steel_dk"], bev=0.005, parent=ts)
    for s in (-0.07, 0.07):
        boxmm(f"ts_arm{s}", (s - 0.012, -0.012, 0.03), (s + 0.012, 0.012, 0.42), M["steel_dk"], bev=0.003, parent=ts)
    wheel("ts_wheel", ts, (0, 0, 0.4), 0.3, M=M, axis_y=False).rotation_euler = _rot((0, 90, 0))
    # radio
    rd = grp("radio", (3.5, y1 - 0.25, 0.92), (0, 0, -8))
    box("radio_body", (0.3, 0.1, 0.17), (0, 0, 0.085), M["counter_paint"], bev=0.012, parent=rd)
    gr = rect("radio_grille", -0.13, 0.02, -0.02, 0.15, 0.0, M["hole"], rd)
    gr.rotation_euler = _rot((90, 0, 0))
    gr.location = (0, -0.0505, 0)
    box("radio_dial", (0.1, 0.004, 0.04), (0.07, -0.051, 0.11), M["radio_dial"], bev=0, parent=rd)
    for kx in (0.04, 0.1):
        cyl(f"radio_knob{kx}", 0.012, 0.012, (kx, -0.055, 0.045), M["plastic_blk"], rot=(90, 0, 0), n=10, parent=rd)
    tube("radio_ant", (0.12, 0.0, 0.17), (0.02, 0.05, 0.5), 0.0025, M["chrome"], parent=rd)
    # strip light over the bench
    boxmm("strip_housing", (2.5, y1 - 0.09, 2.18), (3.7, y1 - 0.01, 2.24), M["trim"], bev=0.008)
    st = cyl("strip_tube", 0.016, 1.14, (3.1, y1 - 0.06, 2.165), M["tube"], rot=(0, 90, 0), n=10)
    no_shadow(st)
    # a work lamp clamped to the bench (Martin working late)
    boxmm("worklamp_clamp", (3.25, y1 - 0.62, 0.86), (3.29, y1 - 0.56, 0.95), M["steel_dk"], bev=0.003)
    tube("worklamp_arm", (3.27, y1 - 0.59, 0.95), (3.1, y1 - 0.95, 1.6), 0.008, M["steel_dk"])
    wl = lathe("worklamp_shade", [(0.0, 0.05), (0.03, 0.05), (0.07, -0.04), (0.065, -0.042), (0.027, 0.04), (0.0, 0.04)],
               n=14, loc=(3.1, y1 - 0.98, 1.62), m=[M["steel_dk"]])
    aim(wl, (2.95, 4.5, 0.9))

    # the bike on the repair stand (side-on to the doorway) and one waiting against the wall
    stand = grp("repair_stand", (2.84, 4.92, 0))
    for k in range(3):
        a = 2 * pi * k / 3 + 0.4
        tube(f"stand_leg{k}", (0, 0, 0.35), (0.38 * cos(a), 0.38 * sin(a), 0.0), 0.014, M["steel_dk"], parent=stand)
    tube("stand_post", (0, 0, 0.0), (0, 0, 1.24), 0.02, M["steel_dk"], parent=stand)
    tube("stand_arm", (0, 0, 1.24), (0.0, -0.33, 1.27), 0.016, M["steel_dk"], parent=stand)
    box("stand_clamp", (0.06, 0.07, 0.08), (0.0, -0.36, 1.27), M["pin_red"], bev=0.01, parent=stand)
    bike("bike_stand", (3.06, 4.55, 0.0), 0, M["teal"], M, lift=0.33)
    bike("bike_wall", (2.15, 5.3, 0.0), 180, M["bikered"], M)

    # the counter at the doorway, the brass service bell and its card
    cx0, cx1, cy0, cy1 = 2.95, 3.9, 3.38, 3.88
    boxmm("counter_body", (cx0, cy0 + 0.02, 0), (cx1, cy1, 0.92), M["counter_paint"], bev=0.01)
    boxmm("counter_top", (cx0 - 0.03, cy0, 0.92), (cx1, cy1 + 0.03, 0.96), M["oak_y"], bev=0.01, seg=3)
    for k in range(3):
        boxmm(f"counter_panel{k}", (cx0 + 0.05 + k * 0.3, cy0 + 0.012, 0.15), (cx0 + 0.3 + k * 0.3, cy0 + 0.02, 0.8),
              M["counter_paint"], bev=0.006)
    bell = grp("service_bell", (3.12, 3.62, 0.96))
    lathe("bell_base", [(0.0, 0.0), (0.046, 0.0), (0.048, 0.006), (0.046, 0.016), (0.0, 0.016)], n=24,
          m=M["oak"], parent=bell)
    lathe("bell_dome", [(0.0, 0.058), (0.012, 0.0565), (0.024, 0.052), (0.033, 0.043), (0.039, 0.031),
                        (0.041, 0.018), (0.0, 0.018)], n=24, m=M["brass"], parent=bell)
    cyl("bell_stem", 0.004, 0.02, (0, 0, 0.065), M["brass"], n=8, parent=bell)
    sphere("bell_knob", 0.0075, (0, 0, 0.078), M["brass"], seg=10, rings=6, parent=bell)
    tc = grp("bell_card", (3.25, 3.6, 0.96), (0, 0, -12))
    for s in (1, -1):
        p = boxmm(f"card_side{s}", (-0.05, -0.0008, 0), (0.05, 0.0008, 0.07), M["paper"], bev=0, parent=tc)
        p.location = (0, s * 0.012, 0.0)
        p.rotation_euler = _rot((s * 10, 0, 0))
        text(f"card_text{s}", "RING FOR\nSERVICE", "georgiab.ttf", 0.013, (0, -0.0012 if s > 0 else 0.0012, 0.035),
             M["ink"], rot=(90, 0, 0 if s > 0 else 180), parent=p, line=0.9)


# ================================================================ the desk and the PC
def build_desk(M):
    use("SET")
    boxmm("desk_top", (0.22, 2.06, DZ - 0.045), (2.2, D - 0.005, DZ), M["oak"], bev=0.012, seg=3)
    boxmm("desk_leg_L", (0.245, 2.1, 0), (0.29, D - 0.04, DZ - 0.045), M["oak"], bev=0.008)
    px0, px1 = 1.76, 2.17
    boxmm("desk_ped", (px0, 2.1, 0.02), (px1, D - 0.04, DZ - 0.045), M["oak"], bev=0.008)
    boxmm("desk_back", (0.29, D - 0.06, 0.32), (px0, D - 0.04, DZ - 0.045), M["oak"], bev=0.004)
    for i, (z0, z1) in enumerate([(0.48, 0.68), (0.27, 0.46), (0.05, 0.25)]):
        dy = -0.022 if i == 1 else 0.0                       # drawer 2 (the backup drawer) left ajar
        boxmm(f"desk_drawer{i}", (px0 + 0.014, 2.083 + dy, z0), (px1 - 0.014, 2.1 + dy, z1), M["oak_lt"], bev=0.005)
        cyl(f"desk_pull{i}", 0.006, 0.11, ((px0 + px1) / 2, 2.066 + dy, z1 - 0.045), M["brass_old"], rot=(0, 90, 0), n=8)
        for sx in (-0.05, 0.05):
            tube(f"desk_pullpost{i}{sx}", ((px0 + px1) / 2 + sx, 2.066 + dy, z1 - 0.045),
                 ((px0 + px1) / 2 + sx, 2.084 + dy, z1 - 0.045), 0.004, M["brass_old"], n=6)


def build_chair(M):
    use("SET")
    g = grp("chair", (1.66, 1.55, 0), (0, 0, 58))
    for i in range(5):
        a = 2 * pi * i / 5 + 0.3
        tube(f"chair_leg{i}", (0, 0, 0.1), (0.3 * cos(a), 0.3 * sin(a), 0.065), 0.018, M["plastic_blk"], parent=g)
        sphere(f"chair_caster{i}", 0.028, (0.3 * cos(a), 0.3 * sin(a), 0.03), M["plastic_blk"], seg=10, rings=6,
               parent=g, scale=(0.7, 1.0, 1.0))
    cyl("chair_hub", 0.045, 0.06, (0, 0, 0.1), M["plastic_blk"], n=12, parent=g)
    cyl("chair_lift", 0.024, 0.3, (0, 0, 0.27), M["chrome"], n=12, parent=g)
    box("chair_mech", (0.22, 0.22, 0.04), (0, 0, 0.43), M["plastic_blk"], bev=0.01, parent=g)
    box("chair_seat", (0.48, 0.46, 0.08), (0, 0.02, 0.48), M["fabric"], bev=0.034, seg=3, parent=g)
    box("chair_spine", (0.06, 0.03, 0.34), (0, -0.25, 0.6), M["plastic_blk"], rot=(-8, 0, 0), bev=0.008, parent=g)
    box("chair_back", (0.44, 0.07, 0.5), (0, -0.27, 0.86), M["fabric"], rot=(-9, 0, 0), bev=0.034, seg=3, parent=g)
    for s in (-1, 1):
        box(f"chair_armpost{s}", (0.03, 0.04, 0.2), (s * 0.24, 0.0, 0.58), M["plastic_blk"], bev=0.006, parent=g)
        box(f"chair_armpad{s}", (0.06, 0.26, 0.03), (s * 0.24, 0.02, 0.69), M["plastic_blk"], bev=0.012, parent=g)


def build_tower(M):
    use("SET")
    w, d, h = 0.19, 0.45, 0.42
    g = grp("tower", (0.37, 2.535, DZ))
    box("tower_case", (w, d, h), (0, 0, h / 2 + 0.008), M["pc"], bev=0.007, parent=g)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"tower_foot{sx}{sy}", 0.012, 0.008, (sx * 0.07, sy * 0.19, 0.0), M["rubber"], n=8, base=True, parent=g)
    fy = -d / 2 - 0.016
    box("tower_bezel", (w - 0.004, 0.02, h - 0.006), (0, -d / 2 - 0.006, h / 2 + 0.008), M["pc_dk"], bev=0.008, parent=g)
    box("tower_odd", (0.15, 0.006, 0.042), (0, fy, h - 0.045), M["gloss"], bev=0.002, parent=g)
    box("tower_odd_seam", (0.13, 0.002, 0.0015), (0, fy - 0.003, h - 0.058), M["hole"], bev=0, parent=g)
    box("tower_eject", (0.012, 0.004, 0.006), (0.058, fy - 0.003, h - 0.06), M["steel_dk"], bev=0.001, parent=g)
    box("tower_bay2", (0.15, 0.006, 0.042), (0, fy, h - 0.095), M["pc_dk"], bev=0.002, parent=g)
    cyl("tower_power", 0.012, 0.008, (0, fy - 0.002, h - 0.165), M["gloss"], rot=(90, 0, 0), n=20, parent=g)
    torus("tower_power_ring", 0.0135, 0.0016, (0, fy - 0.004, h - 0.165), M["led_blue"], rot=(90, 0, 0), nR=20, nr=6, parent=g)
    box("tower_hdd_led", (0.006, 0.002, 0.003), (0.035, fy - 0.003, h - 0.198), M["led_amber"], bev=0, parent=g)
    for i in range(2):
        box(f"tower_usb{i}", (0.014, 0.003, 0.006), (-0.014 + i * 0.028, fy - 0.002, h - 0.225), M["hole"], bev=0, parent=g)
    for i in range(10):
        box(f"tower_vent{i}", (0.13, 0.003, 0.0045), (0, fy - 0.001, 0.045 + i * 0.012), M["hole"], bev=0, parent=g)
    # worn stickers, no brand marks: a spec sticker, an "energy" sticker, a service-tag barcode
    box("sticker_spec", (0.034, 0.0006, 0.026), (0.05, fy - 0.003, 0.19), M["steel"], bev=0, parent=g)
    box("sticker_spec_in", (0.014, 0.0006, 0.012), (0.042, fy - 0.0035, 0.193), M["pin_blue"], bev=0, parent=g)
    box("sticker_energy", (0.026, 0.0006, 0.018), (0.05, fy - 0.003, 0.162), M["pin_white"], bev=0, parent=g)
    disc("sticker_star", 0, 0, 0.006, 0, M["pin_blue"], g, n=5, loc=(0.05, fy - 0.0037, 0.162), rot=(90, 0, 0))
    side = grp("tower_side_tag", (w / 2 + 0.0004, 0.08, 0.3), (90, 0, 90), parent=g)
    rect("tag_bg", -0.04, -0.015, 0.04, 0.015, 0, M["pin_white"], side)
    for i in range(22):
        x = -0.034 + i * 0.0031
        rect(f"tag_bar{i}", x, -0.006, x + (0.0012 if i % 3 else 0.002), 0.01, 0.0002, M["ink"], side)


def build_monitor(M, screen_m):
    use("SET")
    g = grp("monitor", (1.0, 2.53, DZ))
    lathe("mon_base", [(0.0, 0.0), (0.11, 0.0), (0.113, 0.006), (0.105, 0.014), (0.0, 0.016)], n=28, m=M["gloss"],
          parent=g).scale = (1.0, 0.72, 1.0)
    box("mon_neck", (0.06, 0.024, 0.19), (0, 0.025, 0.105), M["gloss"], rot=(-6, 0, 0), bev=0.008, parent=g)
    head = grp("monitor_head", (0, 0.0, 0.245), (-5, 0, 0), parent=g)
    aw, ah = 0.408, 0.255
    bs, bt, bb, dep = 0.022, 0.022, 0.034, 0.024
    ow = aw + 2 * bs
    yz = -0.018
    box("bezel_top", (ow, dep, bt), (0, yz, ah / 2 + bt / 2), M["gloss"], bev=0.006, parent=head)
    box("bezel_bot", (ow, dep, bb), (0, yz, -ah / 2 - bb / 2), M["gloss"], bev=0.006, parent=head)
    for s in (-1, 1):
        box(f"bezel_side{s}", (bs, dep, ah + 0.002), (s * (aw / 2 + bs / 2), yz, 0), M["gloss"], bev=0.006, parent=head)
    box("mon_backplate", (ow - 0.01, 0.012, ah + bt + bb - 0.01), (0, -0.002, -0.006), M["gloss"], bev=0.004, parent=head)
    box("mon_hump", (0.34, 0.04, 0.22), (0, 0.022, -0.01), M["pc"], bev=0.018, seg=3, parent=head)
    # the emissive screen (UV-mapped plane facing -y)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(p) for p in ((-aw / 2, 0, -ah / 2), (aw / 2, 0, -ah / 2), (aw / 2, 0, ah / 2), (-aw / 2, 0, ah / 2))]
    f = bm.faces.new(vs)
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = t
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    scr = finish("screen", bm, screen_m, head, (0, yz - dep / 2 + 0.004, 0), smooth=False)
    no_shadow(scr)
    # chin details: power LED and a row of buttons (no logo)
    fy = yz - dep / 2 - 0.0012
    disc("mon_led", 0, 0, 0.0018, 0, M["led_blue"], head, n=10, loc=(aw / 2 - 0.007, fy - 0.0005, -ah / 2 - bb / 2),
         rot=(90, 0, 0))
    for i in range(4):
        cyl(f"mon_btn{i}", 0.0022, 0.002, (aw / 2 - 0.018 - i * 0.008, fy, -ah / 2 - bb / 2), M["pc_dk"],
            rot=(90, 0, 0), n=10, parent=head)
    return head


def build_keyboard(M):
    """A full-size 2009 keyboard: tapered caps, worn shiny keys, legends fading where the fingers go."""
    use("SET")
    g = grp("keyboard", (1.0, 2.21, DZ), (3, 0, 0))
    box("kb_base", (0.465, 0.172, 0.022), (0, 0, 0.011), M["pc"], bev=0.007, seg=2, parent=g)
    box("kb_well", (0.445, 0.128, 0.004), (0, 0.004, 0.0215), M["pc_dk"], bev=0.002, parent=g)
    u = 0.019
    x0, ytop = -0.2185, 0.069
    rows = [
        (0.0, [("Esc", 1), (None, 1)] + [(f"F{i}", 1) for i in range(1, 5)] + [(None, .5)] +
         [(f"F{i}", 1) for i in range(5, 9)] + [(None, .5)] + [(f"F{i}", 1) for i in range(9, 13)],
         [("PrtSc", 1), ("ScrLk", 1), ("Pause", 1)], []),
        (1.5, [(c, 1) for c in "`1234567890-="] + [("Back", 2)], [("Ins", 1), ("Home", 1), ("PgUp", 1)],
         [("Num", 1), ("N/", 1), ("N*", 1), ("N-", 1)]),
        (2.5, [("Tab", 1.5)] + [(c, 1) for c in "QWERTYUIOP[]"] + [("\\", 1.5)], [("Del", 1), ("End", 1), ("PgDn", 1)],
         [("N7", 1), ("N8", 1), ("N9", 1), ("N+", 1, 2)]),
        (3.5, [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL;'"] + [("Enter", 2.25)], [], [("N4", 1), ("N5", 1), ("N6", 1)]),
        (4.5, [("LShift", 2.25)] + [(c, 1) for c in "ZXCVBNM,./"] + [("RShift", 2.75)], [(None, 1), ("Up", 1)],
         [("N1", 1), ("N2", 1), ("N3", 1), ("NEnt", 1, 2)]),
        (5.5, [("LCtrl", 1.25), ("LWin", 1.25), ("LAlt", 1.25), ("Space", 6.25), ("RAlt", 1.25), ("RWin", 1.25),
               ("Menu", 1.25), ("RCtrl", 1.25)], [("Left", 1), ("Down", 1), ("Right", 1)], [("N0", 2), ("N.", 1)]),
    ]
    worn = set("EASNRTOIL") | {"Space", "Enter", "Back", "LShift", "LCtrl", "NEnt", "N.", "Del"} | {f"N{i}" for i in range(10)}
    bm = bmesh.new()
    legends = []
    for ry, main, nav, num in rows:
        for start, keys in ((0.0, main), (15.5, nav), (19.0, num)):
            cx = start
            for k in keys:
                lab, wu = k[0], k[1]
                hu = k[2] if len(k) > 2 else 1
                if lab is not None:
                    kx = x0 + (cx + wu / 2) * u
                    ky = ytop - (ry + hu / 2) * u
                    w2, h2 = wu * u / 2 - 0.0009, hu * u / 2 - 0.0009
                    ins = 0.0019
                    zb, zt = 0.0212, 0.0305
                    vs = [bm.verts.new(p) for p in (
                        (kx - w2, ky - h2, zb), (kx + w2, ky - h2, zb), (kx + w2, ky + h2, zb), (kx - w2, ky + h2, zb),
                        (kx - w2 + ins, ky - h2 + ins, zt), (kx + w2 - ins, ky - h2 + ins, zt),
                        (kx + w2 - ins, ky + h2 - ins, zt), (kx - w2 + ins, ky + h2 - ins, zt))]
                    mi = 1 if lab in worn else 0
                    for idx in ((4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                        bm.faces.new([vs[i] for i in idx]).material_index = mi
                    show = lab.lstrip("N") if lab.startswith("N") and len(lab) == 2 else lab
                    if len(show) == 1 or (show.startswith("F") and len(show) <= 3) or show == "Esc":
                        legends.append((show, kx, ky, lab in worn))
                cx += wu
    keys_m = [M["pc_dk"], mat("key_worn", "#2a2a2c", 0.2, spec=0.65)]
    caps = finish("kb_caps", bm, keys_m, g, angle=30)
    bevel(caps, 0.0011, 1, 30)
    leg_m, leg_w = mat("legend", "#a9abaf", 0.5), mat("legend_worn", "#57595d", 0.4)
    for i, (s, kx, ky, w) in enumerate(legends):
        text(f"kb_leg{i}", s, "verdana.ttf", 0.0044 if len(s) == 1 else 0.0032, (kx, ky, 0.0307),
             leg_w if w else leg_m, parent=g)
    for i, (nm, lm) in enumerate([("num", M["led_green"]), ("caps", M["led_off"]), ("scroll", M["led_off"])]):
        box(f"kb_led_{nm}", (0.004, 0.003, 0.001), (x0 + (19.6 + i * 1.1) * u, ytop - 0.5 * u, 0.0222), lm, bev=0, parent=g)
    return g


def build_keyring(M, kb):
    """Theo's keys, left on the keyboard for Martin: shop door, back gate, padlock; a little chainring fob."""
    use("THEO")
    g = grp("keyring", (0.035, 0.03, 0.0318), (0, 0, -8), parent=kb)
    torus("ring", 0.0135, 0.0014, (0, 0, 0.0016), M["chrome"], rot=(8, -6, 0), nR=28, nr=6, parent=g)

    def key(name, loc, yaw, length, m, bow_r=0.0115, tilt=(0, 0, 0), cover=None):
        k = grp(name, loc, (tilt[0], tilt[1], yaw), parent=g)
        annulus(name + "_bow", circ_pts(0, 0, bow_r, n=18), circ_pts(-bow_r * 0.5, 0, 0.0032, n=18), m=cover or m,
                parent=k, thick=0.0045 if cover else 0.0024, bev=0.0008 if cover else 0.0)
        L = length
        blade = [(bow_r * 0.7, -0.0052), (bow_r + L, -0.0045), (bow_r + L + 0.004, -0.001), (bow_r + L + 0.0025, 0.0016)]
        x = bow_r + L - 0.0025
        up = True
        while x > bow_r + 0.008:
            blade.append((x, 0.0046 if up else 0.0016))
            x -= 0.0038
            up = not up
        blade += [(bow_r + 0.005, 0.0048), (bow_r + 0.002, 0.0065), (bow_r * 0.7, 0.0065)]
        prism(name + "_blade", blade, 0.0022, loc=(0, 0, -0.0011), m=m, parent=k, bev=0.0004)
        box(name + "_groove", (L * 0.8, 0.0009, 0.0004), (bow_r + L * 0.55, 0.0003, 0.0011), M["steel_dk"], bev=0, parent=k)
        return k

    for nm, phi, yaw, L, m, br, tl, dz, cov in (
            ("key_shop", -6, -2, 0.04, M["brass"], 0.014, (0, 3, 0), 0.0, None),
            ("key_gate", 38, 46, 0.034, M["steel"], 0.0135, (5, 0, 0), 0.0008, M["pin_red"]),
            ("key_padlock", -58, -52, 0.022, M["brass_old"], 0.0095, (0, -6, 0), 0.0004, M["pin_blue"])):
        rp = Vector((0.0135 * cos(radians(phi)), 0.0135 * sin(radians(phi)), 0))
        loc = rp + 0.5 * br * Vector((cos(radians(yaw)), sin(radians(yaw)), 0))
        key(nm, (loc.x, loc.y, dz), yaw, L, m, bow_r=br, tilt=tl, cover=cov)
    # the fob: a little chainring, bright steel
    teeth = 14
    pts = []
    for k in range(teeth):
        a = 2 * pi * k / teeth
        for da, rr in ((-0.1, 0.0145), (-0.045, 0.0172), (0.045, 0.0172), (0.1, 0.0145)):
            pts.append((rr * cos(a + da), rr * sin(a + da)))
    inner = [(0.0065 * x / math.hypot(x, y), 0.0065 * y / math.hypot(x, y)) for x, y in pts]
    fob = grp("fob", (-0.034, -0.004, 0.0003), (0, 3, 15), parent=g)
    fob.scale = (1.25, 1.25, 1.25)
    annulus("fob_ring", pts, inner, m=M["brass"], parent=fob, thick=0.0026, bev=0.0005)
    torus("fob_link", 0.0045, 0.001, (-0.0155, -0.002, 0.0012), M["chrome"], rot=(75, 0, 15), nR=14, nr=5, parent=g)
    return g


def build_mouse(M):
    use("SET")
    pad = box("mousepad", (0.23, 0.195, 0.0035), (1.395, 2.225, DZ + 0.00175), M["mousepad"], rot=(0, 0, -4), bev=0.0015)
    pg = grp("pad_print", (1.395, 2.225, DZ + 0.0036), (0, 0, -4))
    torus("pad_logo_wheel", 0.014, 0.0012, (-0.07, -0.072, 0), mat("pad_print", "#8a97a8", 0.9), nR=20, nr=4,
          parent=pg).scale = (1, 1, 0.2)
    text("pad_logo_text", "WHEELWRIGHT", "verdanab.ttf", 0.0085, (-0.05, -0.072, 0), MATS["pad_print"], ax="LEFT", parent=pg)
    m = grp("mouse", (1.41, 2.235, DZ + 0.0035), (0, 0, -9))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        hump = 0.75 + 0.35 * max(0.0, min(1.0, 0.5 - y * 0.6))
        v.co = Vector((x * 0.031 * (1 - 0.12 * y), y * 0.056, max(z, -0.05) * 0.024 * hump + 0.0012))
    body = finish("mouse_body", bm, M["pc"], m, angle=60)
    box("mouse_split", (0.0012, 0.04, 0.004), (0, 0.03, 0.021), M["hole"], bev=0, parent=m)
    cyl("mouse_wheel", 0.0055, 0.004, (0, 0.03, 0.022), M["rubber"], rot=(0, 90, 0), n=12, parent=m)
    disc("mouse_glow", 0, 0, 0.012, 0.0004, mat("mouse_red", "#ff2a1a", 0.5, emit="#ff2a1a", estr=2.0), m, n=10)
    curve("mouse_cable", [(1.41, 2.29, DZ + 0.015), (1.40, 2.36, DZ + 0.004), (1.33, 2.44, DZ + 0.003),
                          (1.24, 2.62, DZ + 0.003), (1.2, D - 0.02, DZ - 0.02), (1.2, D - 0.02, DZ - 0.3)],
          0.0018, M["plastic_blk"])
    curve("kb_cable", [(1.0, 2.3, DZ + 0.012), (0.97, 2.37, DZ + 0.003), (0.9, 2.43, DZ + 0.003),
                       (0.86, 2.66, DZ + 0.003), (0.82, D - 0.02, DZ - 0.05), (0.82, D - 0.02, DZ - 0.3)],
          0.0022, M["plastic_blk"])
    return body


def build_speakers(M):
    use("SET")
    for s, x in (("L", 0.655), ("R", 1.345)):
        g = grp(f"speaker_{s}", (x, 2.5, DZ), (0, 0, 10 if s == "L" else -10))
        box(f"spk_{s}_body", (0.085, 0.09, 0.15), (0, 0, 0.075), M["pc"], bev=0.012, seg=3, parent=g)
        lathe(f"spk_{s}_cone", [(0.0, -0.006), (0.012, -0.004), (0.028, 0.0), (0.031, 0.002), (0.0, 0.002)], n=18,
              m=M["pc_dk"], parent=g, rot=(90, 0, 0), loc=(0, -0.045, 0.06))
        sphere(f"spk_{s}_cap", 0.008, (0, -0.043, 0.06), M["gloss"], seg=10, rings=6, parent=g, scale=(1, 0.5, 1))
        cyl(f"spk_{s}_tw", 0.009, 0.003, (0, -0.0455, 0.118), M["pc_dk"], rot=(90, 0, 0), n=12, parent=g)
        if s == "R":
            cyl("spk_vol", 0.009, 0.012, (0.0, -0.05, 0.022), M["steel_dk"], rot=(90, 0, 0), n=14, parent=g)
            disc("spk_led", 0, 0, 0.0018, 0, M["led_green"], g, n=8, loc=(0.026, -0.0455, 0.022), rot=(90, 0, 0))


def build_lamp(M):
    """Mustard anglepoise between the tower and the monitor, head over the keyboard."""
    use("SET")
    base = Vector((0.605, 2.68, DZ))
    lathe("lamp_base", [(0.0, 0.0), (0.075, 0.0), (0.078, 0.008), (0.07, 0.026), (0.03, 0.034), (0.0, 0.036)], n=24,
          loc=base, m=M["mustard"])
    cyl("lamp_switch", 0.008, 0.008, base + Vector((0.035, -0.035, 0.026)), M["plastic_blk"], n=10, base=True)
    j1 = base + Vector((0, 0, 0.05))
    el = Vector((0.585, 2.6, 1.23))
    hd = Vector((0.66, 2.36, 1.075))
    for p, q, nm in ((j1, el, "lo"), (el, hd + Vector((0, 0.02, 0.03)), "up")):
        side = (q - p).cross(Vector((0, 0, 1))).normalized() * 0.011
        for s in (1, -1):
            tube(f"lamp_arm_{nm}{s}", p + side * s, q + side * s, 0.0045, M["mustard"], n=8)
        mid = (p + q) / 2
        sp = (q - p).normalized()
        tube(f"lamp_spring_{nm}", mid - sp * 0.08 + Vector((0, 0, 0.02)), mid + sp * 0.05 + Vector((0, 0, 0.02)), 0.004,
             M["steel"], n=8)
    for p, nm in ((j1, "j1"), (el, "j2")):
        cyl(f"lamp_knuckle_{nm}", 0.012, 0.034, p, M["mustard"], rot=(0, 90, 20), n=12)
    head = grp("lamp_head", hd)
    aim(head, (0.93, 2.2, 0.76))
    lathe("lamp_shade", [(0.0, 0.085), (0.02, 0.085), (0.027, 0.07), (0.04, 0.03), (0.07, -0.035), (0.067, -0.038),
                         (0.037, 0.026), (0.024, 0.064), (0.0, 0.068)], n=22, m=[M["mustard"], M["shade_in"]],
          seg_mats=[0, 0, 0, 0, 0, 1, 1, 1], parent=head)
    bulb = sphere("lamp_bulb", 0.022, (0, 0, 0.012), M["bulb"], seg=12, rings=8, parent=head)
    no_shadow(bulb)
    cyl("lamp_cap", 0.014, 0.03, (0, 0, 0.095), M["mustard"], n=12, parent=head)
    return head


def paper_sheet(name, w, h, m, parent, curl=0.0, z=0.0):
    """A sheet hanging from its top-centre (origin), extending down -Y, bottom edge lifting off by `curl`."""
    bm = bmesh.new()
    nx, ny = 3, 6
    vs = [[bm.verts.new((-w / 2 + w * i / nx, -h * j / ny, z + curl * (j / ny) ** 2)) for i in range(nx + 1)]
          for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    ob = finish(name, bm, m, parent, smooth=True)
    sd = ob.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.0005
    sd.offset = -1
    return ob


def pushpin(name, parent, x, y, m):
    lathe(name, [(0.0, 0.0), (0.0058, 0.0), (0.0062, 0.0025), (0.0035, 0.004), (0.004, 0.009), (0.0055, 0.0105),
                 (0.0052, 0.013), (0.0, 0.0135)], n=14, loc=(x, y, 0.0005), m=m, parent=parent)


def build_calendar(M, parent):
    """Supplier calendar, November 2026 (Monday-first). Friday 27 circled in Martin's hand."""
    w, h = 0.22, 0.36
    paper_sheet("cal_paper", w, h, M["paper"], parent, curl=0.006)
    top = grp("cal_print", (0, -h / 2, 0.0), parent=parent)       # print space: origin at sheet centre
    zz = 0.00055

    def zc(y):
        return zz + 0.006 * ((h / 2 - y) / h) ** 2               # follow the sheet's curl

    # illustration: a lane through low hills, a rider, a pale sun
    il = [("#d9ddd0", [(-0.1, 0.035), (0.1, 0.035), (0.1, 0.17), (-0.1, 0.17)]),
          ("#efd9a2", circ_pts(0.05, 0.135, 0.016, n=16)),
          ("#9eb294", [(-0.1, 0.085), (-0.06, 0.112), (-0.02, 0.097), (0.03, 0.12), (0.07, 0.102), (0.1, 0.114), (0.1, 0.035), (-0.1, 0.035)]),
          ("#71906b", [(-0.1, 0.064), (-0.04, 0.088), (0.02, 0.072), (0.1, 0.09), (0.1, 0.035), (-0.1, 0.035)]),
          ("#8d877b", [(-0.034, 0.035), (0.046, 0.035), (0.013, 0.083), (0.006, 0.083)])]
    for i, (c, pts) in enumerate(il):
        flat(f"cal_il{i}", pts, zc(0.1) + i * 0.00004, mat(f"cal_il{i}", c, 0.7), top)
    rider = mat("cal_rider", "#2f3a40", 0.6)
    for k, cx in enumerate((-0.068, -0.036)):
        annulus(f"cal_wheel{k}", circ_pts(cx, 0.052, 0.0105, n=16), circ_pts(cx, 0.052, 0.0085, n=16),
                zc(0.05) + 0.0003, rider, top)
    flat("cal_frame", [(-0.068, 0.052), (-0.05, 0.068), (-0.036, 0.052), (-0.052, 0.052), (-0.05, 0.066), (-0.066, 0.053)],
         zc(0.05) + 0.0003, rider, top)
    flat("cal_body", [(-0.055, 0.07), (-0.045, 0.088), (-0.036, 0.09), (-0.033, 0.084), (-0.044, 0.068)],
         zc(0.05) + 0.0003, rider, top)
    disc("cal_head", -0.034, 0.095, 0.0045, zc(0.05) + 0.0003, rider, top, n=10)
    text("cal_month", "NOVEMBER", "verdanab.ttf", 0.017, (-0.1, 0.012, zc(0.0)), M["ink"], ax="LEFT", parent=top)
    text("cal_year", "2026", "verdana.ttf", 0.017, (0.1, 0.012, zc(0.0)), M["red_ink"], ax="RIGHT", parent=top)
    cw, chh, gx0, gy0 = 0.2 / 7, 0.0235, -0.1, -0.012
    for c, dname in enumerate("MTWTFSS"):
        text(f"cal_wd{c}", dname, "verdanab.ttf", 0.0065, (gx0 + (c + 0.5) * cw, gy0 + 0.004, zc(gy0)),
             M["red_ink"] if c == 6 else M["print_grey"], parent=top)
    grey = mat("cal_grid", "#b9b4aa", 0.8)
    for r in range(7):
        yy = gy0 - r * chh
        rect(f"cal_hl{r}", gx0, yy - 0.0002, gx0 + 0.2, yy + 0.0002, zc(yy) + 0.0001, grey, top)
    for c in range(8):
        xx = gx0 + c * cw
        rect(f"cal_vl{c}", xx - 0.0002, gy0 - 6 * chh, xx + 0.0002, gy0, zc(gy0 - 0.07) + 0.0001, grey, top)
    for d in range(1, 31):
        idx = d + 5
        r, c = divmod(idx, 7)
        x = gx0 + c * cw + 0.0025
        y = gy0 - r * chh - 0.0058
        text(f"cal_d{d}", str(d), "verdana.ttf", 0.0074, (x, y, zc(y) + 0.0002),
             M["red_ink"] if c == 6 else M["ink"], ax="LEFT", parent=top)
    text("cal_supplier", "WHEELWRIGHT CYCLE SUPPLY  ·  trade parts since 1979  ·  01632 960 412", "verdana.ttf",
         0.0042, (0, -0.168, zc(-0.168)), M["print_grey"], parent=top, fit=0.196)
    # Martin's marks: Friday 27 circled (twice round, like a real pen), Mon/Tue crossed off, the note in row 6
    cx, cy = gx0 + 4.5 * cw, gy0 - 4.5 * chh
    pts = []
    for i in range(30):
        t = 2 * pi * 1.15 * i / 29 + 1.9
        rr = 1.0 + 0.06 * sin(3 * t) + 0.03 * i / 29
        pts.append((cx + 0.0165 * rr * cos(t), cy + 0.0128 * rr * sin(t), zc(cy) + 0.0006))
    curve("cal_circle", pts, 0.00065, M["red_ink"], parent=top, res=3, bres=1)
    for d in (23, 24):
        r, c = divmod(d + 5, 7)
        x, y = gx0 + (c + 0.5) * cw, gy0 - (r + 0.5) * chh
        for a in (38, -38):
            box(f"cal_x{d}{a}", (0.026, 0.0011, 0.0002), (x, y, zc(y) + 0.0005), M["red_ink"], rot=(0, 0, a), bev=0,
                parent=top)
    yy = gy0 - 5.5 * chh
    text("cal_note", "THEO'S LAST DAY :(", "Inkfree.ttf", 0.0135, (gx0 + 4.0 * cw, yy - 0.0015, zc(yy) + 0.0005),
         M["red_ink"], parent=top, fit=0.165, rot=(0, 0, 3), extrude=0.00008)
    curve("cal_arrow", [(cx + 0.005, yy + 0.0075, zc(yy) + 0.0006), (cx + 0.0085, yy + 0.012, zc(yy) + 0.0006),
                        (cx + 0.006, cy - 0.0135, zc(cy) + 0.0006)], 0.0005, M["red_ink"], parent=top, res=4, bres=1)
    for a in (-35, 35):
        box(f"cal_arrowhead{a}", (0.0045, 0.0009, 0.0002), (cx + 0.006 + 0.0016 * (1 if a > 0 else -1), cy - 0.0155,
                                                            zc(cy) + 0.0006), M["red_ink"], rot=(0, 0, 90 + a), bev=0, parent=top)
    pushpin("cal_pin", parent, 0, -0.008, M["pin_red"])


def build_photo(M, parent):
    """2009 print: teenage Theo (red hoodie, shaggy fringe) holding up a CD-R, Martin's arm round him, shopfront."""
    w, h = 0.152, 0.102
    paper_sheet("photo_paper", w, h, mat("photo_white", "#f3f1ea", 0.3, coat=0.3), parent, curl=0.0)
    p = grp("photo_print", (0, -h / 2, 0.00055), parent=parent)
    gl = {}

    def pm(c):
        if c not in gl:
            gl[c] = mat("ph_" + c.lstrip("#"), c, 0.3, coat=0.4)
        return gl[c]

    z = [0.0]

    def shape(nm, pts, c):
        z[0] += 0.00004
        return flat("ph_" + nm, pts, z[0], pm(c), p)

    X0, X1, Y0, Y1 = -0.0715, 0.0715, -0.0465, 0.0465
    shape("sky", [(X0, 0.028), (X1, 0.028), (X1, Y1), (X0, Y1)], "#b7c4cc")
    shape("facade", [(X0, -0.03), (X1, -0.03), (X1, 0.032), (X0, 0.032)], "#cdbd96")
    shape("fascia", [(X0, 0.012), (X1, 0.012), (X1, 0.027), (X0, 0.027)], "#2f4d3c")
    shape("win", [(X0 + 0.004, -0.028), (0.022, -0.028), (0.022, 0.009), (X0 + 0.004, 0.009)], "#2f4d3c")
    shape("glass", [(X0 + 0.007, -0.025), (0.019, -0.025), (0.019, 0.006), (X0 + 0.007, 0.006)], "#7d939d")
    shape("glint", [(X0 + 0.02, -0.025), (X0 + 0.032, -0.025), (X0 + 0.05, 0.006), (X0 + 0.038, 0.006)], "#a7bac2")
    shape("door", [(0.032, -0.03), (0.058, -0.03), (0.058, 0.01), (0.032, 0.01)], "#2f4d3c")
    shape("doorglass", [(0.036, -0.008), (0.054, -0.008), (0.054, 0.006), (0.036, 0.006)], "#6c818b")
    shape("pavement", [(X0, Y0), (X1, Y0), (X1, -0.03), (X0, -0.03)], "#8f8b83")
    # Martin, 44 in 2009: flat cap, work apron
    shape("m_legs", [(0.008, -0.044), (0.0255, -0.044), (0.024, -0.016), (0.0095, -0.016)], "#2b2f38")
    shape("m_torso", [(0.0065, -0.017), (0.027, -0.017), (0.0285, 0.0045), (0.005, 0.0045)], "#3c4f72")
    shape("m_apron", [(0.009, -0.024), (0.0245, -0.024), (0.0235, 0.002), (0.01, 0.002)], "#7a5536")
    shape("m_arm_r", [(0.027, 0.004), (0.031, 0.002), (0.03, -0.016), (0.0265, -0.016)], "#3c4f72")
    shape("m_head", circ_pts(0.0168, 0.0095, 0.0047, n=14), "#d9a785")
    shape("m_cap", [(0.0118, 0.011), (0.0222, 0.011), (0.0232, 0.0128), (0.0205, 0.0155), (0.013, 0.0155)], "#4a4642")
    shape("m_tache", [(0.0148, 0.0078), (0.0188, 0.0078), (0.0185, 0.0071), (0.0151, 0.0071)], "#6b5a4c")
    # Theo, 14: shaggy fringe, red hoodie, jeans
    shape("t_legs", [(-0.016, -0.044), (-0.004, -0.044), (-0.0045, -0.024), (-0.0155, -0.024)], "#4d6487")
    shape("t_torso", [(-0.0185, -0.025), (-0.0015, -0.025), (-0.001, -0.0035), (-0.019, -0.0035)], "#a8443a")
    shape("t_head", circ_pts(-0.01, 0.0015, 0.0041, n=14), "#e0b08f")
    shape("t_hair", [(-0.0148, 0.0012), (-0.0145, 0.005), (-0.0115, 0.0068), (-0.0065, 0.0066), (-0.0048, 0.004),
                     (-0.0052, 0.0016), (-0.0075, 0.0034), (-0.0105, 0.0026), (-0.0128, 0.0036)], "#3b2a20")
    shape("m_arm_l", [(0.0065, 0.003), (-0.003, 0.0005), (-0.0045, -0.003), (0.0065, -0.0005)], "#3c4f72")
    shape("t_arm", [(-0.0185, -0.006), (-0.0215, -0.016), (-0.018, -0.0175), (-0.0155, -0.009)], "#a8443a")
    # the CD-R, held up to the camera, oversized
    cdx, cdy = -0.0215, -0.0145
    shape("cd", circ_pts(cdx, cdy, 0.0095, n=24), "#d8dcde")
    shape("cd_sheen", [(cdx - 0.006, cdy - 0.0072), (cdx - 0.002, cdy - 0.0092), (cdx + 0.008, cdy + 0.003),
                       (cdx + 0.006, cdy + 0.0065)], "#e7e3ef")
    shape("cd_hole", circ_pts(cdx, cdy, 0.0016, n=12), "#9aa0a3")
    shape("t_hand", circ_pts(cdx + 0.0005, cdy - 0.0095, 0.0022, n=10), "#e0b08f")
    for i, (x, y) in enumerate(((-0.0115, 0.0013), (-0.0085, 0.0013), (0.0152, 0.0098), (0.0185, 0.0098))):
        disc(f"ph_eye{i}", x, y, 0.00042, z[0] + 0.00004, pm("#2a221d"), p, n=6)
    z[0] += 0.0001
    text("ph_cd_text", "SHOP SYSTEM\nv1", "segoeprb.ttf", 0.0022, (cdx, cdy + 0.0032, z[0]), M["marker"], parent=p,
         line=0.85, fit=0.0125, rot=(0, 0, 8))
    text("ph_sign", "SPOKES & SPROCKETS", "georgiab.ttf", 0.0068, (0, 0.0195, z[0]), pm("#e9dfc4"), parent=p, fit=0.112)
    text("ph_date", "'09  6 14", "consolab.ttf", 0.0042, (0.066, -0.0425, z[0]), pm("#ff8a24"), ax="RIGHT", parent=p)
    pushpin("photo_pin", parent, -0.058, -0.006, M["pin_blue"])


def build_readme(M, parent):
    """Theo's printed README, dog-eared bottom-right; the notes that used to be sticky notes live here now."""
    w, h = 0.21, 0.297
    c = 0.032
    bm = bmesh.new()
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, -h + c), (w / 2 - c, -h), (-w / 2, -h)]
    f = bm.faces.new([bm.verts.new((x, y, 0.0)) for x, y in pts])
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    sheet = finish("readme_paper", bm, M["paper"], parent, smooth=False)
    sd = sheet.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.0005
    sd.offset = -1
    flat("readme_dogear", [(w / 2 - c, -h), (w / 2, -h + c), (w / 2 - c, -h + c)], 0.0012, M["paper_back"], parent)
    zt = 0.0009
    text("readme_title", "README", "consolab.ttf", 0.026, (-w / 2 + 0.016, -0.034, zt), M["ink"], ax="LEFT", parent=parent)
    text("readme_sub", "for whoever looks after it next", "consola.ttf", 0.0085, (-w / 2 + 0.016, -0.05, zt),
         M["print_grey"], ax="LEFT", parent=parent)
    rect("readme_rule", -w / 2 + 0.016, -0.057, w / 2 - 0.016, -0.0565, zt, M["ink"], parent)
    lines = ["1. The system is this PC.", "   Don't unplug it.", "", "2. Backup: USB stick,", "   desk drawer 2.", "",
             "3. Supplier logins are in", "   the red binder.", "", "4. Never trust the stock", "   count on a Friday.", "",
             "5. Reports: coming soon!!", "", "Look after him. - T"]
    for i, ln in enumerate(lines):
        if ln:
            y = -0.073 - i * 0.0128
            text(f"readme_l{i}", ln, "consola.ttf", 0.0098, (-w / 2 + 0.016, y, zt),
                 M["ink"], ax="LEFT", parent=parent)
    pushpin("readme_pin", parent, 0, -0.008, M["pin_yellow"])


def build_corkboard(M):
    use("SET")
    x0, x1, z0, z1 = 1.45, 2.25, 0.98, 1.62
    for nm, a, b in [("cork_fr_T", (x0, D - 0.026, z1 - 0.028), (x1, D, z1)), ("cork_fr_B", (x0, D - 0.026, z0), (x1, D, z0 + 0.028)),
                     ("cork_fr_L", (x0, D - 0.026, z0), (x0 + 0.028, D, z1)), ("cork_fr_R", (x1 - 0.028, D - 0.026, z0), (x1, D, z1))]:
        boxmm(nm, a, b, M["oak_lt"], bev=0.006)
    boxmm("cork", (x0 + 0.02, D - 0.018, z0 + 0.02), (x1 - 0.02, D, z1 - 0.02), M["cork"], bev=0)
    yf = D - 0.0185
    cal = grp("calendar", (1.6, yf, 1.585), (88, 1.5, 0))
    build_calendar(M, cal)
    ph = grp("photo", (1.875, yf, 1.565), (88.5, -5, 0))
    build_photo(M, ph)
    rd = grp("readme", (2.085, yf, 1.505), (88, 3, 0))
    build_readme(M, rd)
    spare = grp("spare_pins", (0, yf, 0), (90, 0, 0))
    for i, (x, z, c) in enumerate(((1.79, 1.07, "green"), (1.81, 1.065, "red"), (1.505, 1.03, "white"))):
        pushpin(f"spare_pin{i}", spare, x, z, M["pin_" + c])
    # the wall clock above the board (hands set per preset)
    clk = grp("clock", (1.85, D - 0.03, 1.88), (90, 0, 0))
    lathe("clock_rim", [(0.0, -0.03), (0.125, -0.03), (0.13, -0.02), (0.13, 0.0), (0.122, 0.008), (0.112, 0.0),
                        (0.0, 0.0)], n=36, m=M["oak"], parent=clk)
    disc("clock_face", 0, 0, 0.112, 0.0005, M["clock_face"], clk, n=36)
    for k in range(12):
        a = 2 * pi * k / 12
        big = k % 3 == 0
        box(f"clock_tick{k}", (0.004 if big else 0.0022, 0.014 if big else 0.009, 0.0004),
            (0.098 * sin(a), 0.098 * cos(a), 0.0008), M["ink"], rot=(0, 0, -math.degrees(a)), bev=0, parent=clk)
    hands = {}
    for nm, ln, wd in (("hour", 0.058, 0.0055), ("minute", 0.088, 0.0035)):
        hg = grp(f"clock_{nm}", (0, 0, 0.0016 if nm == "hour" else 0.0022), parent=clk)
        box(f"clock_{nm}_hand", (wd, ln, 0.0006), (0, ln / 2 - 0.012, 0), M["ink"], bev=0, parent=hg)
        hands[nm] = hg
    cyl("clock_hub", 0.005, 0.004, (0, 0, 0.0024), M["brass"], n=12, parent=clk)
    return hands


def drawer_contents(name, parent, kind, w, d, M):
    bm = bmesh.new()
    n = {"bolts": 26, "nipples": 40, "balls": 30, "valves": 14, "ends": 34, "ferrules": 30, "plugs": 12,
         "links": 16, "misc": 14, "cables": 0}[kind]
    for _ in range(n):
        x, y = RNG.uniform(-w / 2 + 0.006, w / 2 - 0.006), RNG.uniform(-d / 2 + 0.006, d / 2 - 0.006)
        zz = RNG.uniform(0.002, 0.026)
        if kind == "balls":
            g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0035)
        else:
            L = {"bolts": 0.016, "valves": 0.03, "plugs": 0.012}.get(kind, 0.008)
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0024 if kind != "plugs" else 0.007,
                                      radius2=0.0024 if kind != "plugs" else 0.007, depth=L)
        rot = Vector((RNG.random(), RNG.random(), RNG.random())).normalized()
        q = Vector((0, 0, 1)).rotation_difference(rot)
        for v in g["verts"]:
            v.co = q @ v.co + Vector((x, y, zz))
    m = {"bolts": M["steel"], "nipples": M["brass"], "balls": M["chrome"], "valves": M["brass_old"], "ends": M["steel"],
         "ferrules": M["plastic_blk"], "plugs": M["pin_red"], "links": M["steel_dk"], "misc": M["brass_old"]}[kind]
    return finish(name, bm, m, parent, angle=60)


def build_shelf(M):
    """Wall shelf over the left of the desk: a parts cabinet with clear drawers, the brake pads drawer pulled out
    with ONE pair left, ring binders, stock boxes."""
    use("SET")
    sx0, sx1, sz = 0.22, 1.42, 1.5
    boxmm("shelf", (sx0, D - 0.25, sz), (sx1, D, sz + 0.028), M["oak_lt"], bev=0.006)
    for bx in (0.32, 1.3):
        boxmm(f"shelf_brk_h{bx}", (bx - 0.01, D - 0.2, sz - 0.012), (bx + 0.01, D, sz), M["steel_dk"], bev=0.002)
        boxmm(f"shelf_brk_v{bx}", (bx - 0.01, D - 0.012, sz - 0.17), (bx + 0.01, D, sz), M["steel_dk"], bev=0.002)
        tube(f"shelf_brk_d{bx}", (bx, D - 0.008, sz - 0.15), (bx, D - 0.17, sz - 0.008), 0.005, M["steel_dk"], n=6)
    top = sz + 0.028
    # parts cabinet: 3 rows x 4 small drawers, 1 row x 2 big drawers; clear plastic, contents visible
    cab = grp("parts_cabinet", (0.5, D - 0.1, top))
    cw, cdp, chh = 0.46, 0.17, 0.33
    box("cab_top", (cw, cdp, 0.012), (0, 0, chh - 0.006), M["drawer_body"], bev=0.004, parent=cab)
    box("cab_bot", (cw, cdp, 0.012), (0, 0, 0.006), M["drawer_body"], bev=0.004, parent=cab)
    box("cab_back", (cw, 0.008, chh), (0, cdp / 2 - 0.004, chh / 2), M["drawer_body"], bev=0.002, parent=cab)
    for s in (-1, 1):
        box(f"cab_side{s}", (0.012, cdp, chh), (s * (cw / 2 - 0.006), 0, chh / 2), M["drawer_body"], bev=0.004, parent=cab)
    zdiv = 0.012 + 0.11 + 0.002
    box("cab_div_big", (cw - 0.02, cdp, 0.004), (0, 0, zdiv), M["drawer_body"], bev=0.001, parent=cab)
    box("cab_div_bigv", (0.004, cdp, 0.11), (0, 0, 0.012 + 0.055), M["drawer_body"], bev=0.001, parent=cab)
    for r in (1, 2):
        box(f"cab_div_h{r}", (cw - 0.02, cdp, 0.003), (0, 0, zdiv + 0.002 + r * 0.067 - 0.0015), M["drawer_body"],
            bev=0.001, parent=cab)
    for c in (1, 2, 3):
        box(f"cab_div_v{c}", (0.003, cdp, chh - zdiv - 0.012), (-cw / 2 + 0.012 + c * (cw - 0.024) / 4, 0,
            (zdiv + chh - 0.012) / 2), M["drawer_body"], bev=0.001, parent=cab)
    small = [("M5 BOLTS", "bolts"), ("SPOKE NIPS", "nipples"), ("BEARINGS", "balls"), ("VALVES", "valves"),
             ("CABLE ENDS", "ends"), ("FERRULES", "ferrules"), ("BAR PLUGS", "plugs"), ("CHAIN LINKS", "links"),
             ("BOTTLE BOLTS", "bolts"), ("SPOKE NIPS 2", "nipples"), ("BITS", "misc"), ("MISC", "misc")]
    big = [("BRAKE PADS", "pads"), ("CABLES", "cables")]
    dw_s, dh_s, dw_b, dh_b = (cw - 0.024) / 4, 0.064, (cw - 0.024) / 2, 0.11
    lab_m = mat("label", "#f4f0e4", 0.7)
    for r in range(3):
        for c in range(4):
            lab, kind = small[r * 4 + c]
            x = -cw / 2 + 0.012 + (c + 0.5) * dw_s
            zb = 0.012 + dh_b + 0.004 + r * (dh_s + 0.003)
            dg = grp(f"drawer_{lab}", (x, -0.008, zb), parent=cab)
            _drawer(dg, dw_s - 0.004, cdp - 0.02, dh_s - 0.004, lab, kind, M, lab_m)
    for c in range(2):
        lab, kind = big[c]
        x = -cw / 2 + 0.012 + (c + 0.5) * dw_b
        pull = -0.095 if lab == "BRAKE PADS" else -0.008
        dg = grp(f"drawer_{lab}", (x, pull, 0.014), parent=cab)
        _drawer(dg, dw_b - 0.004, cdp - 0.02, dh_b - 0.004, lab, kind, M, lab_m)
    # stock boxes and ring binders
    for i, (x, wdt, hgt, c) in enumerate(((0.79, 0.11, 0.09, "card"), (0.8, 0.1, 0.07, "card"), (0.91, 0.12, 0.13, "card"))):
        z0 = top if i != 1 else top + 0.09
        bx = box(f"stock_box{i}", (wdt, 0.18, hgt), (x if i != 1 else 0.795, D - 0.11, z0 + hgt / 2), M[c], bev=0.004,
                 rot=(0, 0, RNG.uniform(-4, 4)))
        lbl = ["TUBES 700C", "TUBES 26\"", "GRIPS"][i]
        text(f"stock_label{i}", lbl, "verdanab.ttf", 0.0095, (0, -0.0905, 0), M["marker"], rot=(90, 0, 0), parent=bx,
             fit=wdt - 0.02)
    bcols = [("binder_navy", "INVOICES\n2009–"), ("binder_red", "SUPPLIERS\n& LOGINS"), ("binder_green", "VAT"),
             ("binder_black", "MANUALS")]
    for i, (mn, lbl) in enumerate(bcols):
        lean = -14 if i == 3 else 0
        x = 1.025 + i * 0.07 + (0.03 if i == 3 else 0)
        b = grp(f"binder{i}", (x, D - 0.135, top), (0, lean, 0))
        box(f"binder{i}_body", (0.062, 0.26, 0.315), (0, 0, 0.1575), M[mn], bev=0.006, parent=b)
        box(f"binder{i}_label", (0.044, 0.0012, 0.075), (0, -0.1305, 0.225), lab_m, bev=0, parent=b)
        text(f"binder{i}_text", lbl, "Inkfree.ttf", 0.0105, (0, -0.1315, 0.23), M["marker"], rot=(90, 0, 0), parent=b,
             fit=0.04, line=0.9)
        torus(f"binder{i}_hole", 0.0085, 0.0022, (0, -0.1305, 0.09), M["hole"], rot=(90, 0, 0), nR=14, nr=5, parent=b)


def _drawer(g, w, d, h, label, kind, M, lab_m):
    t = 0.0025
    box("dr_front", (w, t, h), (0, -d / 2, h / 2), mat("clear_front", "#e6eef3", 0.05, spec=0.7, alpha=0.08), bev=0.002,
        parent=g)
    box("dr_lip", (w, t * 1.6, 0.012), (0, -d / 2, h - 0.006), M["drawer_body"], bev=0.0015, parent=g)
    box("dr_back", (w, t, h * 0.8), (0, d / 2, h * 0.4), M["clear"], bev=0.001, parent=g)
    box("dr_floor", (w, d, t), (0, 0, t / 2), M["clear"], bev=0.001, parent=g)
    for s in (-1, 1):
        box(f"dr_side{s}", (t, d, h * 0.8), (s * w / 2, 0, h * 0.4), M["clear"], bev=0.001, parent=g)
    box("dr_pull", (w * 0.35, 0.008, 0.005), (0, -d / 2 - 0.004, h * 0.18), M["drawer_body"], bev=0.002, parent=g)
    lw = min(w * 0.8, 0.09)
    box("dr_label", (lw, 0.001, 0.0135), (0, -d / 2 - 0.0026, h - 0.0075), lab_m, bev=0, parent=g)
    text("dr_label_text", label.replace(" 2", ""), "Inkfree.ttf", 0.0108, (0, -d / 2 - 0.0033, h - 0.0078), M["marker"],
         rot=(90, 0, 0), parent=g, fit=lw - 0.008)
    if kind == "pads":
        # the last pair of disc pads, stood up just behind the clear front, friction side out: an empty drawer
        # with one pair in it reads from anywhere in front of the shelf
        for i, (x, rz, rx) in enumerate(((-0.028, 5, 78), (0.026, -7, 82))):
            pg = grp(f"pad{i}", (x, -d / 2 + 0.016, t + 0.0125), (rx, 0, rz), parent=g)
            outline = [(-0.021, -0.012), (0.021, -0.012), (0.024, 0.0), (0.019, 0.011), (0.006, 0.015), (0.004, 0.021),
                       (-0.004, 0.021), (-0.006, 0.015), (-0.019, 0.011), (-0.024, 0.0)]
            prism("pad_plate", outline, 0.0022, m=M["steel_dk"], parent=pg, bev=0.0005)
            inner = [(-0.019, -0.0105), (0.019, -0.0105), (0.0215, 0.0), (0.017, 0.0095), (-0.017, 0.0095), (-0.0215, 0.0)]
            prism("pad_comp", inner, 0.004, loc=(0, 0, 0.0022), m=M["pad_compound"], parent=pg, bev=0.0006)
            disc("pad_hole", 0, 0.0175, 0.0012, 0.0023, M["hole"], pg, n=8)
    elif kind == "cables":
        for i in range(9):
            torus(f"cable{i}", RNG.uniform(0.03, 0.04), 0.0018,
                  (RNG.uniform(-w / 4, w / 4), RNG.uniform(-d / 5, d / 5), 0.01 + i * 0.0085),
                  M["plastic_blk"] if i % 3 else M["steel"], rot=(RNG.uniform(-12, 12), RNG.uniform(-12, 12), 0),
                  nR=20, nr=5, parent=g)
    else:
        drawer_contents("dr_stuff", g, kind, w, d, M)


# ================================================================ desk-top props
def build_desk_props(M):
    use("SET")
    # CD-R spindle (era), letter tray, pen pot, bin, the OKAYEST NEPHEW mug
    sp = grp("cd_spindle", (1.555, 2.66, DZ))
    lathe("spindle_base", [(0.0, 0.0), (0.066, 0.0), (0.068, 0.006), (0.064, 0.012), (0.0, 0.012)], n=24, m=M["plastic_blk"], parent=sp)
    cyl("spindle_post", 0.0072, 0.115, (0, 0, 0.012), M["plastic_blk"], n=10, base=True, parent=sp)
    lathe("spindle_cds", [(0.0076, 0.012), (0.06, 0.012), (0.06, 0.058), (0.0076, 0.058)], n=32, m=[M["cd"]], parent=sp)
    lathe("spindle_cdtop", [(0.0076, 0.0581), (0.06, 0.0581), (0.0599, 0.0587), (0.0076, 0.0587)], n=32, m=M["paper"], parent=sp)
    lathe("spindle_cdhub", [(0.0076, 0.0588), (0.019, 0.0588), (0.019, 0.0589), (0.0076, 0.0589)], n=24, m=M["cd_top"], parent=sp)
    lathe("spindle_dome", [(0.0, 0.135), (0.03, 0.133), (0.055, 0.124), (0.064, 0.11), (0.065, 0.014),
                           (0.0638, 0.014), (0.0638, 0.11), (0.054, 0.1225), (0.03, 0.1315), (0.0, 0.1335)], n=28,
          m=M["dome"], parent=sp)
    tr = grp("letter_tray", (1.98, 2.52, DZ), (0, 0, -6))
    box("tray_floor", (0.26, 0.33, 0.006), (0, 0, 0.003), M["plastic_blk"], bev=0.002, parent=tr)
    for s in (-1, 1):
        box(f"tray_side{s}", (0.006, 0.33, 0.06), (s * 0.127, 0, 0.03), M["plastic_blk"], bev=0.002, parent=tr)
    box("tray_back", (0.26, 0.006, 0.06), (0, 0.162, 0.03), M["plastic_blk"], bev=0.002, parent=tr)
    for i in range(6):
        box(f"tray_paper{i}", (0.21, 0.297, 0.0012), (RNG.uniform(-0.006, 0.006), RNG.uniform(-0.01, 0.004), 0.007 + i * 0.0014),
            M["paper"] if i % 2 else M["paper_back"], rot=(0, 0, RNG.uniform(-3, 3)), bev=0, parent=tr)
    pot = grp("pen_pot", (1.79, 2.69, DZ))
    lathe("pen_pot_jar", [(0.0, 0.0), (0.033, 0.0), (0.035, 0.004), (0.035, 0.1), (0.032, 0.1), (0.032, 0.006), (0.0, 0.006)],
          n=18, m=M["navy"], parent=pot)
    for i, (dx, dy, c, ln) in enumerate(((0.01, 0.004, "blue", 0.14), (-0.012, 0.006, "red", 0.13), (0.0, -0.012, "yellow", 0.16),
                                          (-0.006, -0.002, "white", 0.15))):
        tube(f"pen{i}", (dx * 0.4, dy * 0.4, 0.01), (dx * 2.2, dy * 2.2, 0.01 + ln), 0.004, M["pin_" + c], n=6, parent=pot)
    tube("pot_scissors", (0.0, 0.0, 0.01), (0.022, 0.016, 0.15), 0.0025, M["steel"], n=6, parent=pot)
    torus("pot_scissor_loop", 0.009, 0.0025, (0.024, 0.018, 0.158), M["pin_red"], rot=(60, 0, 30), nR=12, nr=5, parent=pot)
    bin_ = grp("waste_bin", (0.62, 2.45, 0))
    lathe("bin", [(0.0, 0.0), (0.11, 0.0), (0.13, 0.3), (0.124, 0.3), (0.105, 0.008), (0.0, 0.008)], n=20, m=M["steel_dk"], parent=bin_)
    for i in range(3):
        sphere(f"bin_paper{i}", 0.04, (RNG.uniform(-0.03, 0.03), RNG.uniform(-0.03, 0.03), 0.27 + i * 0.012), M["paper"],
               ico=1, parent=bin_, scale=(1.0, 0.9, 0.8))
    # the mug, text wrapped round the body
    mug = grp("mug", (1.74, 2.36, DZ), (0, 0, -16))
    R = 0.042
    lathe("mug_body", [(0.0, 0.0), (0.036, 0.0), (0.0405, 0.004), (R, 0.012), (R, 0.092), (0.0405, 0.0965),
                       (0.0375, 0.0965), (0.0365, 0.092), (0.0362, 0.012), (0.0, 0.009)], n=24, m=M["ceramic"], parent=mug)
    torus("mug_handle", 0.026, 0.0065, (R - 0.004, 0, 0.051), M["ceramic"], rot=(90, 0, 0), nR=12, nr=8, arc=(-76, 76), parent=mug)
    t = text("mug_text_src", "WORLD'S\nOKAYEST\nNEPHEW", "verdanab.ttf", 0.0118, (0, 0, 0), M["navy"], line=0.95)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
    bpy.data.objects.remove(t, do_unlink=True)
    rr = R + 0.0004
    for v in me.vertices:
        x, y, _ = v.co
        th = x / rr
        v.co = Vector((rr * sin(th), -rr * cos(th), 0.053 + y))
    me.materials.clear()
    me.materials.append(M["navy"])
    link(bpy.data.objects.new("mug_text", me), mug)
    return mug


def build_theo(M, kb, mug):
    """Theo's last week: his keys on the keyboard, the box for Lisbon, his headphones, cold coffee."""
    build_keyring(M, kb)
    use("THEO")
    cyl("coffee", 0.0362, 0.002, (0, 0, 0.026), M["coffee"], n=24, parent=mug)
    # headphones on the desk, left of the keyboard
    hp = grp("headphones", (0.57, 2.2, DZ), (0, 0, 18))
    pad_m = mat("hp_pad", "#2f6f6a", 0.85)
    for s in (-1, 1):
        cup = grp(f"hp_cup{s}", (s * 0.072, 0, 0.044), (0, 90 * s, 0), parent=hp)
        cyl(f"hp_shell{s}", 0.044, 0.03, (0, 0, -0.012), M["plastic_blk"], n=20, bev=0.01, seg=2, parent=cup)
        torus(f"hp_pad{s}", 0.032, 0.012, (0, 0, 0.008), pad_m, nR=20, nr=8, parent=cup)
        cyl(f"hp_cap{s}", 0.022, 0.004, (0, 0, -0.028), M["steel_dk"], n=16, parent=cup)
        tube(f"hp_yoke{s}", (s * 0.09, 0, 0.07), (s * 0.084, 0, 0.115), 0.004, M["steel"], n=6, parent=hp)
    arc = [(0.086 * cos(radians(a)), 0.0, 0.082 + 0.085 * sin(radians(a))) for a in range(0, 181, 15)]
    curve("hp_band", arc, 0.0085, M["plastic_blk"], parent=hp, res=6).scale = (1.0, 2.2, 1.0)
    curve("hp_cable", [(-0.1, 0.0, 0.02), (-0.14, -0.03, 0.003), (-0.12, -0.1, 0.003), (-0.02, -0.12, 0.003),
                       (0.06, -0.085, 0.003)], 0.0018, M["plastic_blk"], parent=hp)
    # the moving box, half packed, on the floor by the desk
    bxg = grp("moving_box", (2.3, 1.74, 0), (0, 0, 9))
    bw, bd, bh = 0.5, 0.38, 0.36
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * bw, v.co.y * bd, (v.co.z + 0.5) * bh))
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.5], context="FACES")
    body = finish("box_body", bm, M["card"], bxg, angle=30)
    sd = body.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.006
    sd.offset = -1
    bevel(body, 0.003, 1)
    fl = bd * 0.5 - 0.004                                    # every flap is half the box depth
    for nm, size, loc, hinge in [("front", (bw - 0.004, 0.005, fl), (0, -bd / 2 + 0.003, bh), (68, 0, 0)),
                                 ("back", (bw - 0.004, 0.005, fl), (0, bd / 2 - 0.003, bh), (-104, 0, 0)),
                                 ("left", (0.005, bd - 0.004, fl), (-bw / 2 + 0.003, 0, bh), (0, -122, 0)),
                                 ("right", (0.005, bd - 0.004, fl), (bw / 2 - 0.003, 0, bh), (0, 98, 0))]:
        hg = grp(f"flap_{nm}_hinge", loc, hinge, parent=bxg)
        box(f"flap_{nm}", size, (0, 0, fl / 2), M["card"], bev=0.002, parent=hg)
    box("box_tape", (0.05, 0.0012, 0.09), (0.0, -bd / 2 - 0.0009, bh - 0.045), M["tape"], bev=0, parent=bxg)
    text("box_label", "THEO,\nLISBON", "segoeprb.ttf", 0.085, (0.0, -bd / 2 - 0.0015, bh * 0.47), M["marker"],
         rot=(90, 0, 0), parent=bxg, line=0.8, fit=0.42)
    curve("box_underline", [(-0.15, -bd / 2 - 0.0016, 0.07), (0.0, -bd / 2 - 0.0016, 0.064), (0.16, -bd / 2 - 0.0016, 0.072)],
          0.0022, M["marker"], parent=bxg, res=6, bres=1)
    # contents: his desk plant (it goes to Lisbon), a poster tube, a rolled hoodie with a sleeve over the side
    pl = grp("plant", (0.1, 0.06, bh - 0.12), parent=bxg)
    lathe("plant_pot", [(0.0, 0.0), (0.045, 0.0), (0.058, 0.11), (0.062, 0.11), (0.062, 0.125), (0.0, 0.125)], n=14,
          m=M["terracotta"], parent=pl)
    cyl("plant_soil", 0.056, 0.004, (0, 0, 0.122), mat("soil", "#3a2a1f", 0.95), n=14, parent=pl)
    for k in range(9):
        a = 2 * pi * k / 9 + RNG.uniform(-0.2, 0.2)
        L = RNG.uniform(0.13, 0.2)
        lean = RNG.uniform(18, 38)
        leaf = flat(f"leaf{k}", [(0, -0.012), (L * 0.6, -0.018), (L, 0), (L * 0.6, 0.018), (0, 0.012)], 0,
                    M["plant"] if k % 2 else M["plant_dk"], pl)
        leaf.location = (0, 0, 0.12)
        leaf.rotation_euler = (0.0, radians(-(90 - lean)), a)
        sd = leaf.modifiers.new("Solid", "SOLIDIFY")
        sd.thickness = 0.002
    tube("poster_tube", (-0.17, 0.08, 0.05), (-0.08, 0.02, bh + 0.25), 0.035, M["kraft"], n=12, parent=bxg)
    sphere("hoodie_lump", 0.13, (-0.07, -0.05, bh - 0.06), M["hoodie"], ico=2, parent=bxg, scale=(1.3, 0.95, 0.55))
    curve("hoodie_sleeve", [(-0.12, -0.08, bh - 0.02), (-0.2, -0.12, bh + 0.02), (-0.252, -0.12, bh - 0.005),
                            (-0.262, -0.12, bh - 0.12), (-0.258, -0.1, bh - 0.2)], 0.032, M["hoodie"], parent=bxg, res=6)


def build_martin(M, mug):
    """Monday: Martin's reading glasses on a cord, his rag, a paper job card, a pencil, tea in Theo's mug."""
    use("MARTIN")
    cyl("tea", 0.0362, 0.002, (0, 0, 0.079), M["tea"], n=24, parent=mug)
    # job card, Monday's first job: Anika's brakes
    jc = grp("job_card", (0.58, 2.2, DZ + 0.0006), (0, 0, 10))
    box("jc_card", (0.1, 0.15, 0.0008), (0, 0, 0), M["manila"], bev=0, parent=jc)
    zt = 0.0006
    text("jc_head", "SPOKES & SPROCKETS", "verdanab.ttf", 0.0062, (0, 0.062, zt), M["ink"], parent=jc, fit=0.088)
    text("jc_head2", "JOB CARD", "verdana.ttf", 0.0055, (0, 0.053, zt), M["print_grey"], parent=jc)
    text("jc_no", "No. 0417", "consola.ttf", 0.005, (0.042, 0.043, zt), M["red_ink"], ax="RIGHT", parent=jc)
    fields = [("Name", "Anika", 0.03), ("Bike", "grey hybrid", 0.012), ("Work", "brake pads F+R", -0.006),
              ("", "(2 pairs)", -0.02), ("Due", "Tues", -0.038)]
    for i, (lab, val, y) in enumerate(fields):
        if lab:
            text(f"jc_lab{i}", lab + ":", "verdana.ttf", 0.0048, (-0.044, y, zt), M["print_grey"], ax="LEFT", parent=jc)
        rect(f"jc_line{i}", -0.026, y - 0.0025, 0.044, y - 0.0022, zt, M["print_grey"], jc)
        text(f"jc_val{i}", val, "Inkfree.ttf", 0.0082, (-0.023, y + 0.0004, zt + 0.0001), M["blue_ink"], ax="LEFT",
             parent=jc, fit=0.066)
    text("jc_foot", "est. 1987", "georgia.ttf", 0.0045, (0, -0.066, zt), M["print_grey"], parent=jc)
    # reading glasses on a cord, resting on the card
    gl = grp("glasses", (0.6, 2.26, DZ + 0.019), (0, 0, -14))
    fr = grp("glasses_front", (0, 0, 0.0), (62, 0, 0), parent=gl)
    for s in (-1, 1):
        pts = []
        for i in range(16):
            a = 2 * pi * i / 16
            ca, sa = cos(a), sin(a)
            pts.append((s * 0.031 + 0.026 * math.copysign(abs(ca) ** 0.6, ca), 0.019 * math.copysign(abs(sa) ** 0.7, sa), 0))
        curve(f"gl_rim{s}", pts, 0.0024, M["tortoise"], parent=fr, cyclic=True, res=3, bres=1)
        flat(f"gl_lens{s}", [(p[0], p[1]) for p in pts], 0, M["lens"], fr)
    curve("gl_bridge", [(-0.007, 0.006, 0), (0.0, 0.01, 0.0), (0.007, 0.006, 0)], 0.0014, M["tortoise"], parent=fr)
    for s in (-1, 1):
        tube(f"gl_temple{s}", (s * 0.053, 0.004, -0.003), (-s * 0.036, 0.003 * s, -0.011 - 0.002 * s), 0.0013,
             M["tortoise"], n=6, parent=fr)
    curve("gl_cord", [(-0.054, 0.001, 0.002), (-0.075, -0.02, -0.012), (-0.07, -0.07, -0.0145), (0.0, -0.095, -0.0145),
                      (0.075, -0.065, -0.0145), (0.088, -0.012, -0.012), (0.054, 0.001, 0.002)], 0.0009, M["cord"],
          parent=gl, res=8)
    # the greasy rag, a crumpled low-poly cloth
    bm = bmesh.new()
    n = 9
    rr = random.Random(61)
    vs = [[bm.verts.new(((i / (n - 1) - 0.5) * 0.26, (j / (n - 1) - 0.5) * 0.22,
                          max(0.0, 0.028 * sin(i * 1.3 + j * 0.7) * cos(j * 0.9) + rr.uniform(0, 0.018)) *
                          (1 - abs(i / (n - 1) - 0.5) * 1.2)))
           for i in range(n)] for j in range(n)]
    for j in range(n - 1):
        for i in range(n - 1):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    rag = finish("rag", bm, M["rag"], None, (1.66, 2.165, DZ + 0.002), (0, 0, 18), smooth=False)
    sd = rag.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.003
    # pencil behind the keyboard
    pc = grp("pencil", (1.07, 2.335, DZ + 0.0045), (0, 90, 8))
    cyl("pencil_body", 0.0045, 0.16, (0, 0, 0), M["pencil"], n=6, parent=pc)
    cyl("pencil_tip", 0.0045, 0.018, (0, 0, -0.089), M["pencil_wood"], r2=0.0012, n=6, parent=pc).rotation_euler = _rot((180, 0, 0))
    cyl("pencil_ferrule", 0.0046, 0.008, (0, 0, 0.084), M["steel"], n=10, parent=pc)
    cyl("pencil_eraser", 0.0044, 0.008, (0, 0, 0.092), M["eraser"], n=10, parent=pc)


def build_note(M, head):
    """The one sticky note on the whole set: Theo's, on the bezel."""
    use("SET")
    g = grp("sticky_note", (0.122, -0.0312, -0.168), (90, -4, 0), parent=head)
    s = 0.076
    bm = bmesh.new()
    nx = 5
    vs = [[bm.verts.new((-s / 2 + s * i / nx, -s / 2 + s * j / nx,
                         0.0 if (-s / 2 + s * j / nx) > -0.02 else 0.011 * ((-0.02 - (-s / 2 + s * j / nx)) / 0.018) ** 2))
           for i in range(nx + 1)] for j in range(nx + 1)]
    for j in range(nx):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    note = finish("note_paper", bm, M["sticky"], g, smooth=True)
    sd = note.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.0006
    sd.offset = -1
    text("note_text", "Reports:\ncoming soon\n(sorry Uncle M)", "segoepr.ttf", 0.0115, (0.0, 0.009, 0.0004),
         M["marker"], parent=g, line=0.8, fit=0.07, rot=(0, 0, 2))
    return g


# ================================================================ lights, cameras, presets
LIGHTS = {}


def light(name, kind, loc, energy, color, coll, target=None, size=0.1, size_y=None, spot=None, blend=0.4, radius=None,
          parent=None, jitter=True):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.shape = "RECTANGLE"
        ld.size = size
        ld.size_y = size_y if size_y is not None else size
    elif kind == "SPOT":
        ld.spot_size = radians(spot or 60)
        ld.spot_blend = blend
    if radius is not None and kind != "AREA" and kind != "SUN":
        ld.shadow_soft_size = radius
    try:
        ld.use_shadow_jitter = jitter
    except AttributeError:
        pass
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    link(ob, parent, coll)
    if target is not None:
        aim(ob, target)
    LIGHTS[name] = ob
    return ob


def build_lights(M, lamp_head, mon_head):
    bpy.context.view_layer.update()
    # --- night: desk lamp, monitor glow, cool window, a work lamp in the workshop
    lamp = light("L_lamp", "SPOT", (0, 0, 0.0), 40.0, (1.0, 0.74, 0.47), "NIGHT", spot=95, blend=0.65, radius=0.018,
                 parent=lamp_head)
    lamp.rotation_euler = (0, 0, 0)
    light("L_box_kick", "SPOT", (1.75, 0.55, 0.95), 7.0, (1.0, 0.8, 0.6), "NIGHT", target=(2.3, 1.55, 0.2), spot=24,
          blend=0.8, radius=0.2)
    light("L_pegboard", "SPOT", (3.0, 4.2, 2.3), 28.0, (1.0, 0.82, 0.62), "NIGHT", target=(3.0, 6.0, 1.45), spot=60,
          blend=0.7, radius=0.15)
    light("L_floor_spill", "AREA", (1.85, 1.5, 1.9), 9.0, (1.0, 0.78, 0.56), "NIGHT", target=(2.05, 1.85, 0.0),
          size=1.0, size_y=1.0)
    light("L_bounce", "AREA", (1.25, 1.75, 1.7), 7.0, (1.0, 0.78, 0.56), "NIGHT", target=(1.3, 2.5, 0.8), size=1.2,
          size_y=0.8)
    mw = mon_head.matrix_world
    n = (mw.to_3x3() @ Vector((0, -1, 0))).normalized()
    c = mw @ Vector((0, -0.04, 0))
    light("L_screen", "AREA", c + n * 0.01, 5.0, (0.62, 0.76, 1.0), "NIGHT", target=c + n, size=0.4, size_y=0.25)
    wy0, wy1, wz0, wz1 = WIN
    light("L_window_night", "SPOT", (-2.4, 0.85, 3.3), 1300.0, (0.55, 0.68, 1.0), "NIGHT",
          target=(0.9, 1.7, 0.35), spot=26, blend=0.35, radius=0.22)
    light("L_window_fill", "AREA", (-0.2, (wy0 + wy1) / 2, (wz0 + wz1) / 2), 14.0, (0.5, 0.62, 0.95), "NIGHT",
          target=(1.5, 1.5, 1.2), size=0.9, size_y=0.95)
    light("L_street", "POINT", (-0.4, 1.4, 2.3), 9.0, (0.75, 0.82, 1.0), "NIGHT", radius=0.1)
    light("L_worklamp", "SPOT", (3.1, 5.0, 1.6), 90.0, (1.0, 0.8, 0.58), "NIGHT", target=(2.95, 4.5, 0.9), spot=80,
          blend=0.6, radius=0.05)
    light("L_bell_kiss", "POINT", (3.0, 3.35, 1.35), 2.0, (1.0, 0.82, 0.6), "NIGHT", radius=0.1)
    # --- monday: cool daylight through the window, sky fill, workshop strip light
    sun = light("L_sun", "SUN", (-2, 1.5, 3), 22.0, (1.0, 0.97, 0.93), "MONDAY")
    sun.data.angle = radians(3)
    aim(sun, (-2 + 0.65, 1.5 + 0.55, 3 - 0.52))
    light("L_window_day", "AREA", (-0.16, (wy0 + wy1) / 2, (wz0 + wz1) / 2 + 0.05), 90.0, (0.72, 0.84, 1.0), "MONDAY",
          target=(1.4, 2.3, 0.9), size=0.95, size_y=1.0)
    light("L_strip", "AREA", (3.1, 5.9, 2.12), 140.0, (0.93, 0.97, 1.0), "MONDAY", target=(3.0, 3.6, 0.6), size=1.15, size_y=0.12)
    light("L_screen_day", "AREA", c + n * 0.01, 2.0, (0.62, 0.76, 1.0), "MONDAY", target=c + n, size=0.4, size_y=0.25)
    light("L_room_fill", "AREA", (1.6, 0.7, 2.4), 40.0, (0.8, 0.88, 1.0), "MONDAY", target=(1.3, 2.3, 0.6), size=2.2, size_y=1.6)


def camera(name, loc, target, lens, fstop, focus, shift=(0, 0)):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.shift_x, cd.shift_y = shift
    cd.clip_start = 0.02
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    fe = grp(name + "_focus", focus, coll="CAMS")
    cd.dof.focus_object = fe
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    link(ob, coll="CAMS")
    aim(ob, target)
    return ob


def build_cameras():
    camera("CAM_wide", (2.8, -4.95, 2.4), (1.66, 1.4, 0.82), 38, 1.6, (1.1, 2.4, 1.0))
    camera("CAM_medium", (1.44, 0.86, 1.5), (1.12, 2.5, 1.1), 30, 2.4, (1.02, 2.34, 0.9))
    camera("CAM_keys", (1.25, 1.92, 1.1), (1.08, 2.34, 0.8), 45, 10.0, (1.06, 2.3, 0.8))
    camera("CAM_medium_monday", (1.44, 0.86, 1.5), (1.12, 2.5, 1.1), 30, 2.4, (1.02, 2.34, 0.9))
    camera("CAM_board", (1.84, 1.98, 1.42), (1.84, 2.8, 1.4), 36, 2.8, (1.84, 2.78, 1.4))
    camera("CAM_shelf", (0.66, 1.95, 1.86), (0.44, 2.62, 1.6), 45, 2.8, (0.4, 2.6, 1.57))


def apply_preset(name, M, hands):
    night = name == "night"
    COLL["NIGHT"].hide_render = not night
    COLL["MONDAY"].hide_render = night
    COLL["THEO"].hide_render = not night
    COLL["MARTIN"].hide_render = night
    sc = bpy.context.scene
    bg = sc.world.node_tree.nodes["Background"]
    if night:
        bg.inputs[0].default_value = rgba("#1c2333")
        bg.inputs[1].default_value = 0.45
    else:
        bg.inputs[0].default_value = rgba("#b4c2d2")
        bg.inputs[1].default_value = 0.5
    principled(M["bulb"]).inputs["Emission Strength"].default_value = 20.0 if night else 0.0
    principled(M["tube"]).inputs["Emission Strength"].default_value = 0.0 if night else 9.0
    sky = principled(M["outside_sky"])
    sky.inputs["Emission Color"].default_value = rgba("#0c1424") if night else rgba("#dfe8ef")
    sky.inputs["Emission Strength"].default_value = 1.0 if night else 3.0
    principled(M["outside_win"]).inputs["Emission Strength"].default_value = 3.0 if night else 0.0
    principled(M["outside_brick"]).inputs["Base Color"].default_value = rgba("#6c4537")
    SCREEN["bsdf"].inputs["Emission Strength"].default_value = 1.0 if night else 1.25
    sc.view_settings.exposure = 0.3 if night else 0.0
    # clock: 23:41 on the night, 08:52 on Monday
    hh, mm = (23, 41) if night else (8, 52)
    hands["hour"].rotation_euler = (0, 0, -2 * pi * ((hh % 12) + mm / 60) / 12)
    hands["minute"].rotation_euler = (0, 0, -2 * pi * mm / 60)


def setup_render(args):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = args.scale
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    ee = sc.eevee
    ee.taa_render_samples = args.samples
    ee.use_raytracing = True
    ee.ray_tracing_method = "SCREEN"
    ee.ray_tracing_options.resolution_scale = "2"
    ee.ray_tracing_options.use_denoise = True
    ee.use_fast_gi = True
    ee.fast_gi_method = "GLOBAL_ILLUMINATION"
    ee.fast_gi_distance = 0.6
    ee.use_shadows = True
    ee.shadow_ray_count = 2
    ee.shadow_step_count = 8
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError as e:
        print("colour management:", e)
    w = bpy.data.worlds.new("World")
    if not w.node_tree:
        w.use_nodes = True
    sc.world = w
    build_compositor()


def build_compositor():
    """Soft bloom on the practicals and a gentle vignette."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new("Grade", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    rl = N.new("CompositorNodeRLayers")
    out = N.new("NodeGroupOutput")
    last = rl.outputs["Image"]
    try:
        gl = N.new("CompositorNodeGlare")
        vals = {"Type": "Bloom", "Quality": "High", "Threshold": 1.0, "Smoothness": 0.6, "Strength": 0.22, "Size": 0.6}
        for s in gl.inputs:
            if s.name in vals:
                try:
                    s.default_value = vals[s.name]
                except (TypeError, ValueError) as e:
                    print("glare", s.name, e)
        L.new(last, gl.inputs["Image"])
        last = gl.outputs["Image"]
        em = N.new("CompositorNodeEllipseMask")
        em.inputs["Size"].default_value = (0.98, 0.9)
        bl = N.new("CompositorNodeBlur")
        bl.inputs["Size"].default_value = (260, 260)
        L.new(em.outputs["Mask"], bl.inputs["Image"])
        mx = N.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        sock(mx.inputs, "Factor_Float").default_value = 0.3
        L.new(last, sock(mx.inputs, "A_Color"))
        L.new(bl.outputs["Image"], sock(mx.inputs, "B_Color"))
        last = sock(mx.outputs, "Result_Color")
    except Exception as e:                                    # keep rendering even if a node API shifts
        print("compositor fallback:", repr(e))
    L.new(last, out.inputs["Image"])
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    try:
        sc.render.compositor_device = "GPU"
    except TypeError:
        pass


# ================================================================ main
def main():
    args = parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for name in ("SET", "WORKSHOP", "THEO", "MARTIN", "NIGHT", "MONDAY", "CAMS"):
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    if args.regen_screen or not os.path.exists(PLACEHOLDER):
        make_placeholder(PLACEHOLDER)
        print("wrote", PLACEHOLDER)
    setup_render(args)
    M = build_materials()
    screen_m = screen_material(os.path.abspath(args.screen) if args.screen else PLACEHOLDER)

    build_room(M)
    build_outside(M)
    build_workshop(M)
    build_desk(M)
    build_chair(M)
    build_tower(M)
    mon_head = build_monitor(M, screen_m)
    kb = build_keyboard(M)
    build_mouse(M)
    build_speakers(M)
    lamp_head = build_lamp(M)
    hands = build_corkboard(M)
    build_shelf(M)
    mug = build_desk_props(M)
    build_theo(M, kb, mug)
    build_martin(M, mug)
    build_note(M, mon_head)
    apply_fits()
    build_lights(M, lamp_head, mon_head)
    build_cameras()
    print(f"built {len(bpy.data.objects)} objects in {time.time() - t0:.1f}s")

    if args.save_blend:
        apply_preset("night", M, hands)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "desk.blend"), compress=True)
    if args.no_render:
        return
    sc = bpy.context.scene
    for shot in [s.strip() for s in args.shots.split(",") if s.strip()]:
        cam, preset, fname, ev = SHOTS[shot]
        apply_preset(preset, M, hands)
        sc.view_settings.exposure += ev
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = os.path.join(OUT, fname)
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {shot} -> {fname} in {time.time() - t1:.1f}s")


if __name__ == "__main__":
    main()
