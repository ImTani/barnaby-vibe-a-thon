"""Barnaby film v2: the back-office desk diorama at Spokes & Sprockets.

Builds the whole set procedurally (no external assets except Windows fonts and the screen PNG) and renders stills
with Eevee. Everything is reproducible from this file. See video/v2/WORLD.md for the world it depicts.

Run from the repo root (Git Bash):
    source scripts/env.sh
    "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \
        --python video/v2/world/desk.py -- [options]

Options (after the `--`):
    --shots a,b,...    which stills to render (default: DEFAULT_SHOTS; extras: board_night, shelf_monday, bell_night,
                       screen_night, close_night, drawer_monday)
    --scale N          resolution percentage of 1920x1080 (default 100; use 40 for quick looks)
    --samples N        Eevee render samples (default 64)
    --screen PATH      one PNG for the monitor in every preset (overrides the per-preset screens below)
    --screen-night / --screen-monday / --screen-tuesday / --screen-close PATH
                       per-preset screens (defaults: SCREENS; 16:10 fills the panel, 16:9 is letterboxed)
    --screen-fit M     auto (default: letterbox anything not 16:10), letterbox, crop (fill, centred) or stretch
    --lcd plain        the old flat emissive screen (no LCD treatment, no reflection room)
    --regen-screen     rebuild screen_placeholder.png
    --regen-photo      re-render the 2009 photo (out/photo_2009.png) from its mini-set
    --save-blend       also save out/desk.blend (for animation work)
    --no-render        build only

Collections: SET (the room, desk, PC, corkboard, shelf), WORKSHOP (through the doorway), THEO (Thursday night only),
MARTIN (Monday only), MARTIN_KIT (Monday and Tuesday), PRIYA (Tuesday only), CLOSE (the goodnight shot only),
NOTE (the sticky note: Thursday and Monday), NIGHT and MONDAY (each preset's lights), REFLECT (the room's fourth
wall, seen only in the glossy screen), CAMS. apply_preset() swaps them. Presets: night, monday, tuesday, close.
Dates and times: CONTINUITY.md (and CLOCK below). Handwriting: Segoe Print is Theo's (the sticky note, the box, the
key tag), Ink Free is Martin's (calendar, labels, job cards, binders), Mistral is the barista's (Priya's cup),
Kristen ITC is a child's (the thank-you drawing).
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
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PLACEHOLDER = os.path.join(HERE, "screen_placeholder.png")
FRAMES = os.path.normpath(os.path.join(HERE, "..", "look", "frames"))
SCREEN_DIR = os.path.join(HERE, "screens")                  # made by make_screens.py (Tuesday patch, asleep)
PHOTO_2009 = os.path.join(OUT, "photo_2009.png")            # rendered from the mini-set on first run
FONT_DIR = r"C:\Windows\Fonts"

# shot name -> (camera, lighting preset, output file, exposure offset)
SHOTS = {
    "wide_night": ("CAM_wide", "night", "01_wide_night.png", 0.45),
    "medium_night": ("CAM_medium", "night", "02_medium_night.png", 0.0),
    "keys_night": ("CAM_keys", "night", "03_keys_night.png", 0.0),
    "medium_monday": ("CAM_medium_monday", "monday", "04_medium_monday.png", 0.0),
    "medium_tuesday": ("CAM_medium_tuesday", "tuesday", "05_medium_tuesday.png", 0.0),
    # detail stills
    "board_night": ("CAM_board", "night", "x_board_night.png", 0.2),
    "shelf_monday": ("CAM_shelf", "monday", "x_shelf_monday.png", 0.0),
    "bell_night": ("CAM_bell", "night", "x_bell.png", 0.3),
    "screen_night": ("CAM_screen", "night", "x_screen_night.png", 0.0),
    "drawer_monday": ("CAM_drawer", "monday", "x_drawer_monday.png", 0.2),
    "close_night": ("CAM_medium", "close", "x_close_night.png", 0.0),
    "close_half": ("CAM_close_half", "close", "x_close_half_shop.png", 0.0, (960, 1080)),
    "cables_top": ("CAM_cables_top", "monday", "x_cables_top.png", 0.0),
    "cables_under": ("CAM_cables_under", "monday", "x_cables_under.png", 1.2),
}
DEFAULT_SHOTS = "wide_night,medium_night,keys_night,medium_monday,medium_tuesday"

# what the monitor shows in each preset (the shop PC look-dev is canon; see CONTINUITY.md)
SCREENS = {
    "night": os.path.join(FRAMES, "shop-pc-03-tabs.png"),                 # Thu 19 Nov, 21:47, nine tabs
    "monday": os.path.join(FRAMES, "shop-pc-12-desktop-16x10.png"),       # Mon 23 Nov, 08:52, Back Office
    "tuesday": os.path.join(SCREEN_DIR, "shop-tuesday.png"),              # Tue 24 Nov, 08:34, Priya's two jobs
    "close": os.path.join(SCREEN_DIR, "shop-asleep.png"),                 # asleep; Barnaby's bell in the corner
}
SCREEN_BRIGHT = {"night": 0.88, "monday": 1.3, "tuesday": 1.3, "close": 1.0}   # backlight against the room
REFLECT_LEVEL = {"night": 0.06, "monday": 0.45, "tuesday": 0.5, "close": 0.05}  # the fourth wall's light level
SCREEN_PATHS = {}
SCREEN_FIT = ["auto"]
# the wall clock per preset (hh, mm)
CLOCK = {"night": (21, 47), "monday": (8, 52), "tuesday": (8, 34), "close": (18, 40)}

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
    for k in SCREENS:
        p.add_argument(f"--screen-{k}", default=None)
    p.add_argument("--screen-fit", default="auto", choices=("auto", "letterbox", "crop", "stretch"))
    p.add_argument("--lcd", default="film", choices=("film", "plain"))
    p.add_argument("--regen-photo", action="store_true")
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


# ---------------------------------------------------------------- cables: every one starts and ends somewhere
PORTS = {}


def port(name, loc, direction, parent):
    """A socket on a device: an empty whose +Z is the way a plug's cable leaves it (in the parent's space)."""
    e = grp("port_" + name, loc, parent=parent)
    e.rotation_mode = "QUATERNION"
    e.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized())
    e.empty_display_size = 0.01
    PORTS[name] = e
    return e


def port_frame(name):
    bpy.context.view_layer.update()
    mw = PORTS[name].matrix_world
    return mw.translation.copy(), (mw.to_3x3() @ Vector((0, 0, 1))).normalized()


def connector(name, kind, at, d, M, coll=None, spin=0.0):
    """A plug seated at `at` with its cable leaving along unit vector `d` (spun `spin` degrees about it).
    Returns where the cable begins."""
    at, d = Vector(at), Vector(d).normalized()
    g = grp(name, at, coll=coll)
    g.rotation_mode = "QUATERNION"
    g.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d) @ Quaternion((0, 0, 1), radians(spin))
    blk, grey = M["plastic_blk"], mat("plug_grey", "#4a4c50", 0.45)
    if kind == "usb":
        box(name + "_metal", (0.012, 0.0045, 0.012), (0, 0, -0.004), M["steel"], bev=0.0005, parent=g, coll=coll)
        box(name + "_body", (0.016, 0.0085, 0.022), (0, 0, 0.011), blk, bev=0.002, parent=g, coll=coll)
        cyl(name + "_relief", 0.004, 0.012, (0, 0, 0.026), blk, r2=0.0028, n=10, parent=g, coll=coll)
        L = 0.032
    elif kind == "ps2":
        cyl(name + "_body", 0.0068, 0.02, (0, 0, 0.01), mat("ps2_purple", "#6b4c8f", 0.4), n=14, bev=0.0015, parent=g,
            coll=coll)
        cyl(name + "_relief", 0.0045, 0.01, (0, 0, 0.025), blk, r2=0.003, n=10, parent=g, coll=coll)
        L = 0.03
    elif kind == "jack":
        col = {"green": "#5aa55a", "pink": "#d98aa8", "blue": "#5b86c9"}.get(name.split("_")[-1], "#5aa55a")
        cyl(name + "_tip", 0.0018, 0.008, (0, 0, -0.004), M["chrome"], n=8, parent=g, coll=coll)
        cyl(name + "_body", 0.0038, 0.018, (0, 0, 0.009), mat("jack_" + col, col, 0.45), n=12, bev=0.001, parent=g,
            coll=coll)
        cyl(name + "_relief", 0.0026, 0.008, (0, 0, 0.022), blk, r2=0.0018, n=8, parent=g, coll=coll)
        L = 0.026
    elif kind == "vga":
        box(name + "_body", (0.033, 0.012, 0.016), (0, 0, 0.008), mat("vga_blue", "#3a5aa8", 0.4), bev=0.002, parent=g,
            coll=coll)
        for s in (-1, 1):
            cyl(f"{name}_screw{s}", 0.0035, 0.012, (s * 0.0205, 0, 0.012), M["steel_dk"], n=10, bev=0.0008, parent=g,
                coll=coll)
        cyl(name + "_hood", 0.0075, 0.02, (0, 0, 0.026), blk, r2=0.0045, n=12, parent=g, coll=coll)
        L = 0.036
    elif kind == "iec":
        box(name + "_body", (0.026, 0.02, 0.034), (0, 0, 0.017), blk, bev=0.003, parent=g, coll=coll)
        cyl(name + "_relief", 0.006, 0.016, (0, 0, 0.04), blk, r2=0.004, n=10, parent=g, coll=coll)
        L = 0.048
    elif kind == "uk":                                        # UK mains plug: the cable leaves from its side
        box(name + "_body", (0.051, 0.045, 0.024), (0, 0, 0.012), mat("plug_white", "#ece8de", 0.4), bev=0.003,
            parent=g, coll=coll)
        box(name + "_fuse", (0.012, 0.025, 0.0008), (0.012, 0.0, 0.0244), mat("plug_fuse", "#d7d1c3", 0.5), bev=0,
            parent=g, coll=coll)
        cyl(name + "_relief", 0.0055, 0.014, (0, -0.0275, 0.012), mat("plug_white", "#ece8de", 0.4), rot=(90, 0, 0),
            n=10, parent=g, coll=coll)
        bpy.context.view_layer.update()
        return g.matrix_world @ Vector((0, -0.034, 0.012))
    elif kind == "relief":                                    # a hard-wired cable through a rubber bush
        cyl(name + "_bush", 0.0042, 0.008, (0, 0, 0.004), blk, r2=0.003, n=10, parent=g, coll=coll)
        L = 0.008
    else:
        raise ValueError(kind)
    return at + d * L


def cable(name, pts, r, m, coll=None, res=10):
    """A cable through control points (world space). Clamped NURBS: it starts and ends exactly on the end points
    and leaves along the first and last segments, so put the second point straight out of the plug."""
    return curve(name, [tuple(p) for p in pts], r, m, res=res, bres=2, coll=coll)


def run(name, plug_kind, port_name, waypoints, r, M, m=None, out=0.02, coll=None, end=None):
    """Plug into a port and lay the cable through world waypoints. Returns the cable."""
    at, d = port_frame(port_name)
    start = connector(name + "_plug", plug_kind, at, d, M, coll=coll)
    pts = [start, start + d * out] + [Vector(p) for p in waypoints]
    if end is not None:
        pts += end
    return cable(name, pts, r, m or M["plastic_blk"], coll=coll)


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
PANEL_ASPECT = 0.408 / 0.255          # the 19in 16:10 panel's active area
PANEL_NATIVE = (1440, 900)            # its native resolution (2009): the pixel grid in close-ups


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def halation_image(img, name, down=6, passes=3, radius=3):
    """A small, blurred copy of the screen image: the light that scatters inside the panel's glass and the film's
    halation. Sampled with linear filtering, so it is a big soft blur for free."""
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
    px = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)   # stored sRGB -> linear light
    SCREEN["mean"] = px.reshape(-1, 3).mean(axis=0)
    hh, ww = h // down, w // down
    small = px[:hh * down, :ww * down].reshape(hh, down, ww, down, 3).mean(axis=(1, 3))
    for _ in range(passes):                                   # three box blurs ~ a gaussian
        for ax in (0, 1):
            c = np.cumsum(np.pad(small, [(radius + 1, radius) if a == ax else (0, 0) for a in range(2)] + [(0, 0)],
                                 mode="edge"), axis=ax)
            hi = [slice(None)] * 3
            lo = [slice(None)] * 3
            hi[ax] = slice(2 * radius + 1, None)
            lo[ax] = slice(None, -2 * radius - 1)
            small = (c[tuple(hi)] - c[tuple(lo)]) / (2 * radius + 1)
    out = bpy.data.images.get(name) or bpy.data.images.new(name, ww, hh, alpha=False, float_buffer=True)
    if tuple(out.size) != (ww, hh):
        out.scale(ww, hh)
    rgba_ = np.concatenate([small, np.ones((hh, ww, 1), np.float32)], axis=2)
    out.pixels.foreach_set(rgba_.ravel())
    return out


def lcd_material(name="screen", plain=False):
    """The 2009 glossy LCD. Emission = the screen image (fitted to the 16:10 panel: letterboxed, cropped or
    stretched) + a soft halation veil + the panel's black level with a little backlight bleed at the edges, times a
    subpixel grid that only fades in when a camera is close enough to resolve it. The surface on top is glossy glass,
    so the room (and its reflection-only fourth wall) shows in the dark parts of the picture."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = principled(m)
    b.inputs["Base Color"].default_value = rgba("#050506")
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.4 if plain else 0.75
    b.inputs["Coat Roughness"].default_value = 0.03 if plain else 0.015
    uvn = nt.nodes.new("ShaderNodeUVMap")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    nt.links.new(uvn.outputs["UV"], mp.inputs["Vector"])
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.interpolation = "Cubic"
    tx.extension = "EXTEND" if plain else "CLIP"
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    bright = nt.nodes.new("ShaderNodeValue")
    bright.outputs[0].default_value = 1.0
    nt.links.new(bright.outputs[0], b.inputs["Emission Strength"])
    SCREEN.update(mat=m, bsdf=b, tex=tx, mapping=mp, bright=bright, plain=plain, img=None)
    if plain:
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        return m
    # halation veil (same fit), mixed under the sharp image
    hx = nt.nodes.new("ShaderNodeTexImage")
    hx.interpolation = "Linear"
    hx.extension = "CLIP"
    nt.links.new(mp.outputs["Vector"], hx.inputs["Vector"])
    veil = nt.nodes.new("ShaderNodeMix")
    veil.data_type = "RGBA"
    veil.blend_type = "ADD"
    sock(veil.inputs, "Factor_Float").default_value = 0.09
    nt.links.new(tx.outputs["Color"], sock(veil.inputs, "A_Color"))
    nt.links.new(hx.outputs["Color"], sock(veil.inputs, "B_Color"))
    col = sock(veil.outputs, "Result_Color")
    # black level and backlight bleed (the panel glows faintly where the picture is black, more at the edges)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs["UV"], sep.inputs[0])
    dx = _math(nt, "MINIMUM", sep.outputs["X"], _math(nt, "SUBTRACT", 1.0, sep.outputs["X"]))
    dy = _math(nt, "MINIMUM", sep.outputs["Y"], _math(nt, "SUBTRACT", 1.0, sep.outputs["Y"]))
    edge = _math(nt, "MINIMUM", _math(nt, "MULTIPLY", dx, 1.6), dy)
    bleed = _math(nt, "ADD", 1.0, _math(nt, "MULTIPLY", _math(nt, "POWER", _math(nt, "SUBTRACT", 1.0, _math(
        nt, "MULTIPLY", edge, 9.0, clamp=True)), 3.0), 2.2))
    blk = nt.nodes.new("ShaderNodeMix")
    blk.data_type = "RGBA"
    blk.blend_type = "ADD"
    nt.links.new(_math(nt, "MULTIPLY", bleed, 0.0035), sock(blk.inputs, "Factor_Float"))
    nt.links.new(col, sock(blk.inputs, "A_Color"))
    sock(blk.inputs, "B_Color").default_value = rgba("#c9d4e6")
    col = sock(blk.outputs, "Result_Color")
    # subpixel grid at the panel's native resolution: R, G, B stripes with the black matrix between them
    grid = nt.nodes.new("ShaderNodeValue")
    grid.outputs[0].default_value = 0.0
    fx = _math(nt, "FRACT", _math(nt, "MULTIPLY", sep.outputs["X"], PANEL_NATIVE[0]))
    fy = _math(nt, "FRACT", _math(nt, "MULTIPLY", sep.outputs["Y"], PANEL_NATIVE[1]))
    sub = _math(nt, "MULTIPLY", fx, 3.0)
    gapx = _math(nt, "GREATER_THAN", _math(nt, "FRACT", sub), 0.14)
    gapy = _math(nt, "GREATER_THAN", fy, 0.1)
    gap = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", gapx, gapy), 3.0 / (0.86 * 0.9))
    r_ = _math(nt, "LESS_THAN", sub, 1.0)
    b_ = _math(nt, "GREATER_THAN", sub, 2.0)
    g_ = _math(nt, "SUBTRACT", _math(nt, "SUBTRACT", 1.0, r_), b_)
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for i, ch in enumerate((r_, g_, b_)):
        nt.links.new(_math(nt, "MULTIPLY", ch, gap), cc.inputs[i])
    gm = nt.nodes.new("ShaderNodeMix")
    gm.data_type = "RGBA"
    nt.links.new(grid.outputs[0], sock(gm.inputs, "Factor_Float"))
    sock(gm.inputs, "A_Color").default_value = (1, 1, 1, 1)
    nt.links.new(cc.outputs[0], sock(gm.inputs, "B_Color"))
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    sock(mul.inputs, "Factor_Float").default_value = 1.0
    nt.links.new(col, sock(mul.inputs, "A_Color"))
    nt.links.new(sock(gm.outputs, "Result_Color"), sock(mul.inputs, "B_Color"))
    nt.links.new(sock(mul.outputs, "Result_Color"), b.inputs["Emission Color"])
    SCREEN.update(halo=hx, grid=grid)
    return m


def set_screen(path, fit="auto"):
    """Show an image on the panel. 16:10 fills it; anything else is letterboxed or pillarboxed (fit=auto), the way a
    2009 LCD with aspect scaling shows a non-native picture; fit=crop fills and crops the centre; stretch stretches."""
    if SCREEN.get("path") == (path, fit):
        return
    img = bpy.data.images.load(path, check_existing=True)
    SCREEN["tex"].image = img
    w, h = img.size
    a = w / h
    sx = sy = 1.0
    mode = fit
    if fit == "auto":
        mode = "stretch" if abs(a - PANEL_ASPECT) < 0.01 else "letterbox"
    if mode == "letterbox":
        if a > PANEL_ASPECT:
            sy = a / PANEL_ASPECT                             # bars top and bottom
        else:
            sx = PANEL_ASPECT / a                             # bars left and right
    elif mode == "crop":
        if a > PANEL_ASPECT:
            sx = PANEL_ASPECT / a
        else:
            sy = a / PANEL_ASPECT
    mp = SCREEN["mapping"]
    mp.inputs["Scale"].default_value = (sx, sy, 1.0)
    mp.inputs["Location"].default_value = (0.5 * (1 - sx), 0.5 * (1 - sy), 0.0)
    if "halo" in SCREEN:
        SCREEN["halo"].image = halation_image(img, "halation_" + os.path.basename(path))
    SCREEN["path"] = (path, fit)
    print(f"screen: {os.path.basename(path)} {w}x{h} ({mode})")


def grid_for_camera(cam, scale_pct):
    """How strongly to show the subpixel grid for this camera: only when one LCD pixel covers a few film pixels."""
    if "grid" not in SCREEN:
        return
    bpy.context.view_layer.update()
    scr = bpy.data.objects["screen"]
    d = (cam.matrix_world.translation - scr.matrix_world.translation).length
    res_x = 1920 * scale_pct / 100
    footprint = d * cam.data.sensor_width / (cam.data.lens * res_x)   # metres of panel per render pixel
    cell_px = (0.408 / PANEL_NATIVE[0]) / footprint
    g = max(0.0, min(1.0, (cell_px - 1.5) / 2.5))
    SCREEN["grid"].outputs[0].default_value = g * 0.85
    print(f"  LCD pixel = {cell_px:.2f} film px -> grid {g:.2f}")


REFLECT_EMIT = []


def refl_mat(name, color, strength=1.0):
    """Self-lit material for the reflection-only room (it is only ever seen in the glossy screen, so it is shaded by
    hand: a little emission, scaled per preset)."""
    if name in MATS:
        return MATS[name]
    m = mat(name, color, 0.9, emit=color, estr=strength)
    REFLECT_EMIT.append((principled(m), strength))
    return m


def build_reflect_room(M):
    """The office's fourth wall, behind the camera: never seen by it, only in the monitor's glossy glass (via the
    screen's planar probe). Plaster over green panelling like the other walls, a glazed door through to the shop
    (the frosted glass carries the shop floor's light), coats on hooks, the ceiling."""
    use("REFLECT")
    y = -0.06
    wall = refl_mat("refl_wall", "#d3c3a3")
    panel = refl_mat("refl_panel", "#5d7466")
    trim = refl_mat("refl_trim", "#e4d9c1")
    obs = [boxmm("refl_wall", (-WT, y - 0.05, 0), (W, y, H), wall, bev=0),
           boxmm("refl_dado", (-WT, y, 0), (W, y + 0.012, 0.98), panel, bev=0),
           boxmm("refl_rail", (-WT, y, 0.965), (W, y + 0.032, 1.01), trim, bev=0.004),
           boxmm("refl_skirt", (-WT, y, 0), (W, y + 0.03, 0.1), trim, bev=0.004),
           boxmm("refl_ceiling", (-WT, y - 0.05, H), (W, D, H + 0.03), refl_mat("refl_ceiling", "#e6dcc6", 0.8), bev=0)]
    dx0, dx1 = 0.1, 0.9
    for nm, a, b in [("refl_door_L", (dx0 - 0.07, y, 0), (dx0, y + 0.03, 2.12)),
                     ("refl_door_R", (dx1, y, 0), (dx1 + 0.07, y + 0.03, 2.12)),
                     ("refl_door_T", (dx0 - 0.07, y, 2.05), (dx1 + 0.07, y + 0.03, 2.14))]:
        obs.append(boxmm(nm, a, b, trim, bev=0.004))
    door = refl_mat("refl_door", "#e9e0cc", 0.9)
    for nm, a, b in [("refl_door_bot", (dx0, y + 0.012, 0), (dx1, y + 0.05, 0.42)),
                     ("refl_door_stile_L", (dx0, y + 0.012, 0.42), (dx0 + 0.09, y + 0.05, 2.05)),
                     ("refl_door_stile_R", (dx1 - 0.09, y + 0.012, 0.42), (dx1, y + 0.05, 2.05)),
                     ("refl_door_rail", (dx0, y + 0.012, 1.9), (dx1, y + 0.05, 2.05))]:
        obs.append(boxmm(nm, a, b, door, bev=0.006))
    obs.append(boxmm("refl_door_glass", (dx0 + 0.09, y + 0.02, 0.42), (dx1 - 0.09, y + 0.03, 1.9),
                     refl_mat("refl_glass", "#cfdbe6", 2.2), bev=0))
    for k, x in enumerate((0.24, 0.5, 0.76)):                 # glazing bars
        obs.append(boxmm(f"refl_bar{k}", (x - 0.008, y + 0.03, 0.42), (x + 0.008, y + 0.04, 1.9), door, bev=0))
    obs.append(cyl("refl_handle", 0.012, 0.06, (dx1 - 0.05, y + 0.07, 1.0), refl_mat("refl_brass", "#a98546", 0.9),
                   rot=(90, 0, 0), n=10))
    obs.append(boxmm("refl_hooks", (1.25, y, 1.68), (1.95, y + 0.02, 1.76), trim, bev=0.004))
    coat = refl_mat("refl_coat", "#3e4a36", 0.7)
    obs.append(sphere("refl_coat1", 0.22, (1.42, y + 0.12, 1.35), coat, ico=2, scale=(0.75, 0.45, 1.6)))
    obs.append(sphere("refl_coat2", 0.2, (1.78, y + 0.11, 1.4), refl_mat("refl_jacket", "#1f3a5c", 0.7), ico=2,
                      scale=(0.7, 0.4, 1.4)))
    for ob in obs:
        ob.visible_camera = False
        ob.visible_shadow = False
    return obs


def screen_probe(head, ow, oh, y):
    """A planar light probe on the screen glass: the glossy panel and bezel reflect the room, including what is
    behind the camera (the reflection-only fourth wall)."""
    pd = bpy.data.lightprobes.new("screen_probe", "PLANE")
    pd.influence_distance = 0.012
    try:
        pd.clip_start = 0.004
    except AttributeError:
        pass
    po = bpy.data.objects.new("screen_probe", pd)
    link(po, head, "SET")
    po.location = (0, y, 0)
    po.rotation_euler = (radians(90), 0, 0)
    po.scale = (ow / 2 + 0.004, oh / 2 + 0.004, 1.0)
    return po


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
    box("ws_socket", (0.086, 0.01, 0.086), (3.42, y1 - 0.005, 0.62), mat("plug_white", "#ece8de", 0.4), bev=0.002)
    st = connector("worklamp_plug", "uk", (3.40, y1 - 0.01, 0.618), (0, -1, 0), M)
    cable("worklamp_lead", [(3.1, y1 - 0.96, 1.64), (3.16, y1 - 0.84, 1.42), (3.22, y1 - 0.7, 1.15),
                            (3.27, y1 - 0.6, 0.97), (3.3, y1 - 0.56, 0.9), (3.33, y1 - 0.1, 0.84),
                            (3.4, y1 - 0.03, 0.55), st + Vector((0, 0, -0.02)), st], 0.003, M["plastic_blk"])

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
    build_service_bell(M, (3.12, 3.62, 0.96), 0)
    tc = grp("bell_card", (3.255, 3.6, 0.96), (0, 0, -14))
    card = mat("bell_card", "#f3ecd9", 0.65, spec=0.3)
    gold = mat("bell_card_gold", "#a8823c", 0.4)
    for s in (1, -1):                                         # a folded tent card, printed on both outer faces
        p = grp(f"card_hinge{s}", (0, s * 0.0125, 0.0), (s * 10, 0, 0), parent=tc)   # each side leans from its foot
        boxmm(f"card_side{s}", (-0.05, -0.0007, 0), (0.05, 0.0007, 0.072), card, bev=0, parent=p)
        y, rz = (0.0009, 180) if s > 0 else (-0.0009, 0)
        text(f"card_text{s}", "RING FOR\nSERVICE", "georgiab.ttf", 0.0125, (0, y, 0.038), M["ink"], rot=(90, 0, rz),
             parent=p, line=0.92)
        for k, (w, h) in enumerate(((0.092, 0.062), (0.087, 0.057))):
            for nm, (a0, b0, a1, b1) in (("t", (-w / 2, h / 2 + 0.035, w / 2, h / 2 + 0.0358)),
                                         ("b", (-w / 2, -h / 2 + 0.035, w / 2, -h / 2 + 0.0358)),
                                         ("l", (-w / 2, -h / 2 + 0.035, -w / 2 + 0.0008, h / 2 + 0.0358)),
                                         ("r", (w / 2 - 0.0008, -h / 2 + 0.035, w / 2, h / 2 + 0.0358))):
                boxmm(f"card_rule{s}{k}{nm}", (a0, y - 0.00005, b0), (a1, y + 0.00005, b1), gold, bev=0, parent=p)


def build_service_bell(M, loc, yaw, coll=None, name="bell"):
    """The shop's brass counter bell (Barnaby's emblem): a black enamelled cast-iron base, weighted, lined in brass, on
    a felt pad; a polished brass dome on its post; the plunger through the crown with a mushroom knob."""
    g = grp("service_bell", loc, (0, 0, yaw), coll=coll)
    enamel = mat("bell_enamel", "#141414", 0.22, spec=0.6, coat=0.6)
    lathe(name + "_base", [(0.0, 0.002), (0.05, 0.002), (0.052, 0.005), (0.052, 0.009), (0.0485, 0.0125),
                           (0.044, 0.0142), (0.03, 0.0158), (0.012, 0.0172), (0.0, 0.0175)], n=40, m=enamel, parent=g)
    cyl(name + "_felt", 0.049, 0.002, (0, 0, 0.0), mat("bell_felt", "#2c3b2c", 0.95), n=32, base=True, parent=g)
    torus(name + "_line", 0.0505, 0.0009, (0, 0, 0.0092), M["brass"], nR=40, nr=5, parent=g)
    cyl(name + "_post", 0.006, 0.008, (0, 0, 0.0165), M["brass_old"], n=12, base=True, parent=g)
    outer = [(0.0438 * sin(a), 0.0225 + 0.042 * cos(a)) for a in (radians(t) for t in range(0, 91, 6))]
    inner = [(r * 0.94, 0.0225 + (z - 0.0225) * 0.92) for r, z in outer[::-1]]   # rim back up to the crown
    lathe(name + "_dome", outer + [(0.0425, 0.0221)] + inner[1:], n=48, m=M["brass"], parent=g, angle=70)
    torus(name + "_bead", 0.0436, 0.0011, (0, 0, 0.0238), M["brass"], nR=40, nr=5, parent=g)
    cyl(name + "_collar", 0.0058, 0.0035, (0, 0, 0.064), M["brass_old"], n=16, base=True, bev=0.0008, parent=g)
    cyl(name + "_plunger", 0.0026, 0.016, (0, 0, 0.0665), M["chrome"], n=10, base=True, parent=g)
    lathe(name + "_knob", [(0.0, 0.0805), (0.004, 0.0806), (0.0085, 0.0822), (0.0098, 0.0848), (0.0088, 0.0872),
                           (0.005, 0.0886), (0.0, 0.089)], n=24, m=M["brass"], parent=g)
    return g


# ================================================================ the desk and the PC
DESK_BACK = D - 0.032          # the desk stands against the skirting, so its top stops short of the wall: cable gap


def build_desk(M):
    use("SET")
    boxmm("desk_top", (0.22, 2.06, DZ - 0.045), (2.2, DESK_BACK, DZ), M["oak"], bev=0.012, seg=3)
    boxmm("desk_leg_L", (0.245, 2.1, 0), (0.29, D - 0.04, DZ - 0.045), M["oak"], bev=0.008)
    px0, px1 = 1.76, 2.17
    boxmm("desk_ped", (px0, 2.1, 0.02), (px1, D - 0.04, DZ - 0.045), M["oak"], bev=0.008)
    boxmm("desk_back", (0.29, D - 0.06, 0.32), (px0, D - 0.04, DZ - 0.045), M["oak"], bev=0.004)
    for i, (z0, z1) in enumerate([(0.48, 0.68), (0.27, 0.46), (0.05, 0.25)]):
        dy = -0.2 if i == 1 else 0.0                        # drawer 2 (the backup drawer, README item 2) left open
        g = grp(f"desk_drawer_g{i}", (0, dy, 0))
        boxmm(f"desk_drawer{i}", (px0 + 0.014, 2.083, z0), (px1 - 0.014, 2.1, z1), M["oak_lt"], bev=0.005, parent=g)
        cyl(f"desk_pull{i}", 0.006, 0.11, ((px0 + px1) / 2, 2.066, z1 - 0.045), M["brass_old"], rot=(0, 90, 0), n=8,
            parent=g)
        for sx in (-0.05, 0.05):
            tube(f"desk_pullpost{i}{sx}", ((px0 + px1) / 2 + sx, 2.066, z1 - 0.045),
                 ((px0 + px1) / 2 + sx, 2.084, z1 - 0.045), 0.004, M["brass_old"], n=6, parent=g)
        if i == 1:
            build_drawer_box(M, g, px0 + 0.02, px1 - 0.02, z0 + 0.012, z1 - 0.025)
    # the pedestal's top rail and the dark slot the open drawer came out of
    boxmm("desk_ped_slot", (px0 + 0.016, 2.095, 0.272), (px1 - 0.016, 2.1, 0.458), M["hole"], bev=0)


def build_drawer_box(M, g, x0, x1, z0, z1):
    """Drawer 2's box and what's in it: the backup USB stick on its paper tag (README item 2), CD-R sleeves, a
    stapler, a box of staples, rubber bands. Only the front 20 cm are out of the pedestal."""
    y0, y1, t = 2.1, 2.62, 0.012
    for nm, a, b in [("dr2_side_L", (x0, y0, z0), (x0 + t, y1, z1)), ("dr2_side_R", (x1 - t, y0, z0), (x1, y1, z1)),
                     ("dr2_back", (x0, y1 - t, z0), (x1, y1, z1)), ("dr2_floor", (x0, y0, z0), (x1, y1, z0 + 0.008))]:
        boxmm(nm, a, b, M["oak_lt"], bev=0.002, parent=g)
    zf = z0 + 0.008
    # the USB stick: black body, blue cap, a lanyard loop and Theo's paper tag
    u = grp("usb_stick", (x0 + 0.2, y0 + 0.105, zf + 0.004), (0, 0, 24), parent=g)
    box("usb_body", (0.058, 0.019, 0.009), (0, 0, 0.0045), M["plastic_blk"], bev=0.003, parent=u)
    box("usb_cap", (0.024, 0.0205, 0.0098), (0.039, 0, 0.0049), mat("usb_blue", "#2f63b8", 0.3, coat=0.4), bev=0.003,
        parent=u)
    box("usb_led", (0.004, 0.003, 0.0008), (0.012, 0, 0.0092), mat("usb_led", "#3a4a3a", 0.3), bev=0, parent=u)
    torus("usb_loop", 0.006, 0.0012, (-0.034, 0, 0.0045), M["chrome"], rot=(90, 0, 0), nR=12, nr=5, parent=u)
    curve("usb_string", [(-0.038, 0, 0.004), (-0.05, 0.004, 0.001), (-0.062, 0.002, 0.0008), (-0.07, -0.006, 0.0008)],
          0.0006, M["paper_back"], parent=u)
    tg = grp("usb_tag", (-0.088, -0.012, 0.0009), (0, 0, -20), parent=u)
    rect("usb_tag_card", -0.02, -0.011, 0.02, 0.011, 0, M["manila"], tg)
    disc("usb_tag_hole", 0.016, 0, 0.0018, 0.0002, M["oak_lt"], tg, n=10)
    text("usb_tag_text", "BACKUP\n(Fridays!)", "segoeprb.ttf", 0.0062, (-0.002, 0.0, 0.0003), M["marker"], parent=tg,
         line=0.85, fit=0.03)
    # CD-R sleeves (paper envelopes with a window), a stapler, staples, rubber bands
    for k, (dx, dy, rz) in enumerate(((0.03, 0.135, 4), (0.04, 0.14, -7), (0.035, 0.142, 15))):
        s = grp(f"cd_sleeve{k}", (x0 + dx + 0.06, y0 + dy, zf + 0.0012 * k), (0, 0, rz), parent=g)
        box(f"cd_sleeve{k}_env", (0.125, 0.125, 0.0012), (0, 0, 0.0006), M["paper"], bev=0, parent=s)
        disc(f"cd_sleeve{k}_win", 0, 0, 0.04, 0.0013, mat("sleeve_win", "#d9e0e3", 0.2, spec=0.6), s, n=24)
        disc(f"cd_sleeve{k}_disc", 0, 0, 0.0075, 0.00135, M["cd_top"], s, n=16)
    text("cd_sleeve_label", "backup 09/2026", "segoepr.ttf", 0.0075, (x0 + 0.095, y0 + 0.175, zf + 0.0046), M["marker"],
         rot=(0, 0, 11), parent=g)
    st = grp("stapler", (x1 - 0.06, y0 + 0.07, zf), (0, 0, -70), parent=g)
    box("stapler_base", (0.13, 0.03, 0.012), (0, 0, 0.006), M["plastic_blk"], bev=0.004, parent=st)
    box("stapler_top", (0.12, 0.026, 0.02), (0.004, 0, 0.022), mat("stapler_red", "#9b2f27", 0.35, coat=0.3),
        bev=0.006, parent=st)
    box("staples", (0.045, 0.028, 0.018), (x1 - 0.12, y0 + 0.035, zf + 0.009), mat("staple_box", "#c9a54a", 0.6),
        bev=0.002, parent=g)
    for k in range(3):
        torus(f"rubber_band{k}", 0.018 + 0.002 * k, 0.0012, (x0 + 0.05 + 0.012 * k, y0 + 0.04 - 0.008 * k, zf + 0.0012),
              mat("rubber_band", "#b88a4e", 0.6), nR=16, nr=4, scale=(1.0, 0.7, 0.4), parent=g)


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
    g = grp("tower", (0.37, 2.5, DZ))
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
    # front audio: headphones (green) and mic (pink)
    for i, (x, c) in enumerate(((-0.012, "#5aa55a"), (0.012, "#d98aa8"))):
        torus(f"tower_jack_ring{i}", 0.0042, 0.0011, (x, fy - 0.003, h - 0.252), mat(f"jackring{i}", c, 0.4),
              rot=(90, 0, 0), nR=14, nr=5, parent=g)
        cyl(f"tower_jack{i}", 0.0028, 0.003, (x, fy - 0.0015, h - 0.252), M["hole"], rot=(90, 0, 0), n=10, parent=g)
    port("hp", (-0.012, fy - 0.004, h - 0.252), (0, -1, 0), g)
    # the back: PSU on top (fan, IEC socket, rocker), the I/O shield, seven slot covers with the graphics card's VGA
    ry = d / 2 + 0.0008
    box("psu_plate", (w - 0.012, 0.002, 0.086), (0, ry, h - 0.052), M["steel_dk"], bev=0.001, parent=g)
    torus("psu_fan", 0.034, 0.002, (0.035, ry + 0.001, h - 0.052), M["steel"], rot=(90, 0, 0), nR=24, nr=4, parent=g)
    torus("psu_fan2", 0.022, 0.0016, (0.035, ry + 0.001, h - 0.052), M["steel"], rot=(90, 0, 0), nR=20, nr=4, parent=g)
    for a in (45, 135):
        box(f"psu_fan_bar{a}", (0.07, 0.002, 0.003), (0.035, ry + 0.0012, h - 0.052), M["steel"], rot=(0, a, 0), bev=0,
            parent=g)
    box("psu_iec", (0.028, 0.004, 0.024), (-0.05, ry + 0.001, h - 0.06), M["plastic_blk"], bev=0.001, parent=g)
    port("psu", (-0.05, ry + 0.003, h - 0.06), (0, 1, 0), g)
    box("psu_rocker", (0.012, 0.005, 0.016), (-0.05, ry + 0.002, h - 0.028), M["plastic_blk"], bev=0.001, parent=g)
    box("io_shield", (0.044, 0.0015, 0.165), (0.062, ry, h - 0.2), M["steel"], bev=0.0005, parent=g)
    io = [("ps2_kb", 0.288, "ps2"), ("usb_a", 0.268, "usb"), ("usb_b", 0.256, "usb"), ("usb_c", 0.239, "usb"),
          ("usb_d", 0.227, "usb"), ("lan", 0.207, "lan"), ("aud_blue", 0.183, "jack"), ("aud_green", 0.17, "jack"),
          ("aud_pink", 0.157, "jack")]
    for nm, zz, k in io:
        if k == "ps2":
            cyl("io_ps2", 0.0065, 0.002, (0.062, ry + 0.001, zz), mat("ps2_purple", "#6b4c8f", 0.4), rot=(90, 0, 0),
                n=14, parent=g)
        elif k == "usb":
            box(f"io_{nm}", (0.014, 0.002, 0.006), (0.062, ry + 0.001, zz), M["hole"], bev=0, parent=g)
        elif k == "lan":
            box("io_lan", (0.016, 0.002, 0.014), (0.062, ry + 0.001, zz), M["hole"], bev=0, parent=g)
        else:
            c = {"blue": "#5b86c9", "green": "#5aa55a", "pink": "#d98aa8"}[nm.split("_")[1]]
            torus(f"io_{nm}", 0.0042, 0.0011, (0.062, ry + 0.001, zz), mat("jackring_" + nm, c, 0.4), rot=(90, 0, 0),
                  nR=12, nr=4, parent=g)
        port(nm, (0.062, ry + 0.002, zz), (0, 1, 0), g)
    box("rear_fan_grille", (0.09, 0.0015, 0.09), (-0.035, ry, h - 0.19), M["hole"], bev=0, parent=g)
    for k in range(7):
        zz = 0.035 + k * 0.015
        box(f"slot_cover{k}", (0.125, 0.002, 0.012), (0.0, ry + 0.0005, zz), M["steel"], bev=0.0005, parent=g)
    box("gpu_vga", (0.03, 0.003, 0.01), (0.03, ry + 0.002, 0.125), mat("vga_blue", "#3a5aa8", 0.4), bev=0.001, parent=g)
    box("gpu_dvi", (0.034, 0.003, 0.01), (-0.025, ry + 0.002, 0.125), M["pin_white"], bev=0.001, parent=g)
    port("vga", (0.03, ry + 0.004, 0.125), (0, 1, 0), g)
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
    # connectors under the hump, facing down: VGA (left of the neck) and mains (right)
    box("mon_vga_port", (0.034, 0.012, 0.002), (-0.075, 0.024, -0.1205), M["hole"], bev=0, parent=head)
    box("mon_pwr_port", (0.026, 0.018, 0.002), (0.095, 0.024, -0.1205), M["hole"], bev=0, parent=head)
    port("mon_vga", (-0.075, 0.024, -0.122), (0, 0, -1), head)
    port("mon_pwr", (0.095, 0.024, -0.122), (0, 0, -1), head)
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
    if not SCREEN.get("plain"):
        screen_probe(head, ow, ah + bt + bb, yz - dep / 2 + 0.004)
    # chin details: power LED and a row of buttons (no logo)
    fy = yz - dep / 2 - 0.0012
    disc("mon_led", 0, 0, 0.0018, 0, M["led_blue"], head, n=10, loc=(aw / 2 - 0.007, fy - 0.0005, -ah / 2 - bb / 2),
         rot=(90, 0, 0))
    for i in range(4):
        cyl(f"mon_btn{i}", 0.0022, 0.002, (aw / 2 - 0.018 - i * 0.008, fy, -ah / 2 - bb / 2), M["pc_dk"],
            rot=(90, 0, 0), n=10, parent=head)
    return head


# UK ISO 105-key layout: (row offset in u, [(col, width, height, id, legend), ...]). Legends: "A" single; ("!", "1")
# shifted over unshifted; ("w", "Shift") a word, bottom-left; ("c", "Page\nUp") small words, centred; ("arrow", "←");
# ("num", "7", "Home") a numpad digit with its second function; ("icon", "win" | "menu").
UK_ISO = [
    (0.0, [(0, 1, 1, "Esc", ("c", "Esc"))] +
     [(2 + i, 1, 1, f"F{i + 1}", ("c", f"F{i + 1}")) for i in range(4)] +
     [(6.5 + i, 1, 1, f"F{i + 5}", ("c", f"F{i + 5}")) for i in range(4)] +
     [(11 + i, 1, 1, f"F{i + 9}", ("c", f"F{i + 9}")) for i in range(4)] +
     [(15.25, 1, 1, "PrtSc", ("c", "Print\nScreen")), (16.25, 1, 1, "ScrLk", ("c", "Scroll\nLock")),
      (17.25, 1, 1, "Pause", ("c", "Pause\nBreak"))]),
    (1.5, [(0, 1, 1, "Grave", ("¬", "`"))] +
     [(1 + i, 1, 1, "D" + d, (s, d)) for i, (s, d) in enumerate(zip('!"£$%^&*()', "1234567890"))] +
     [(11, 1, 1, "Minus", ("_", "-")), (12, 1, 1, "Equals", ("+", "=")), (13, 2, 1, "Back", ("arrow", "←")),
      (15.25, 1, 1, "Ins", ("c", "Insert")), (16.25, 1, 1, "Home", ("c", "Home")),
      (17.25, 1, 1, "PgUp", ("c", "Page\nUp")),
      (18.5, 1, 1, "NumLk", ("c", "Num\nLock")), (19.5, 1, 1, "NDiv", "/"), (20.5, 1, 1, "NMul", "*"),
      (21.5, 1, 1, "NSub", "-")]),
    (2.5, [(0, 1.5, 1, "Tab", ("w", "Tab"))] +
     [(1.5 + i, 1, 1, c, c) for i, c in enumerate("QWERTYUIOP")] +
     [(11.5, 1, 1, "LBr", ("{", "[")), (12.5, 1, 1, "RBr", ("}", "]")), (13.5, 1.5, 2, "Enter", ("w", "Enter")),
      (15.25, 1, 1, "Del", ("c", "Delete")), (16.25, 1, 1, "End", ("c", "End")),
      (17.25, 1, 1, "PgDn", ("c", "Page\nDown")),
      (18.5, 1, 1, "N7", ("num", "7", "Home")), (19.5, 1, 1, "N8", ("num", "8", "↑")),
      (20.5, 1, 1, "N9", ("num", "9", "Pg Up")), (21.5, 1, 2, "NAdd", "+")]),
    (3.5, [(0, 1.75, 1, "Caps", ("w", "Caps Lock"))] +
     [(1.75 + i, 1, 1, c, c) for i, c in enumerate("ASDFGHJKL")] +
     [(10.75, 1, 1, "Semi", (":", ";")), (11.75, 1, 1, "Quote", ("@", "'")), (12.75, 1, 1, "Hash", ("~", "#")),
      (18.5, 1, 1, "N4", ("num", "4", "←")), (19.5, 1, 1, "N5", "5"), (20.5, 1, 1, "N6", ("num", "6", "→"))]),
    (4.5, [(0, 1.25, 1, "LShift", ("w", "Shift")), (1.25, 1, 1, "Backslash", ("|", "\\"))] +
     [(2.25 + i, 1, 1, c, c) for i, c in enumerate("ZXCVBNM")] +
     [(9.25, 1, 1, "Comma", ("<", ",")), (10.25, 1, 1, "Period", (">", ".")), (11.25, 1, 1, "Slash", ("?", "/")),
      (12.25, 2.75, 1, "RShift", ("w", "Shift")), (16.25, 1, 1, "Up", ("arrow", "↑")),
      (18.5, 1, 1, "N1", ("num", "1", "End")), (19.5, 1, 1, "N2", ("num", "2", "↓")),
      (20.5, 1, 1, "N3", ("num", "3", "Pg Dn")), (21.5, 1, 2, "NEnter", ("c", "Enter"))]),
    (5.5, [(0, 1.25, 1, "LCtrl", ("w", "Ctrl")), (1.25, 1.25, 1, "LWin", ("icon", "win")),
           (2.5, 1.25, 1, "LAlt", ("w", "Alt")), (3.75, 6.25, 1, "Space", None),
           (10, 1.25, 1, "AltGr", ("w", "Alt Gr")), (11.25, 1.25, 1, "RWin", ("icon", "win")),
           (12.5, 1.25, 1, "Menu", ("icon", "menu")), (13.75, 1.25, 1, "RCtrl", ("w", "Ctrl")),
           (15.25, 1, 1, "Left", ("arrow", "←")), (16.25, 1, 1, "Down", ("arrow", "↓")),
           (17.25, 1, 1, "Right", ("arrow", "→")),
           (18.5, 2, 1, "N0", ("num", "0", "Ins")), (20.5, 1, 1, "NDot", ("num", ".", "Del"))]),
]
WORN_KEYS = ({"Enter", "Space", "Back", "NEnter", "LShift", "LCtrl"} | {"D" + d for d in "1234567890"} |
             {f"N{d}" for d in "0123456789"} | {"NDot"} | set("EASRTONIL"))


def build_keyboard(M):
    """A full-size 2009 UK keyboard (ISO, 105 keys): L-shaped Enter, £ on 3, " on 2, @ by ;, nav cluster, arrows,
    numpad. Tapered caps; the keys Martin and Theo hit most are shiny and their legends half worn away."""
    use("SET")
    g = grp("keyboard", (1.0, 2.21, DZ), (3, 0, 0))
    box("kb_base", (0.465, 0.172, 0.022), (0, 0, 0.011), M["pc"], bev=0.007, seg=2, parent=g)
    box("kb_well", (0.445, 0.128, 0.004), (0, 0.004, 0.0215), M["pc_dk"], bev=0.002, parent=g)
    port("kb_out", (0, 0.088, 0.011), (0, 1, 0), g)
    u = 0.019
    x0, ytop = -22.5 * u / 2, 0.069
    zb, zt, ins, gap = 0.0212, 0.0305, 0.0019, 0.0009
    bm = bmesh.new()
    legends = []

    def cap(outline, mi):
        """Tapered keycap from an axis-aligned outline (bottom) and its inset (top); outline points carry the
        inset direction (ix, iy). Listed clockwise from the top-left; built counter-clockwise (normals out)."""
        outline = outline[::-1]
        lo = [bm.verts.new((x, y, zb)) for x, y, _, _ in outline]
        hi = [bm.verts.new((x + ix * ins, y + iy * ins, zt)) for x, y, ix, iy in outline]
        n = len(outline)
        bm.faces.new(hi).material_index = mi
        for k in range(n):
            bm.faces.new((lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k])).material_index = mi

    for ry, keys in UK_ISO:
        for col, wu, hu, kid, leg in keys:
            mi = 1 if kid in WORN_KEYS else 0
            xa, xb = x0 + col * u + gap, x0 + (col + wu) * u - gap
            ya, yb = ytop - ry * u - gap, ytop - (ry + hu) * u + gap          # ya top edge, yb bottom edge
            if kid == "Enter":                                                 # ISO: 1.5u on top, 1.25u below
                xm = x0 + (col + 0.25) * u + gap
                ymid = ytop - (ry + 1) * u - gap
                cap([(xa, ya, 1, -1), (xb, ya, -1, -1), (xb, yb, -1, 1), (xm, yb, 1, 1), (xm, ymid, 1, 1),
                     (xa, ymid, 1, 1)], mi)
                yb = ymid + 2 * gap                                            # legends go on the top part
            else:
                cap([(xa, ya, 1, -1), (xb, ya, -1, -1), (xb, yb, -1, 1), (xa, yb, 1, 1)], mi)
            if leg is not None:
                legends.append((kid, leg, (xa + xb) / 2, (ya + yb) / 2, xa + ins, yb + ins, xb - ins, ya - ins,
                                kid in WORN_KEYS))
    keys_m = [M["pc_dk"], mat("key_worn", "#2a2a2c", 0.2, spec=0.65)]
    caps = finish("kb_caps", bm, keys_m, g, angle=30)
    bevel(caps, 0.0011, 1, 30)
    leg_m, leg_w = mat("legend", "#a9abaf", 0.5), mat("legend_worn", "#5c5e62", 0.4)
    z = zt + 0.0002
    for kid, leg, cx, cy, l, b, r, t, worn in legends:
        lm = leg_w if worn else leg_m
        nm = f"kb_leg_{kid}"
        if isinstance(leg, str):
            text(nm, leg, "verdana.ttf", 0.0048 if leg.isalpha() else 0.0044, (cx, cy, z), lm, parent=g)
        elif leg[0] == "c":
            two = "\n" in leg[1]
            text(nm, leg[1], "verdana.ttf", 0.0021 if two else (0.0029 if len(leg[1]) <= 3 else 0.0023),
                 (cx, cy, z), lm, parent=g, line=0.95, fit=r - l - 0.001)
        elif leg[0] == "w":
            text(nm, leg[1], "verdana.ttf", 0.0024, (l + 0.0012, b + 0.0016, z), lm, ax="LEFT", ay="BOTTOM", parent=g,
                 fit=r - l - 0.002)
            sym = {"Enter": "↵", "Tab": "⇥", "LShift": "⇧", "RShift": "⇧"}.get(kid)
            if sym:
                at = (r - 0.0035, t - 0.0045, z) if kid == "Enter" else (l + 0.0035, t - 0.0045, z)
                text(nm + "_sym", sym, "seguisym.ttf", 0.0048, at, lm, parent=g)
        elif leg[0] == "arrow":
            text(nm, leg[1], "tahoma.ttf", 0.0052, (cx, cy, z), lm, parent=g)
        elif leg[0] == "num":
            text(nm, leg[1], "verdana.ttf", 0.0042, (cx, cy + 0.0018, z), lm, parent=g)
            text(nm + "_2", leg[2], "tahoma.ttf" if len(leg[2]) == 1 else "verdana.ttf",
                 0.0034 if len(leg[2]) == 1 else 0.0019, (cx, cy - 0.0036, z), lm, parent=g)
        elif leg[0] == "icon":
            ig = grp(nm, (cx, cy, z), parent=g)
            if leg[1] == "win":                                                # a plain window outline, no logo
                bars = ((-0.0026, 0.0018, 0.0026, 0.0024), (-0.0026, -0.0024, 0.0026, -0.0018),
                        (-0.0026, -0.0024, -0.002, 0.0024), (0.002, -0.0024, 0.0026, 0.0024),
                        (-0.0026, 0.0009, 0.0026, 0.0013))
            else:                                                              # menu: a page with lines
                bars = ((-0.0022, 0.0026, 0.0022, 0.0031), (-0.0022, -0.0031, 0.0022, -0.0026),
                        (-0.0022, -0.0031, -0.0017, 0.0031), (0.0017, -0.0031, 0.0022, 0.0031),
                        (-0.0011, 0.0012, 0.0011, 0.0016), (-0.0011, -0.0002, 0.0011, 0.0002),
                        (-0.0011, -0.0016, 0.0011, -0.0012))
            for k, (a0, b0, a1, b1) in enumerate(bars):
                rect(f"{nm}_{k}", a0, b0, a1, b1, 0, lm, ig)
        else:                                                                  # shifted over unshifted
            text(nm + "_s", leg[0], "verdana.ttf", 0.0036, (cx, cy + 0.0026, z), lm, parent=g)
            text(nm, leg[1], "verdana.ttf", 0.0036, (cx, cy - 0.0026, z), lm, parent=g)
    # lock lights above the numpad, each with its little label
    for i, (nm, lm, lab) in enumerate([("num", M["led_green"], "Num"), ("caps", M["led_off"], "Caps"),
                                        ("scroll", M["led_off"], "Scroll")]):
        x = x0 + (19.0 + i * 1.0) * u
        box(f"kb_led_{nm}", (0.004, 0.003, 0.001), (x, ytop - 0.35 * u, 0.0222), lm, bev=0, parent=g)
        text(f"kb_led_lab_{nm}", lab, "verdana.ttf", 0.0016, (x, ytop - 0.72 * u, 0.0222), leg_m, parent=g)
    return g


def key_shape(name, parent, loc, yaw, length, m, M, bow_r=0.0115, tilt=(0, 0, 0)):
    """A flat cylinder-lock key: a round bow with a hole, a grooved blade with cuts."""
    k = grp(name, loc, (tilt[0], tilt[1], yaw), parent=parent)
    annulus(name + "_bow", circ_pts(0, 0, bow_r, n=20), circ_pts(-bow_r * 0.5, 0, 0.0032, n=20), m=m, parent=k,
            thick=0.0024, bev=0.0004)
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


def build_backoffice_key(M, kb):
    """Thursday night: Theo slides ONE key off his own ring (he keeps the ring and its chainring fob) and leaves it on
    the keyboard for Martin: a brass key on a small split ring with a round, metal-rimmed paper tag, BACK OFFICE in
    Theo's hand."""
    use("THEO")
    g = grp("backoffice_key", (0.052, 0.016, 0.0309), (0, 0, -12), parent=kb)
    rr = 0.0098
    pts = [(rr * cos(t), rr * sin(t), 0.0011 + 0.0012 * t / (4 * pi))
           for t in (4 * pi * i / 47 for i in range(48))]
    curve("split_ring", pts, 0.0006, M["chrome"], parent=g, res=3, bres=1)
    # the tag: white card in a thin steel rim, its eyelet riding on the ring
    tg = grp("key_tag", (-0.0255, -0.0035, 0.0002), (0, 0, 6), parent=g)
    disc("tag_card", 0, 0, 0.0142, 0.0004, mat("tag_card", "#f4efe2", 0.7, spec=0.3), tg, n=40)
    disc("tag_back", 0, 0, 0.0142, 0.0001, M["paper_back"], tg, n=40)
    torus("tag_rim", 0.0145, 0.0008, (0, 0, 0.0004), M["steel"], nR=40, nr=6, parent=tg).scale = (1, 1, 0.7)
    torus("tag_eyelet", 0.0022, 0.0006, (0.0159, 0.0, 0.0004), M["steel"], nR=12, nr=4, parent=tg)
    text("tag_text", "BACK\nOFFICE", "segoeprb.ttf", 0.0082, (-0.0005, 0.0008, 0.00045), M["marker"], parent=tg,
         line=0.78, fit=0.0235, rot=(0, 0, 4), extrude=0.00005)
    curve("tag_underline", [(-0.009, -0.0068, 0.00046), (0.0, -0.0074, 0.00046), (0.009, -0.0066, 0.00046)], 0.00028,
          M["marker"], parent=tg, res=4, bres=1)
    # the key: bow hole on the ring, lying flat on the keys, a bright brass cylinder key
    a = radians(-28)
    hole = Vector((rr * cos(a), rr * sin(a), 0.0))
    bow_r = 0.0118
    key_shape("key_backoffice", g, hole + 0.5 * bow_r * Vector((cos(a), sin(a), 0)) + Vector((0, 0, 0.0013)),
              math.degrees(a), 0.036, M["brass"], M, bow_r=bow_r, tilt=(0, 3, 0))
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
    port("mouse", (0, 0.057, 0.012), (0, 1, 0.15), m)
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
            # the powered speaker: its satellite lead goes in at the back, and two leads go to the PC (audio, USB power)
            box("spk_R_in", (0.012, 0.002, 0.008), (0.022, 0.0455, 0.03), M["hole"], bev=0, parent=g)
            port("spk_in", (0.022, 0.047, 0.03), (0, 1, 0), g)
            port("spk_audio", (-0.012, 0.046, 0.026), (0, 1, 0), g)
            port("spk_usb", (-0.026, 0.046, 0.026), (0, 1, 0), g)
        else:
            port("spk_out", (0.0, 0.046, 0.03), (0, 1, 0), g)


def build_lamp(M):
    """Mustard anglepoise between the tower and the monitor, head over the keyboard."""
    use("SET")
    base = Vector((0.605, 2.655, DZ))
    lathe("lamp_base", [(0.0, 0.0), (0.075, 0.0), (0.078, 0.008), (0.07, 0.026), (0.03, 0.034), (0.0, 0.036)], n=24,
          loc=base, m=M["mustard"])
    cyl("lamp_switch", 0.008, 0.008, base + Vector((0.035, -0.035, 0.026)), M["plastic_blk"], n=10, base=True)
    pe = port("lamp", base + Vector((0.0, 0.074, 0.01)), (0, 1, 0), None)
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


def bush_end(name, port_name, M, coll=None, out=0.02):
    """The device end of a hard-wired lead: a rubber bush on the port; returns the last two cable points."""
    at, d = port_frame(port_name)
    p = connector(name + "_bush", "relief", at, d, M, coll=coll)
    return [p + d * out, p]


def build_cables(M):
    """Every lead on the desk ends in something. Data and audio run along the back of the desk, behind the monitor,
    to the tower's rear I/O; mains leads drop down the gap between the desk and the wall (the desk stands against the
    skirting) to a four-way strip on the floor, which plugs into a double socket on the wall under the desk."""
    use("SET")
    blk = M["plastic_blk"]
    lane_z = DZ + 0.0026
    BACK = DESK_BACK
    gap_y = (BACK + D - 0.012) / 2                            # the 2 cm slot between desk and panelling

    def lane(y, xs):
        return [(x, y, lane_z) for x in xs]

    def tower_rise(x_port, z_port, y_lane, x_lane):
        """From a rear port: bend down over the desk's back edge and settle into the cable lane."""
        return [(x_port + 0.004, BACK + 0.002, z_port - 0.03), (x_port + 0.02, BACK - 0.004, DZ + 0.05),
                (x_lane - 0.03, y_lane + 0.003, DZ + 0.008)]

    # tower-end plugs and their runs (built from the tower outwards)
    def tower_run(name, kind, port_name, r, y_lane, path, end, m=blk):
        at, d = port_frame(port_name)
        st = connector(name + "_plug", kind, at, d, M)
        pts = [st, st + d * 0.006] + tower_rise(at.x, at.z, y_lane, 0.5) + lane(y_lane, (0.5,)) + path + end
        return cable(name, pts, r, m)

    # keyboard: from the purple PS/2 socket along the back, round the left of the monitor base, into its back
    tower_run("kb_cable", "ps2", "ps2_kb", 0.0022, 2.746,
              lane(2.746, (0.66, 0.8)) + [(0.85, 2.68, lane_z), (0.86, 2.58, lane_z), (0.87, 2.47, lane_z),
                                          (0.95, 2.4, lane_z), (1.0, 2.33, lane_z)],
              bush_end("kb_lead", "kb_out", M))
    # mouse: off the back of the pad, left of the right speaker, along the back, into a USB port
    tower_run("mouse_cable", "usb", "usb_a", 0.0018, 2.742,
              lane(2.742, (0.7, 1.0, 1.17)) + [(1.23, 2.66, lane_z), (1.25, 2.53, lane_z), (1.29, 2.43, lane_z),
                                               (1.39, 2.37, DZ + 0.0055), (1.42, 2.335, DZ + 0.0055)],
              bush_end("mouse_lead", "mouse", M, out=0.015))
    # powered speaker (right): audio into the green jack, USB for power
    for nm, kind, prt, src, yl in (("spk_audio_cable", "jack", "aud_green", "spk_audio", 2.754),
                                   ("spk_usb_cable", "usb", "usb_b", "spk_usb", 2.758)):
        tower_run(nm, kind, prt, 0.0016, yl,
                  lane(yl, (0.75, 1.0, 1.24)) + [(1.31, yl - 0.04, lane_z), (1.325, 2.62, lane_z),
                                                 (1.33, 2.575, DZ + 0.01)],
                  bush_end(nm + "_lead", src, M, out=0.015))
    # satellite (left) to the powered speaker: round the lamp base, along the back, into its input jack
    at, d = port_frame("spk_in")
    st = connector("spk_link_plug", "jack", at, d, M)
    cable("spk_link", [st, st + d * 0.012, (1.37, 2.6, lane_z), (1.34, 2.68, lane_z), (1.28, 2.762, lane_z)] +
          lane(2.762, (1.0, 0.8)) + [(0.735, 2.74, lane_z), (0.71, 2.64, lane_z), (0.69, 2.57, lane_z),
                                     (0.66, 2.556, DZ + 0.02)] + bush_end("spk_link_lead", "spk_out", M, out=0.012),
          0.0015, blk)
    # monitor: VGA down behind the neck, over the back of the base, along to the graphics card (ferrite bead)
    at, d = port_frame("mon_vga")
    st = connector("vga_mon_plug", "vga", at, d, M)
    cyl("vga_ferrite", 0.0072, 0.03, st + d * 0.03, blk, n=12, bev=0.002).rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    at2, d2 = port_frame("vga")
    st2 = connector("vga_pc_plug", "vga", at2, d2, M)
    cable("vga_cable", [st, st + d * 0.05, st + d * 0.075 + Vector((0, 0.03, 0)), (at.x, 2.615, DZ + 0.018),
                        (at.x - 0.01, 2.67, lane_z), (at.x - 0.04, 2.75, lane_z)] +
          lane(2.75, (0.75, 0.55))[::1] + tower_rise(at2.x, at2.z, 2.75, 0.5)[::-1] + [st2 + d2 * 0.006, st2],
          0.0034, blk)
    # mains: monitor, lamp and tower leads go down the gap behind the desk to the strip on the floor
    strip_x0, strip_x1, sy, sz = 0.4, 0.84, 2.705, 0.042
    boxmm("strip_body", (strip_x0, sy - 0.032, 0.0), (strip_x1, sy + 0.032, sz), mat("strip_white", "#e9e5da", 0.45),
          bev=0.008, seg=2)
    sock_x = [0.465, 0.565, 0.665, 0.765]
    for i, x in enumerate(sock_x):
        box(f"strip_socket{i}", (0.056, 0.05, 0.001), (x, sy, sz + 0.0004), mat("strip_face", "#dedad0", 0.5), bev=0)
        for k, (dx, dy, w, h) in enumerate(((0.0, 0.011, 0.004, 0.008), (-0.011, -0.008, 0.008, 0.004),
                                            (0.011, -0.008, 0.008, 0.004))):
            box(f"strip_slot{i}{k}", (w, h, 0.001), (x + dx, sy + dy, sz + 0.001), M["hole"], bev=0)
    box("strip_switch", (0.014, 0.022, 0.006), (0.818, sy, sz + 0.003), mat("strip_red", "#d1402c", 0.3, emit="#ff4a2a",
                                                                          estr=1.5), bev=0.002)
    drops = {"tower": (0.33, sock_x[0]), "lamp": (0.6, sock_x[1]), "monitor": (1.08, sock_x[2])}

    def mains(name, top_pts, xd, xs):
        st = connector(name + "_uk", "uk", (xs, sy, sz), (0, 0, 1), M, spin=180)
        down = [(xd, gap_y, DZ - 0.04), (xd, gap_y, 0.3), (xd + 0.01, gap_y, 0.16), (xd + 0.01, BACK - 0.012, 0.115),
                (xd, BACK - 0.02, 0.03), ((xd + xs) / 2, sy + 0.05, 0.008), (xs, sy + 0.048, 0.03)]
        return cable(name, top_pts + down + [st + Vector((0, 0.01, 0.0)), st], 0.0031, blk)

    at, d = port_frame("psu")
    st = connector("psu_plug", "iec", at, d, M)
    mains("tower_power", [st, st + d * 0.004, (at.x, gap_y, at.z - 0.03), (at.x, gap_y, DZ + 0.1)], *drops["tower"])
    at, d = port_frame("mon_pwr")
    st = connector("mon_pwr_plug", "iec", at, d, M)
    mains("monitor_power", [st, st + d * 0.02, (at.x, 2.6, DZ + 0.03), (at.x, 2.65, lane_z), (1.09, 2.74, lane_z),
                            (1.085, BACK + 0.004, DZ - 0.01)], *drops["monitor"])
    lamp_end = bush_end("lamp_lead", "lamp", M, out=0.01)[::-1]
    mains("lamp_power", lamp_end + [(0.6, BACK - 0.008, lane_z), (0.6, BACK + 0.006, DZ - 0.012)], *drops["lamp"])
    # the strip's own lead to the double socket on the wall under the desk
    wx, wz, wy = 0.36, 0.25, D - 0.012
    box("wall_socket", (0.146, 0.009, 0.086), (wx, wy - 0.0045, wz), mat("plug_white", "#ece8de", 0.4), bev=0.002)
    for k, sx in enumerate((-0.036, 0.036)):
        box(f"wall_rocker{k}", (0.012, 0.004, 0.009), (wx + sx + 0.022, wy - 0.01, wz + 0.028), M["pin_white"],
            bev=0.001)
        if k:
            for j, (dx, dz, w, h) in enumerate(((0.0, 0.011, 0.004, 0.008), (-0.011, -0.008, 0.008, 0.004),
                                                (0.011, -0.008, 0.008, 0.004))):
                box(f"wall_slot{j}", (w, 0.001, h), (wx + sx + dx, wy - 0.0095, wz + dz - 0.004), M["hole"], bev=0)
    st = connector("strip_wall_uk", "uk", (wx - 0.036, wy - 0.009, wz - 0.004), (0, -1, 0), M)
    lead_in = Vector((strip_x0 - 0.004, sy, 0.02))
    cable("strip_lead", [st, st + Vector((0, 0, -0.012)), (wx - 0.036, wy - 0.03, 0.12), (wx - 0.03, BACK - 0.03, 0.03),
                         (strip_x0 - 0.04, sy + 0.02, 0.006), lead_in - Vector((0.02, 0, 0.012)), lead_in],
          0.0035, blk)
    cyl("strip_lead_relief", 0.0055, 0.016, lead_in + Vector((0.006, 0, 0)), blk, rot=(0, 90, 0), n=10)


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


# ================================================================ the 2009 photo: a mini-set, rendered to a print
def _limb(name, a, b, r, m, parent, r2=None, n=10):
    t = tube(name, a, b, r, m, n=n, parent=parent, r2=r2)
    sphere(name + "_j", r * 1.02, a, m, seg=10, rings=6, parent=parent)
    return t


def _face(name, g, head_z, r, M, skin, brow, smile_w=0.03):
    eye = mat("ph_eye", "#2a221d", 0.4)
    for s in (-1, 1):
        sphere(f"{name}_eye{s}", r * 0.11, (s * r * 0.36, -r * 0.9, head_z + r * 0.12), eye, seg=8, rings=5, parent=g)
        box(f"{name}_brow{s}", (r * 0.32, r * 0.06, r * 0.07), (s * r * 0.37, -r * 0.93, head_z + r * 0.34), brow,
            rot=(0, -s * 6, 0), bev=r * 0.02, parent=g)
        sphere(f"{name}_ear{s}", r * 0.2, (s * r * 0.98, 0, head_z + 0.0), skin, seg=8, rings=6, parent=g,
               scale=(0.5, 1.0, 1.25))
    cyl(f"{name}_nose", r * 0.12, r * 0.28, (0, -r * 1.0, head_z - r * 0.05), skin, r2=r * 0.05, rot=(90, 0, 0), n=8,
        parent=g)
    curve(f"{name}_smile", [(-smile_w, -r * 0.93, head_z - r * 0.38), (0, -r * 0.97, head_z - r * 0.48),
                            (smile_w, -r * 0.93, head_z - r * 0.38)], r * 0.035, mat("ph_mouth", "#7a3a2e", 0.5),
          parent=g, res=6, bres=1)


def photo_figures(M):
    """Theo, 14, red hoodie and shaggy 2009 fringe, holding up the CD-R; Martin, 44, flat cap, moustache, work apron,
    his arm round Theo's shoulders. Simple, low-poly, the same miniature style as the desk."""
    skin_t, skin_m = mat("ph_skin_t", "#e3b28f", 0.55), mat("ph_skin_m", "#d29c78", 0.55)
    hoodie, jeans = mat("ph_hoodie", "#b0473b", 0.85), mat("ph_jeans", "#4b6288", 0.8)
    hair_t = mat("ph_hair_t", "#3b2a20", 0.7)
    # ---- Theo (to the left in the photo)
    t = grp("theo14", (-0.27, -1.0, 0.0), (0, 0, 8))
    for s in (-1, 1):
        box(f"t_shoe{s}", (0.1, 0.25, 0.075), (s * 0.09, -0.03, 0.0375), mat("ph_canvas", "#d9d5cc", 0.7), bev=0.03,
            parent=t)
        box(f"t_sole{s}", (0.104, 0.254, 0.02), (s * 0.09, -0.03, 0.01), mat("ph_sole", "#efede6", 0.6), bev=0.008,
            parent=t)
        _limb(f"t_leg{s}", (s * 0.088, 0.0, 0.08), (s * 0.095, 0.0, 0.8), 0.062, jeans, t, r2=0.07)
    box("t_torso", (0.37, 0.22, 0.54), (0, 0, 1.06), hoodie, bev=0.07, seg=3, parent=t)
    box("t_pocket", (0.22, 0.02, 0.12), (0, -0.108, 0.9), mat("ph_hoodie_dk", "#97392f", 0.85), bev=0.02, parent=t)
    sphere("t_hood", 0.15, (0, 0.08, 1.31), hoodie, seg=14, rings=8, parent=t, scale=(1.1, 0.75, 0.55))
    for s in (-1, 1):
        tube(f"t_string{s}", (s * 0.035, -0.115, 1.3), (s * 0.04, -0.12, 1.16), 0.006, mat("ph_string", "#ece6da", 0.6),
             n=6, parent=t)
    cyl("t_neck", 0.048, 0.1, (0, 0, 1.36), skin_t, n=12, parent=t)
    hz = 1.49
    sphere("t_head", 0.105, (0, 0, hz), skin_t, seg=18, rings=12, parent=t, scale=(1.0, 0.98, 1.12))
    _face("t", t, hz, 0.105, M, skin_t, hair_t, 0.028)
    sphere("t_hair_cap", 0.116, (0, 0.012, hz + 0.03), hair_t, seg=16, rings=10, parent=t, scale=(1.02, 1.02, 0.95))
    for k, (x, z, ry, rz, L) in enumerate(((-0.01, 0.085, 72, -18, 0.12), (0.04, 0.078, 62, -26, 0.12),
                                          (0.075, 0.055, 55, -38, 0.09), (-0.055, 0.08, 82, 10, 0.07))):
        cyl(f"t_fringe{k}", 0.028, L, (x, -0.09, hz + z), hair_t, r2=0.004, rot=(10, ry, rz), n=8, parent=t)
    for k in range(5):                                       # shaggy back and sides
        a = radians(-70 + 35 * k)
        cyl(f"t_tuft{k}", 0.035, 0.09, (0.1 * sin(a), 0.07 * cos(a) + 0.03, hz - 0.03), hair_t, r2=0.005,
            rot=(160 - 20 * cos(a), 0, math.degrees(a)), n=7, parent=t)
    # arms up, both hands holding the CD-R out to the camera
    cdc = Vector((0.0, -0.36, 1.2))
    for s in (-1, 1):
        sh, el = Vector((s * 0.2, 0.0, 1.26)), Vector((s * 0.2, -0.16, 1.02))
        hand = cdc + Vector((s * 0.066, 0.01, -0.01))
        _limb(f"t_upper{s}", sh, el, 0.055, hoodie, t)
        _limb(f"t_fore{s}", el, hand + Vector((s * 0.01, 0.03, -0.02)), 0.05, hoodie, t, r2=0.045)
        sphere(f"t_hand{s}", 0.038, hand, skin_t, seg=10, rings=7, parent=t, scale=(0.75, 1.0, 1.0))
    cdg = grp("t_cd", cdc, (88, 0, -8), parent=t)
    cyl("cd_body", 0.06, 0.0012, (0, 0, 0), mat("ph_cdr", "#c9cfd4", 0.22, metal=0.6), n=40, parent=cdg)
    cyl("cd_label", 0.0585, 0.0004, (0, 0, 0.0008), mat("ph_cdr_top", "#e2e3df", 0.35), n=40, parent=cdg)
    cyl("cd_hub", 0.018, 0.0006, (0, 0, 0.0011), mat("ph_cdr_hub", "#b9c0c4", 0.3, metal=0.4), n=24, parent=cdg)
    cyl("cd_hole", 0.0075, 0.0008, (0, 0, 0.0013), mat("ph_cdr_hole", "#1a1a1a", 0.5), n=16, parent=cdg)
    text("cd_text", "SHOP SYSTEM", "segoeprb.ttf", 0.0135, (0, 0.032, 0.0013), M["marker"], parent=cdg, fit=0.08)
    text("cd_text2", "v1  :)", "segoeprb.ttf", 0.014, (0.002, -0.034, 0.0013), M["marker"], parent=cdg)
    # ---- Martin (to the right), his right arm round Theo
    m = grp("martin44", (0.24, -0.95, 0.0), (0, 0, -6))
    shirt, trous = mat("ph_shirt", "#4a6288", 0.8), mat("ph_trousers", "#2c3038", 0.85)
    apron = mat("ph_apron", "#7c5636", 0.9)
    for s in (-1, 1):
        box(f"m_boot{s}", (0.115, 0.29, 0.1), (s * 0.1, -0.03, 0.05), mat("ph_boot", "#4a3324", 0.5), bev=0.035,
            parent=m)
        _limb(f"m_leg{s}", (s * 0.1, 0.0, 0.09), (s * 0.105, 0.0, 0.88), 0.074, trous, m, r2=0.08)
    box("m_torso", (0.47, 0.27, 0.62), (0, 0, 1.2), shirt, bev=0.085, seg=3, parent=m)
    prism("m_apron", [(-0.2, 0.0), (0.2, 0.0), (0.18, 0.86), (0.13, 0.95), (-0.13, 0.95), (-0.18, 0.86)], 0.012,
          loc=(0, -0.142, 0.52), rot=(90, 0, 0), m=apron, bev=0.004, parent=m)
    box("m_apron_pocket", (0.22, 0.012, 0.1), (0, -0.152, 0.86), mat("ph_apron_dk", "#6a4a2e", 0.9), bev=0.01, parent=m)
    tube("m_pencil", (0.06, -0.156, 0.91), (0.072, -0.158, 0.99), 0.006, M["pencil"], n=6, parent=m)
    for s in (-1, 1):
        tube(f"m_strap{s}", (s * 0.12, -0.15, 1.46), (s * 0.08, -0.04, 1.52), 0.012, apron, n=6, parent=m)
    cyl("m_neck", 0.056, 0.1, (0, 0, 1.53), skin_m, n=12, parent=m)
    hz = 1.665
    sphere("m_head", 0.115, (0, 0, hz), skin_m, seg=18, rings=12, parent=m, scale=(1.0, 0.98, 1.1))
    _face("m", m, hz, 0.115, M, skin_m, mat("ph_brow_m", "#6b5a4c", 0.7), 0.026)
    sphere("m_tache", 0.04, (0, -0.105, hz - 0.035), mat("ph_tache", "#6b5a4c", 0.8), seg=10, rings=6, parent=m,
           scale=(1.3, 0.45, 0.42))
    cap = mat("ph_cap", "#5a554e", 0.9)
    sphere("m_cap", 0.125, (0, 0.0, hz + 0.055), cap, seg=16, rings=10, parent=m, scale=(1.02, 1.08, 0.5))
    box("m_peak", (0.2, 0.1, 0.018), (0, -0.115, hz + 0.05), cap, rot=(-10, 0, 0), bev=0.008, parent=m)
    # his right arm (nearest Theo) round Theo's shoulders, the hand on Theo's far shoulder
    sh = Vector((-0.24, 0.0, 1.43))
    el = Vector((-0.42, 0.06, 1.38))
    th_far = Vector((-0.66, -0.02, 1.31))                    # the top of Theo's far shoulder, in Martin's space
    _limb("m_upper_r", sh, el, 0.064, shirt, m)
    _limb("m_fore_r", el, th_far + Vector((0.05, 0.03, 0.03)), 0.05, shirt, m, r2=0.046)
    sphere("m_hand_r", 0.043, th_far + Vector((0.0, -0.02, 0.0)), skin_m, seg=10, rings=7, parent=m,
           scale=(0.9, 1.2, 0.55))
    # his left arm down, thumb in the apron pocket
    sh2, el2 = Vector((0.25, 0.0, 1.43)), Vector((0.3, -0.04, 1.12))
    _limb("m_upper_l", sh2, el2, 0.064, shirt, m)
    _limb("m_fore_l", el2, Vector((0.12, -0.17, 0.9)), 0.052, skin_m, m, r2=0.046)
    sphere("m_hand_l", 0.045, (0.11, -0.17, 0.9), skin_m, seg=10, rings=7, parent=m)


def photo_shopfront(M):
    """The shop in 2009: green fascia with gilt letters, the window with a bike in it, the door, the pavement."""
    green = mat("ph_green", "#2f4d3c", 0.45, coat=0.3)
    cream = mat("ph_cream", "#e6dcc3", 0.5)
    gilt = mat("ph_gilt", "#d4ad5c", 0.25, metal=1.0)
    boxmm("ph_pavement", (-4, -6, -0.05), (4, 0.0, 0.0), brick("ph_slabs", "#a7a39b", "#9b978f", "#7d7a74", scale=1.3,
                                                                      row=0.5, width=0.5), bev=0)
    boxmm("ph_kerb", (-4, -6.0, -0.05), (4, -5.8, 0.02), M["concrete"], bev=0.01)
    boxmm("ph_bricks", (-5, 0.0, 3.12), (5, 0.4, 6.0), M["outside_brick"], bev=0)
    boxmm("ph_bricks_L", (-5, 0.0, 0.0), (-2.66, 0.4, 3.12), M["outside_brick"], bev=0)
    boxmm("ph_bricks_R", (2.41, 0.0, 0.0), (5, 0.4, 3.12), M["outside_brick"], bev=0)
    boxmm("ph_back", (-2.66, 0.4, 0.0), (2.41, 0.5, 3.12), mat("ph_inside", "#3a2c22", 0.9), bev=0)
    boxmm("ph_riser", (-2.3, -0.12, 0.0), (0.6, -0.02, 0.5), green, bev=0.01)
    boxmm("ph_sill", (-2.32, -0.16, 0.5), (0.62, -0.02, 0.56), cream, bev=0.01)
    for nm, a, b in [("ph_win_L", (-2.34, -0.1, 0.56), (-2.26, -0.03, 2.5)), ("ph_win_R", (0.56, -0.1, 0.56),
                                                                             (0.64, -0.03, 2.5)),
                     ("ph_win_T", (-2.34, -0.1, 2.44), (0.64, -0.03, 2.52)), ("ph_transom", (-2.3, -0.1, 2.1),
                                                                             (0.6, -0.03, 2.16)),
                     ("ph_mullion", (-0.89, -0.1, 0.56), (-0.83, -0.03, 2.1))]:
        boxmm(nm, a, b, cream, bev=0.008)
    boxmm("ph_glass", (-2.3, -0.06, 0.56), (0.6, -0.055, 2.44), mat("ph_glass", "#28343a", 0.04, spec=0.8, alpha=0.22),
          bev=0)
    boxmm("ph_display", (-2.3, -0.02, 0.5), (0.6, 0.4, 0.56), M["oak_lt"], bev=0)
    bike("ph_bike", (-1.45, 0.2, 0.56), 0, mat("ph_bike", "#3e7c74", 0.3, coat=0.5), M)
    text("ph_win_text", "CYCLE REPAIRS  ·  SALES", "georgiab.ttf", 0.13, (-0.85, -0.062, 2.3), gilt, rot=(90, 0, 0),
         fit=2.6)
    og = grp("ph_open", (0.05, -0.08, 1.6), (90, 0, 0))
    box("ph_open_card", (0.32, 0.12, 0.006), (0, 0, 0), M["pin_white"], bev=0.004, parent=og)
    text("ph_open_t", "OPEN", "verdanab.ttf", 0.075, (0, 0, 0.0035), M["red_ink"], parent=og)
    for nm, a, b in (("ph_reveal_L", (0.64, -0.06, 0.0), (0.7, 0.1, 2.5)), ("ph_reveal_R", (1.8, -0.06, 0.0),
                                                                            (1.86, 0.1, 2.5)),
                     ("ph_reveal_T", (0.64, -0.06, 2.2), (1.86, 0.1, 2.52))):
        boxmm(nm, a, b, cream, bev=0.006)
    boxmm("ph_door", (0.76, 0.05, 0.02), (1.74, 0.1, 2.2), green, bev=0.012)
    boxmm("ph_door_glass", (0.86, 0.04, 1.05), (1.64, 0.05, 2.08), mat("ph_glass", "#28343a", 0.04), bev=0)
    boxmm("ph_door_panel", (0.88, 0.04, 0.15), (1.62, 0.05, 0.9), green, bev=0.01)
    boxmm("ph_letterbox", (1.1, 0.035, 0.95), (1.4, 0.045, 0.99), gilt, bev=0.004)
    cyl("ph_knob", 0.03, 0.05, (0.86, 0.02, 1.0), gilt, rot=(90, 0, 0), n=14)
    boxmm("ph_step", (0.64, -0.3, 0.0), (1.86, 0.06, 0.08), M["concrete"], bev=0.01)
    for nm, x in (("ph_pil_L", -2.55), ("ph_pil_M", 0.6), ("ph_pil_R", 1.86)):
        w = 0.2 if nm != "ph_pil_M" else 0.04
        boxmm(nm, (x, -0.14, 0.0), (x + w, 0.0, 2.55), cream, bev=0.012)
    boxmm("ph_pil_R2", (2.06, -0.14, 0.0), (2.32, 0.0, 2.55), cream, bev=0.012)
    boxmm("ph_fascia", (-2.6, -0.18, 2.52), (2.35, 0.0, 3.02), green, bev=0.015)
    boxmm("ph_cornice", (-2.66, -0.24, 3.02), (2.41, 0.0, 3.12), cream, bev=0.02)
    boxmm("ph_fascia_line", (-2.52, -0.185, 2.58), (2.27, -0.18, 2.6), gilt, bev=0)
    boxmm("ph_fascia_line2", (-2.52, -0.185, 2.94), (2.27, -0.18, 2.96), gilt, bev=0)
    text("ph_fascia_text", "SPOKES & SPROCKETS", "georgiab.ttf", 0.26, (-0.12, -0.186, 2.77), gilt, rot=(90, 0, 0),
         fit=4.3, extrude=0.006)
    for x in (-2.62, 2.33):
        boxmm(f"ph_console{x}", (x - 0.06, -0.24, 2.5), (x + 0.06, 0.0, 3.04), cream, bev=0.015)
    boxmm("ph_upper_win", (-1.6, -0.05, 3.6), (-0.4, 0.0, 4.6), mat("ph_glass_up", "#5c6f78", 0.1, spec=0.8), bev=0)


def draw_date_stamp(px, w, h, s="'09 6 14", col=(1.0, 0.52, 0.12)):
    """Burn an orange seven-segment date stamp into the bottom-right corner (rows run bottom-up)."""
    seg = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
           "7": "abc", "8": "abcdefg", "9": "abcdfg"}
    dh = int(h * 0.045)
    dw, t = int(dh * 0.55), max(2, int(dh * 0.13))
    x = w - int(w * 0.04) - len(s) * int(dw * 1.45)
    y0 = int(h * 0.05)
    glow = np.zeros((h, w), np.float32)
    for ch in s:
        if ch == "'":
            glow[y0 + dh - t * 3:y0 + dh, x + dw // 2:x + dw // 2 + t] = 1
        elif ch in seg:
            S = seg[ch]
            boxes = {"a": (x, y0 + dh - t, x + dw, y0 + dh), "d": (x, y0, x + dw, y0 + t),
                     "g": (x, y0 + dh // 2 - t // 2, x + dw, y0 + dh // 2 + t - t // 2),
                     "f": (x, y0 + dh // 2, x + t, y0 + dh), "b": (x + dw - t, y0 + dh // 2, x + dw, y0 + dh),
                     "e": (x, y0, x + t, y0 + dh // 2), "c": (x + dw - t, y0, x + dw, y0 + dh // 2)}
            for k in S:
                a0, b0, a1, b1 = boxes[k]
                glow[b0:b1, a0 + 1:a1 - 1] = 1
        x += int(dw * 1.45)
    soft = glow.copy()                                       # a little bloom around the digits
    for _ in range(6):
        soft = (soft + np.roll(soft, 1, 0) + np.roll(soft, -1, 0) + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5
    a = np.clip(glow * 0.9 + soft * 0.8, 0, 1)[..., None]
    px[..., :3] = px[..., :3] * (1 - a) + np.array(col) * a


def render_photo_2009(M, path, res=(1500, 1000), samples=48):
    """Build the 2009 shopfront in its own scene, render it, then make it a print: warmer, faded, grainy, with the
    camera's orange date stamp (Sunday 14 June 2009)."""
    sc = bpy.data.scenes.new("PHOTO2009")
    col = bpy.data.collections.new("PHOTO")
    sc.collection.children.link(col)
    COLL["PHOTO"] = col
    prev = CUR[0]
    use("PHOTO")
    photo_shopfront(M)
    photo_figures(M)
    apply_fits()
    sun = bpy.data.objects.new("ph_sun", bpy.data.lights.new("ph_sun", "SUN"))
    sun.data.energy, sun.data.color, sun.data.angle = 4.2, (1.0, 0.93, 0.8), radians(2.5)
    sun.rotation_euler = (radians(50), 0, radians(-35))
    col.objects.link(sun)
    fill = bpy.data.objects.new("ph_fill", bpy.data.lights.new("ph_fill", "AREA"))
    fill.data.energy, fill.data.size, fill.data.color = 900.0, 4.0, (0.85, 0.9, 1.0)
    fill.location = (0.5, -6.0, 2.5)
    col.objects.link(fill)
    aim(fill, (0, -1, 1.2))
    shop = bpy.data.objects.new("ph_shoplight", bpy.data.lights.new("ph_shoplight", "AREA"))
    shop.data.energy, shop.data.size, shop.data.size_y, shop.data.color = 260.0, 2.6, 0.3, (1.0, 0.85, 0.62)
    shop.location = (-0.85, 0.15, 2.05)
    col.objects.link(shop)
    aim(shop, (-0.85, 0.2, 0.5))
    cd = bpy.data.cameras.new("ph_cam")
    cd.lens, cd.sensor_width = 33, 36
    cam = bpy.data.objects.new("ph_cam", cd)
    cam.location = (0.1, -5.2, 1.35)
    col.objects.link(cam)
    aim(cam, (-0.02, 0, 1.5))
    sc.camera = cam
    w = bpy.data.worlds.new("ph_world")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = rgba("#a9c3dd")
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = w
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    sc.eevee.use_shadows = True
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Base Contrast"
    except TypeError:
        pass
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True, scene=sc.name)
    # the print finish
    im = bpy.data.images.load(path, check_existing=False)
    pw, ph = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(ph, pw, 4)
    rgb = px[..., :3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    rgb = np.clip((rgb - 0.5) * 1.12 + 0.5, 0, 1)            # minilab punch
    rgb = rgb * 0.92 + lum[..., None] * 0.08                 # a touch of fade in the colours
    rgb = rgb * np.array([1.05, 1.0, 0.88]) + np.array([0.02, 0.012, 0.0])  # warm print
    rgb = 0.035 + rgb * 0.94                                 # lifted blacks
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    vig = 1 - 0.22 * (((xx / pw - 0.5) * 1.7) ** 2 + ((yy / ph - 0.5) * 1.7) ** 2)
    rgb *= vig[..., None]
    rgb += np.random.default_rng(2009).normal(0, 0.012, rgb.shape).astype(np.float32)
    px[..., :3] = np.clip(rgb, 0, 1)
    draw_date_stamp(px, pw, ph)
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    # tidy away the mini-set
    for ob in list(col.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(col)
    del COLL["PHOTO"]
    bpy.data.scenes.remove(sc)
    use(prev)


def ensure_photo(M, regen=False):
    if regen or not os.path.exists(PHOTO_2009):
        t = time.time()
        render_photo_2009(M, PHOTO_2009)
        print(f"rendered the 2009 photo in {time.time() - t:.1f}s -> {PHOTO_2009}")
    return PHOTO_2009


def build_photo_frame(M, loc, yaw, coll=None, name="photo_frame"):
    """Theo's 2009 photo, a 6x4in print in a walnut frame with an easel back, standing on a desk."""
    g = grp(name, loc, (0, 0, yaw), coll=coll)
    lean = grp(name + "_lean", (0, 0, 0), (-12, 0, 0), parent=g, coll=coll)   # leans back on its strut
    pw, ph_ = 0.152, 0.102
    fw, t, dep = 0.016, 0.0, 0.014
    ow, oh = pw + 2 * fw - 0.006, ph_ + 2 * fw - 0.006
    walnut = wood("walnut", "#5a3a26", "#3f281a", 0.38, grain=9.0, coat=0.4)
    zc = oh / 2
    for nm, size, at in (("top", (ow, dep, fw), (0, 0, oh - fw / 2)), ("bot", (ow, dep, fw), (0, 0, fw / 2)),
                         ("L", (fw, dep, oh - 2 * fw + 0.002), (-ow / 2 + fw / 2, 0, zc)),
                         ("R", (fw, dep, oh - 2 * fw + 0.002), (ow / 2 - fw / 2, 0, zc))):
        box(f"{name}_{nm}", size, at, walnut, bev=0.004, seg=2, parent=lean, coll=coll)
    img = bpy.data.images.load(ensure_photo(M), check_existing=True)
    pm = bpy.data.materials.new(name + "_print")
    pm.use_nodes = True
    b = principled(pm)
    tx = pm.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = img
    pm.node_tree.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.32
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(p) for p in ((-pw / 2, 0, -ph_ / 2), (pw / 2, 0, -ph_ / 2), (pw / 2, 0, ph_ / 2),
                                    (-pw / 2, 0, ph_ / 2))]
    f = bm.faces.new(vs)
    for lp, tt in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = tt
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    finish(name + "_photo", bm, pm, lean, (0, 0.001, zc), smooth=False, coll=coll)
    box(name + "_glass", (ow - 2 * fw + 0.004, 0.0015, oh - 2 * fw + 0.004), (0, -0.003, zc), M["glass"], bev=0,
        parent=lean, coll=coll).visible_shadow = False
    box(name + "_back", (ow - 0.01, 0.003, oh - 0.01), (0, dep / 2 - 0.001, zc), M["kraft"], bev=0.001, parent=lean,
        coll=coll)
    strut = grp(name + "_strut_h", (0, dep / 2 + 0.001, oh * 0.72), (32, 0, 0), parent=lean, coll=coll)
    box(name + "_strut", (0.03, 0.003, oh * 0.86), (0, 0.0015, -oh * 0.43), M["kraft"], bev=0.001, parent=strut, coll=coll)
    return g


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


def curled_sheet(name, w, h, m, parent, curl=0.0, flat_to=0.93, rows=10):
    """A sheet hanging from its top-centre down -Y, flat to `flat_to` of its height and lifting `curl` at the bottom
    edge. Returns zc(y): the surface height at print-space y (origin at the sheet centre), exactly as meshed."""
    fr = [flat_to * i / rows for i in range(rows + 1)] + [flat_to + (1 - flat_to) * i / 4 for i in range(1, 5)]
    zf = [curl * max(0.0, (f - flat_to) / (1 - flat_to)) ** 2 for f in fr]
    bm = bmesh.new()
    vs = [[bm.verts.new((-w / 2 + w * i / 3, -h * f, z)) for i in range(4)] for f, z in zip(fr, zf)]
    for j in range(len(fr) - 1):
        for i in range(3):
            bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    ob = finish(name, bm, m, parent, smooth=True)
    sd = ob.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.0005
    sd.offset = -1

    def zc(y):
        f = min(1.0, max(0.0, (h / 2 - y) / h))
        for k in range(len(fr) - 1):
            if fr[k] <= f <= fr[k + 1]:
                t = (f - fr[k]) / (fr[k + 1] - fr[k])
                return 0.00055 + zf[k] * (1 - t) + zf[k + 1] * t
        return 0.00055
    return zc


def build_calendar(M, parent):
    """Wheelwright's supplier calendar, November 2026 (Monday-first; the 1st is a Sunday, so six week rows). Martin's
    red pen: Mon 16, Tue 17 and Wed 18 crossed off (Thursday the 19th is tonight) and Friday 20 circled,
    "THEO'S LAST DAY :(". Martin doesn't cross days off, so Monday's calendar looks the same."""
    w, h = 0.22, 0.36
    zc = curled_sheet("cal_paper", w, h, M["paper"], parent, curl=0.007, flat_to=0.93)
    top = grp("cal_print", (0, -h / 2, 0.0), parent=parent)       # print space: origin at sheet centre
    # illustration: a lane through low hills, a rider, a pale sun
    il = [("#d9ddd0", [(-0.1, 0.035), (0.1, 0.035), (0.1, 0.17), (-0.1, 0.17)]),
          ("#efd9a2", circ_pts(0.05, 0.135, 0.016, n=16)),
          ("#9eb294", [(-0.1, 0.085), (-0.06, 0.112), (-0.02, 0.097), (0.03, 0.12), (0.07, 0.102), (0.1, 0.114),
                       (0.1, 0.035), (-0.1, 0.035)]),
          ("#71906b", [(-0.1, 0.064), (-0.04, 0.088), (0.02, 0.072), (0.1, 0.09), (0.1, 0.035), (-0.1, 0.035)]),
          ("#8d877b", [(-0.034, 0.035), (0.046, 0.035), (0.013, 0.083), (0.006, 0.083)])]
    for i, (c, pts) in enumerate(il):
        flat(f"cal_il{i}", pts, zc(0.1) + i * 0.00004, mat(f"cal_il{i}", c, 0.7), top)
    rider = mat("cal_rider", "#2f3a40", 0.6)
    zr = zc(0.05) + 0.0003
    for k, cx in enumerate((-0.068, -0.036)):
        annulus(f"cal_wheel{k}", circ_pts(cx, 0.052, 0.0105, n=16), circ_pts(cx, 0.052, 0.0085, n=16), zr, rider, top)
    flat("cal_frame", [(-0.068, 0.052), (-0.05, 0.068), (-0.036, 0.052), (-0.052, 0.052), (-0.05, 0.066),
                       (-0.066, 0.053)], zr, rider, top)
    flat("cal_body", [(-0.055, 0.07), (-0.045, 0.088), (-0.036, 0.09), (-0.033, 0.084), (-0.044, 0.068)], zr, rider, top)
    disc("cal_head", -0.034, 0.095, 0.0045, zr, rider, top, n=10)
    text("cal_month", "NOVEMBER", "verdanab.ttf", 0.017, (-0.1, 0.012, zc(0.0)), M["ink"], ax="LEFT", parent=top)
    text("cal_year", "2026", "verdana.ttf", 0.017, (0.1, 0.012, zc(0.0)), M["red_ink"], ax="RIGHT", parent=top)
    cw, chh, gx0, gy0 = 0.2 / 7, 0.0235, -0.1, -0.012
    for c, dname in enumerate("MTWTFSS"):
        text(f"cal_wd{c}", dname, "verdanab.ttf", 0.0065, (gx0 + (c + 0.5) * cw, gy0 + 0.004, zc(gy0)),
             M["red_ink"] if c == 6 else M["print_grey"], parent=top)
    grey = mat("cal_grid", "#b9b4aa", 0.8)
    rows = 6
    zg = zc(gy0) + 0.0001                                    # the grid is on the flat part of the sheet
    for r in range(rows + 1):
        yy = gy0 - r * chh
        rect(f"cal_hl{r}", gx0, yy - 0.0002, gx0 + 0.2, yy + 0.0002, zg, grey, top)
    for c in range(8):
        xx = gx0 + c * cw
        rect(f"cal_vl{c}", xx - 0.0002, gy0 - rows * chh, xx + 0.0002, gy0, zg, grey, top)
    for d in range(1, 31):
        r, c = divmod(d + 5, 7)
        x = gx0 + c * cw + 0.0025
        y = gy0 - r * chh - 0.0058
        text(f"cal_d{d}", str(d), "verdana.ttf", 0.0074, (x, y, zg + 0.0001), M["red_ink"] if c == 6 else M["ink"],
             ax="LEFT", parent=top)
    text("cal_supplier", "WHEELWRIGHT CYCLE SUPPLY  ·  trade parts since 1979  ·  01632 960 412", "verdana.ttf",
         0.0042, (0, -0.166, zc(-0.166)), M["print_grey"], parent=top, fit=0.196)
    # Martin's marks: Friday 20 circled (twice round, like a real pen), Mon-Wed crossed off, the note below
    zp = zg + 0.0005
    cx, cy = gx0 + 4.5 * cw, gy0 - 3.5 * chh
    pts = []
    for i in range(30):
        t = 2 * pi * 1.15 * i / 29 + 1.9
        rr = 1.0 + 0.06 * sin(3 * t) + 0.03 * i / 29
        pts.append((cx + 0.0165 * rr * cos(t), cy + 0.0128 * rr * sin(t), zp))
    curve("cal_circle", pts, 0.00065, M["red_ink"], parent=top, res=3, bres=1)
    for d in (16, 17, 18):
        r, c = divmod(d + 5, 7)
        x, y = gx0 + (c + 0.5) * cw, gy0 - (r + 0.5) * chh
        for a in (38, -38):
            box(f"cal_x{d}{a}", (0.026, 0.0011, 0.0002), (x, y, zp), M["red_ink"], rot=(0, 0, a + (d % 3) * 3), bev=0,
                parent=top)
    yy = gy0 - 5.5 * chh
    text("cal_note", "THEO'S LAST DAY :(", "Inkfree.ttf", 0.0135, (gx0 + 4.0 * cw, yy - 0.0015, zp), M["red_ink"],
         parent=top, fit=0.165, rot=(0, 0, 3), extrude=0.00008)
    curve("cal_arrow", [(cx + 0.012, yy + 0.0075, zp), (cx + 0.019, gy0 - 4.5 * chh, zp),
                        (cx + 0.012, cy - 0.0128, zp)], 0.0005, M["red_ink"], parent=top, res=6, bres=1)
    for a in (-30, 40):
        box(f"cal_arrowhead{a}", (0.0045, 0.0009, 0.0002), (cx + 0.012 + 0.0014 * (1 if a > 0 else -1), cy - 0.0145, zp),
            M["red_ink"], rot=(0, 0, 90 + a), bev=0, parent=top)
    pushpin("cal_pin", parent, 0, -0.008, M["pin_red"])


def pinned(name, x, z, rx=88.0, ry=0.0, yf=None):
    return grp(name, (x, yf if yf is not None else D - 0.0185, z), (rx, ry, 0))


def build_flyer(M, parent):
    """The Sunday club run: an A5 flyer on pale green paper with tear-off phone tabs, two already taken."""
    w, h = 0.148, 0.21
    zc = curled_sheet("flyer_paper", w, h, mat("flyer_green", "#dfe6c6", 0.8, spec=0.3), parent, curl=0.004,
                      flat_to=0.86)
    p = grp("flyer_print", (0, -h / 2, 0), parent=parent)
    z = zc(0.0) + 0.0001
    ink = mat("flyer_ink", "#24402f", 0.6)
    text("fl_t1", "SUNDAY", "verdanab.ttf", 0.019, (0, 0.082, z), ink, parent=p, fit=0.13)
    text("fl_t2", "CLUB RUN", "verdanab.ttf", 0.019, (0, 0.06, z), ink, parent=p, fit=0.13)
    # a road over two hills
    flat("fl_hill1", [(-0.062, 0.002), (-0.03, 0.03), (0.0, 0.012), (0.035, 0.038), (0.062, 0.016), (0.062, 0.002)],
         z, mat("fl_hill", "#9db58a", 0.8), p)
    curve("fl_road", [(-0.06, 0.004, z + 0.0001), (-0.02, 0.02, z + 0.0001), (0.01, 0.01, z + 0.0001),
                      (0.04, 0.028, z + 0.0001)], 0.0012, mat("fl_road", "#f4f0dd", 0.7), parent=p, res=6, bres=1,
          flatz=0.2)
    lines = [("Every Sunday, 8am", "verdanab.ttf", 0.0068), ("from the shop", "verdana.ttf", 0.0062),
             ("40 miles · café stop", "verdana.ttf", 0.0058), ("all welcome · lights in winter", "verdana.ttf", 0.005)]
    for i, (t, f, sz) in enumerate(lines):
        text(f"fl_l{i}", t, f, sz, (0, -0.012 - i * 0.0115, z), ink, parent=p, fit=0.13)
    text("fl_club", "Spokes & Sprockets CC", "georgiai.ttf", 0.0058, (0, -0.062, z), ink, parent=p)
    # tear-off tabs: eight tabs, the 3rd and 6th taken
    for k in range(8):
        x = -w / 2 + (k + 0.5) * w / 8
        if k in (2, 5):
            continue
        tg = grp(f"fl_tab{k}", (x, -0.087, zc(-0.087) - 0.00055), (0, 0, 0), parent=p)
        text(f"fl_tab_t{k}", "club run\n01632 960 412", "verdana.ttf", 0.0026, (0, 0, 0.0002), ink, parent=tg,
             rot=(0, 0, 90), line=0.9)
    for k in range(9):
        x = -w / 2 + k * w / 8
        rect(f"fl_cut{k}", x - 0.0002, -0.105, x + 0.0002, -0.07, zc(-0.087) + 0.0001, mat("fl_cut", "#9aa38c", 0.8), p)
    for k in (2, 5):                                        # torn-off tabs show the cork behind
        x = -w / 2 + (k + 0.5) * w / 8
        rect(f"fl_gone{k}", x - w / 16 + 0.0004, -0.105, x + w / 16 - 0.0004, -0.0705, zc(-0.087) + 0.00012, M["cork"], p)
    pushpin("flyer_pin", parent, 0, -0.008, M["pin_green"])


CRAYON = {}


def crayon(c):
    if c not in CRAYON:
        CRAYON[c] = mat("crayon_" + c.lstrip("#"), c, 0.65)
    return CRAYON[c]


def scrawl(name, pts, c, parent, z, r=0.0011, rng=None):
    """A wobbly crayon stroke."""
    rng = rng or random.Random(len(pts) * 7 + int(abs(pts[0][0]) * 1e4))
    wob = [(x + rng.uniform(-0.0007, 0.0007), y + rng.uniform(-0.0007, 0.0007), z) for x, y in pts]
    return curve(name, wob, r, crayon(c), parent=parent, res=5, bres=1, flatz=0.25)


def build_thankyou(M, parent):
    """A thank-you drawing from a customer's daughter: her bike, her, the sun, in crayon; "THANK YOU" in rainbow
    letters and "love Mia (age 6)"."""
    w, h = 0.19, 0.135
    zc = curled_sheet("ty_paper", w, h, mat("cartridge", "#f6f2e6", 0.85, spec=0.25), parent, curl=0.003, flat_to=0.88)
    p = grp("ty_print", (0, -h / 2, 0), parent=parent)
    z = zc(0.0) + 0.0002
    rng = random.Random(6)
    rainbow = ("#d6453a", "#e88a2a", "#d9b22a", "#4f9a4a", "#3c78c8", "#7b52b0", "#d6453a", "#e88a2a")
    for k, (ch, c) in enumerate(zip("THANK YOU", rainbow[:5] + ("",) + rainbow[5:])):
        if ch != " ":
            text(f"ty_l{k}", ch, "ITCKRIST.TTF", 0.0155, (-0.078 + k * 0.0162, 0.046 + rng.uniform(-0.002, 0.002), z),
                 crayon(c), parent=p, rot=(0, 0, rng.uniform(-8, 8)))
    text("ty_sub", "for fixing my bike", "ITCKRIST.TTF", 0.0072, (0.005, 0.03, z), crayon("#3c78c8"), parent=p)
    text("ty_sign", "love Mia (age 6)", "ITCKRIST.TTF", 0.0066, (0.045, -0.054, z), crayon("#7b52b0"), parent=p,
         rot=(0, 0, 4))
    # the bike: two wheels, a pink frame, a basket
    for k, cx in enumerate((-0.045, 0.005)):
        pts = [(cx + 0.0175 * cos(2 * pi * i / 18), -0.03 + 0.0175 * sin(2 * pi * i / 18)) for i in range(19)]
        scrawl(f"ty_wheel{k}", pts, "#2a2a2a", p, z, rng=rng)
        for s in range(4):
            a = pi * s / 4
            scrawl(f"ty_spoke{k}{s}", [(cx - 0.016 * cos(a), -0.03 - 0.016 * sin(a)), (cx + 0.016 * cos(a),
                                                                                   -0.03 + 0.016 * sin(a))],
                   "#8a8a8a", p, z - 0.00005, r=0.0005, rng=rng)
    scrawl("ty_frame", [(-0.045, -0.03), (-0.025, -0.005), (0.0, -0.006), (0.005, -0.03), (-0.02, -0.03),
                        (-0.025, -0.005)], "#e0609a", p, z, r=0.0013, rng=rng)
    scrawl("ty_bars", [(0.0, -0.006), (0.002, 0.006), (0.009, 0.007)], "#2a2a2a", p, z, rng=rng)
    scrawl("ty_basket", [(0.004, 0.004), (0.016, 0.004), (0.014, -0.006), (0.006, -0.006), (0.004, 0.004)], "#b07a3a",
           p, z, rng=rng)
    # Mia on top: a head, a big smile, plaits
    hp = [(-0.022 + 0.008 * cos(2 * pi * i / 14), 0.016 + 0.0085 * sin(2 * pi * i / 14)) for i in range(15)]
    scrawl("ty_head", hp, "#b5704a", p, z, rng=rng)
    scrawl("ty_smile", [(-0.026, 0.014), (-0.022, 0.011), (-0.018, 0.014)], "#d6453a", p, z + 0.00005, r=0.0007, rng=rng)
    for k, ex in enumerate((-0.025, -0.019)):
        disc(f"ty_eye{k}", ex, 0.018, 0.0009, z + 0.00005, crayon("#2a2a2a"), p, n=8)
    scrawl("ty_body", [(-0.022, 0.008), (-0.022, -0.004), (-0.02, -0.01)], "#4f9a4a", p, z, r=0.0016, rng=rng)
    scrawl("ty_arm", [(-0.022, 0.003), (-0.01, 0.006), (0.002, 0.006)], "#b5704a", p, z, r=0.0008, rng=rng)
    for k, s in enumerate((-1, 1)):
        scrawl(f"ty_plait{k}", [(-0.022 + s * 0.008, 0.02), (-0.022 + s * 0.012, 0.01), (-0.022 + s * 0.011, 0.004)],
               "#3a2418", p, z, r=0.0009, rng=rng)
    # the sun and the grass
    sp = [(0.078 + 0.008 * cos(2 * pi * i / 14), 0.05 + 0.008 * sin(2 * pi * i / 14)) for i in range(15)]
    scrawl("ty_sun", sp, "#e4c234", p, z, r=0.0014, rng=rng)
    for k in range(8):
        a = 2 * pi * k / 8
        scrawl(f"ty_ray{k}", [(0.078 + 0.011 * cos(a), 0.05 + 0.011 * sin(a)), (0.078 + 0.016 * cos(a),
                                                                                0.05 + 0.016 * sin(a))],
               "#e88a2a", p, z, r=0.0008, rng=rng)
    gr = [(-0.09 + i * 0.006, -0.05 + (0.004 if i % 2 else 0.0)) for i in range(31)]
    scrawl("ty_grass", gr, "#4f9a4a", p, z, r=0.0009, rng=rng)
    pushpin("ty_pin", parent, 0, -0.006, M["pin_yellow"])


def build_pricelist(M, parent):
    """Wheelwright's trade price list, folded in four (the creases show), half the lines highlighted by Martin."""
    w, h = 0.2, 0.142
    zc = curled_sheet("pl_paper", w, h, M["paper"], parent, curl=0.003, flat_to=0.9)
    p = grp("pl_print", (0, -h / 2, 0), parent=parent)
    z = zc(0.0) + 0.0001
    crease = mat("pl_crease", "#d9d2c3", 0.8)
    rect("pl_crease_v", -0.0003, -h / 2, 0.0003, h / 2, z - 0.00005, crease, p)
    rect("pl_crease_h", -w / 2, -0.0003, w / 2, 0.0003, z - 0.00005, crease, p)
    text("pl_head", "WHEELWRIGHT CYCLE SUPPLY", "verdanab.ttf", 0.0075, (-0.09, 0.058, z), M["ink"], ax="LEFT",
         parent=p, fit=0.15)
    text("pl_sub", "Trade price list  ·  autumn/winter 2026  ·  prices ex VAT", "verdana.ttf", 0.0038,
         (-0.09, 0.049, z), M["print_grey"], ax="LEFT", parent=p, fit=0.17)
    rect("pl_rule", -0.09, 0.0435, 0.09, 0.0442, z, M["ink"], p)
    rows = [("BP-SH-RES", "Disc pads, resin, pair", "3.10"), ("CAB-SH-GEAR", "Gear cable set", "4.60"),
            ("TUB-700-25", "Inner tube 700x25c", "2.05"), ("CHN-KMC-X11", "Chain 11sp", "11.40"),
            ("CAS-11-32", "Cassette 11-32", "19.80"), ("TAPE-BAR-BLK", "Bar tape, black", "6.90"),
            ("BB-SH-HT2", "Bottom bracket HT2", "12.70"), ("SPK-DT-292", "Spoke 292mm (each)", "0.38"),
            ("FLD-DOT51", "Brake fluid DOT 5.1", "3.95"), ("HDS-FSA-118", "Headset 1-1/8in", "15.20")]
    hl = mat("pl_highlight", "#f2e46a", 0.7)
    for i, (code, part, price) in enumerate(rows):
        y = 0.034 - i * 0.0072
        if i in (0, 2, 7):
            rect(f"pl_hl{i}", -0.091, y - 0.0028, 0.091, y + 0.0036, z - 0.00003, hl, p)
        text(f"pl_c{i}", code, "consola.ttf", 0.0042, (-0.09, y, z), M["ink"], ax="LEFT", parent=p)
        text(f"pl_p{i}", part, "verdana.ttf", 0.0041, (-0.042, y, z), M["ink"], ax="LEFT", parent=p, fit=0.09)
        text(f"pl_v{i}", "£" + price, "verdana.ttf", 0.0041, (0.09, y, z), M["ink"], ax="RIGHT", parent=p)
    text("pl_foot", "orders before 2pm: next day  ·  trade only", "verdana.ttf", 0.0034, (0, -0.062, z),
         M["print_grey"], parent=p)
    pushpin("pl_pin_L", parent, -0.08, -0.008, M["pin_blue"])
    pushpin("pl_pin_R", parent, 0.08, -0.009, M["pin_white"])


def build_bizcard(M, parent, name, lines, accent):
    w, h = 0.085, 0.055
    box(name + "_card", (w, h, 0.0006), (0, -h / 2, 0.0003), mat(name + "_stock", "#f7f4ec", 0.6), bev=0, parent=parent)
    rect(name + "_bar", -w / 2, -0.008, w / 2, -0.0, 0.00062, mat(name + "_accent", accent, 0.5), parent)
    for i, (t, f, sz) in enumerate(lines):
        text(f"{name}_t{i}", t, f, sz, (-w / 2 + 0.006, -0.018 - i * 0.0085, 0.00065), M["ink"], ax="LEFT",
             parent=parent, fit=w - 0.012)


def build_corkboard(M):
    """The shop's corkboard: the stars are the calendar and Theo's README. Around them, a shop's life: the Sunday club
    run flyer, a thank-you drawing from a customer's daughter, Wheelwright's trade price list, two business cards.
    No sticky notes. (The 2009 photo is not here: it stands in a frame on Theo's side of the desk.)"""
    use("SET")
    x0, x1, z0, z1 = 1.45, 2.25, 0.98, 1.62
    for nm, a, b in [("cork_fr_T", (x0, D - 0.026, z1 - 0.028), (x1, D, z1)),
                     ("cork_fr_B", (x0, D - 0.026, z0), (x1, D, z0 + 0.028)),
                     ("cork_fr_L", (x0, D - 0.026, z0), (x0 + 0.028, D, z1)),
                     ("cork_fr_R", (x1 - 0.028, D - 0.026, z0), (x1, D, z1))]:
        boxmm(nm, a, b, M["oak_lt"], bev=0.006)
    boxmm("cork", (x0 + 0.02, D - 0.018, z0 + 0.02), (x1 - 0.02, D, z1 - 0.02), M["cork"], bev=0)
    build_calendar(M, pinned("calendar", 1.6, 1.585, 88, 1.5))
    build_readme(M, pinned("readme", 2.085, 1.505, 88, 3))
    build_flyer(M, pinned("flyer", 1.845, 1.592, 88.5, -2.5, yf=D - 0.0187))
    build_thankyou(M, pinned("thankyou", 1.842, 1.372, 88.6, 3.5, yf=D - 0.0189))
    build_pricelist(M, pinned("pricelist", 2.09, 1.192, 89.0, -1.5, yf=D - 0.0186))
    for nm, x, z, rz, lines, acc in (
            ("biz_madison", 1.545, 1.17, -4, [("Steve Ward", "verdanab.ttf", 0.0052),
                                              ("Area sales, trade accounts", "verdana.ttf", 0.0036),
                                              ("Madison  ·  07700 900 316", "verdana.ttf", 0.0036)], "#c23b2e"),
            ("biz_signs", 1.632, 1.108, 5, [("NORTHGATE SIGNS", "georgiab.ttf", 0.0048),
                                            ("signwriting & gilding since 1971", "georgiai.ttf", 0.0034),
                                            ("01632 960 288", "georgia.ttf", 0.0036)], "#2f4d3c")):
        g = pinned(nm, x, z, 89.0, rz, yf=D - 0.0186)
        build_bizcard(M, g, nm, lines, acc)
        pushpin(nm + "_pin", g, 0, -0.006, M["pin_red"] if "mad" in nm else M["pin_white"])
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


def scatter(name, parent, n, w, d, zmax, make, m, seed):
    """Loose small parts in a drawer: `make(bm, rng)` adds one part at the origin, it gets dropped at random."""
    rng = random.Random(seed)
    bm = bmesh.new()
    for _ in range(n):
        before = set(bm.verts)
        make(bm, rng)
        new = [v for v in bm.verts if v not in before]
        q = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.3))).normalized()
        q = Vector((0, 0, 1)).rotation_difference(q)
        off = Vector((rng.uniform(-w / 2 + 0.008, w / 2 - 0.008), rng.uniform(-d / 2 + 0.008, d / 2 - 0.008),
                      rng.uniform(0.004, zmax)))
        for v in new:
            v.co = q @ v.co + off
    return finish(name, bm, m, parent, angle=50)


def _cylpart(bm, r, L, z0=0.0, seg=6):
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L)
    bmesh.ops.translate(bm, vec=(0, 0, z0 + L / 2), verts=g["verts"])


def part_bolt(bm, rng):                                       # M5 x 16, hex head
    _cylpart(bm, 0.0025, 0.016, 0.0, 8)
    _cylpart(bm, 0.0042, 0.0035, 0.016, 6)


def part_nipple(bm, rng):                                     # spoke nipple: 12 mm, flared head
    _cylpart(bm, 0.0018, 0.012, 0.0, 6)
    _cylpart(bm, 0.0027, 0.002, 0.012, 8)


def part_ball(bm, rng):
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0032)


def part_core(bm, rng):                                       # Schrader valve core, 10 mm
    _cylpart(bm, 0.0015, 0.008, 0.0, 6)
    _cylpart(bm, 0.0022, 0.002, 0.008, 6)
    _cylpart(bm, 0.0005, 0.004, 0.01, 4)


def part_cap(bm, rng):                                        # valve dust cap
    _cylpart(bm, 0.0036, 0.009, 0.0, 10)


def pads_in_bag(M, parent, loc, rot):
    """ONE pair of resin disc pads, as they come: two pads face to face with their spring clip, in a small zip bag
    with a printed header card. The last pair (Anika needs two)."""
    g = grp("pads_bag", loc, rot, parent=parent)
    bag = mat("zipbag", "#e9eef0", 0.12, spec=0.6, alpha=0.28)
    box("bag_film", (0.072, 0.098, 0.009), (0, 0, 0.0045), bag, bev=0.003, parent=g).visible_shadow = False
    box("bag_header", (0.072, 0.024, 0.0012), (0, 0.037, 0.0098), M["paper"], bev=0, parent=g)
    box("bag_zip", (0.07, 0.0025, 0.0014), (0, 0.022, 0.0098), mat("zip_red", "#c23b2e", 0.4), bev=0, parent=g)
    text("bag_t1", "RESIN DISC PADS", "verdanab.ttf", 0.0042, (0, 0.04, 0.0106), M["ink"], parent=g, fit=0.064)
    text("bag_t2", "1 PAIR  ·  with spring  ·  BP-SH-RES", "verdana.ttf", 0.0026, (0, 0.033, 0.0106), M["print_grey"],
         parent=g, fit=0.064)
    plate_o = [(-0.0185, -0.011), (0.0185, -0.011), (0.021, -0.004), (0.02, 0.006), (0.012, 0.011), (0.004, 0.012),
               (0.003, 0.019), (-0.003, 0.019), (-0.004, 0.012), (-0.012, 0.011), (-0.02, 0.006), (-0.021, -0.004)]
    comp_o = [(-0.017, -0.0095), (0.017, -0.0095), (0.0192, -0.003), (0.018, 0.0055), (0.011, 0.0092),
              (-0.011, 0.0092), (-0.018, 0.0055), (-0.0192, -0.003)]
    for i, (dz, flip) in enumerate(((0.0012, False), (0.0088, True))):
        pg = grp(f"pad{i}", (0.0, -0.012, dz), (180 if flip else 0, 0, 0), parent=g)
        prism(f"pad{i}_plate", plate_o, 0.0018, m=M["steel"], parent=pg, bev=0.0004)
        prism(f"pad{i}_comp", comp_o, 0.0028, loc=(0, 0, 0.0018 if not flip else -0.0028), m=M["pad_compound"],
              parent=pg, bev=0.0005)
        disc(f"pad{i}_hole", 0, 0.0155, 0.0013, 0.0019 if not flip else -0.0001, M["hole"], pg, n=10)
    # the spring clip: a sprung steel "W" between the pads, its two tabs showing above them
    for s in (-1, 1):
        box(f"pad_spring{s}", (0.03, 0.0012, 0.006), (0, -0.012 + s * 0.0085, 0.0058), M["chrome"],
            rot=(s * 12, 0, 0), bev=0.0003, parent=g)
    box("pad_spring_tab", (0.006, 0.006, 0.006), (0, 0.006, 0.0058), M["chrome"], bev=0.0005, parent=g)
    return g


def product_box(name, size, loc, parent, body, band=None, label=None, M=None, rot=(0, 0, 0), font_sz=0.0055,
                label_m=None):
    """Retail packaging: a printed carton with a colour band and its product line on the front (no brand marks)."""
    b = box(name, size, loc, body, rot=rot, bev=0.0015, parent=parent)
    w, d, h = size
    if band is not None:
        box(name + "_band", (w + 0.0004, d + 0.0004, h * 0.28), (0, 0, h * 0.18), band, bev=0, parent=b)
    if label:
        text(name + "_t", label, "verdanab.ttf", font_sz, (0, -d / 2 - 0.0004, -h * 0.12), label_m or M["ink"],
             rot=(90, 0, 0), parent=b, fit=w - 0.008, line=0.95)
    return b


def drawer_kit(kind, g, w, d, M):
    """What's in each drawer, at real scale, matching its label (and Theo's parts list)."""
    t = 0.0025
    if kind == "bolts":
        scatter("dr_bolts", g, 26, w, d, 0.014, part_bolt, M["steel"], 1)
    elif kind == "nipples":
        scatter("dr_nipples", g, 60, w, d, 0.012, part_nipple, M["brass"], 2)
    elif kind == "balls":
        scatter("dr_balls", g, 60, w, d, 0.006, part_ball, M["chrome"], 3)
    elif kind == "cores":
        scatter("dr_cores", g, 30, w, d, 0.008, part_core, M["brass"], 4)
        scatter("dr_caps", g, 18, w, d, 0.01, part_cap, M["plastic_blk"], 5)
    elif kind == "pads":                                      # drawer 1
        pads_in_bag(M, g, (0.008, -0.045, t), (0, 0, -8))
    elif kind == "cables":                                    # drawer 2: gear cable sets
        for k in range(3):
            pk = grp(f"cable_set{k}", (-0.02 + 0.012 * k, 0.01 - 0.008 * k, t + 0.0015 + k * 0.004), (0, 0, 6 - 7 * k),
                     parent=g)
            box(f"cable_set{k}_card", (0.085, 0.15, 0.0015), (0, 0, 0), mat("cable_card", "#d9dde0", 0.6), bev=0,
                parent=pk)
            box(f"cable_set{k}_band", (0.085, 0.03, 0.0017), (0, 0.055, 0), mat("cable_band", "#2f5fa8", 0.5), bev=0,
                parent=pk)
            text(f"cable_set{k}_t", "GEAR CABLE SET", "verdanab.ttf", 0.005, (0, 0.055, 0.001), M["pin_white"],
                 parent=pk, fit=0.07)
            torus(f"cable_set{k}_coil", 0.03, 0.0022, (0, -0.012, 0.002), M["plastic_blk"], nR=24, nr=5, parent=pk,
                  scale=(1, 1, 0.5))
            torus(f"cable_set{k}_wire", 0.024, 0.0007, (0, -0.012, 0.0025), M["chrome"], nR=24, nr=4, parent=pk)
    elif kind == "tape":                                      # drawer 3: bar tape
        for k in range(3):
            product_box(f"tape_box{k}", (0.1, 0.048, 0.045), (-0.02, 0.05 - k * 0.05, t + 0.0225), g,
                        mat("tape_box", "#1d1d1f", 0.5), mat("tape_band", "#d6d2c8", 0.5), "BAR TAPE · BLACK", M,
                        font_sz=0.0048, label_m=M["pin_white"])
        cyl("tape_roll", 0.022, 0.03, (0.052, -0.04, t + 0.022), mat("bar_tape", "#151515", 0.7), rot=(0, 90, 15), n=18,
            parent=g)
    elif kind == "chains":                                    # drawer 4: chain KMC X11 and cassette 11-32
        product_box("cassette_box", (0.135, 0.135, 0.046), (-0.07, 0.01, t + 0.023), g, M["pin_white"],
                    mat("cas_band", "#b3392c", 0.5), "CASSETTE 11-32  ·  11 SPEED", M, font_sz=0.0052)
        for k in range(2):
            product_box(f"chain_box{k}", (0.092, 0.06, 0.028), (0.075, 0.04 - k * 0.064, t + 0.014), g,
                        mat("chain_box", "#3a3d42", 0.5), mat("chain_band", "#e0b53a", 0.5), "CHAIN  ·  X11", M,
                        font_sz=0.0052, label_m=M["pin_white"])
    elif kind == "bells":                                     # drawer 5: counter-sale bells
        for k, (x, y) in enumerate(((-0.05, 0.03), (0.0, 0.035), (0.05, 0.025), (-0.03, -0.035), (0.035, -0.03))):
            bg = grp(f"cbell{k}", (x, y, t), (0, 0, 40 * k), parent=g)
            lathe(f"cbell{k}_dome", [(0.0, 0.016), (0.012, 0.0145), (0.021, 0.009), (0.025, 0.003), (0.0255, 0.0),
                                     (0.0, 0.0)], n=20, m=M["chrome"], parent=bg)
            box(f"cbell{k}_lever", (0.018, 0.005, 0.003), (0.022, 0, 0.004), M["steel_dk"], bev=0.001, parent=bg)
            torus(f"cbell{k}_clamp", 0.012, 0.002, (0, 0.0, -0.002), M["steel_dk"], rot=(90, 0, 0), nR=12, nr=4,
                  parent=bg, scale=(1, 1, 0.6))
    elif kind == "tubes":                                     # drawer 6: inner tubes 700x25c and spokes 292 mm
        for k, (x, zz) in enumerate(((-0.09, 0.0), (0.0, 0.0), (0.09, 0.0), (-0.045, 0.045))):
            product_box(f"tube_box{k}", (0.078, 0.11, 0.045), (x, 0.035, t + 0.0225 + zz), g,
                        mat("tube_box", "#eef0f2", 0.5), mat("tube_band", "#2f5fa8", 0.5), "INNER TUBE\n700x25C", M,
                        font_sz=0.0046)
        sp = grp("spoke_bundle", (0.0, -0.06, t + 0.004), (0, 0, 2), parent=g)
        for k in range(14):
            yy, zz = (k % 5) * 0.0024 - 0.005, (k // 5) * 0.0022
            tube(f"spoke{k}", (-0.146, yy, zz), (0.146, yy, zz), 0.001, M["chrome"], n=4, parent=sp)
            torus(f"spoke{k}_j", 0.003, 0.001, (0.146, yy, zz + 0.003), M["chrome"], rot=(90, 0, 0), nR=6, nr=3,
                  arc=(-90, 90), parent=sp)
        for x in (-0.08, 0.08):
            torus(f"spoke_band{x}", 0.0075, 0.0015, (x, -0.0005, 0.003), mat("rubber_band", "#b88a4e", 0.6),
                  rot=(0, 90, 0), nR=12, nr=4, parent=sp, scale=(1, 1.1, 0.9))
        box("spoke_tag", (0.03, 0.002, 0.016), (0.11, -0.0085, 0.006), M["manila"], rot=(-15, 0, 0), bev=0, parent=sp)
        text("spoke_tag_t", "292", "Inkfree.ttf", 0.008, (0.11, -0.0098, 0.006), M["marker"], rot=(75, 0, 0), parent=sp)
    elif kind == "bb":                                        # drawer 7: bottom brackets HT2
        for k in range(2):
            product_box(f"bb_box{k}", (0.075, 0.075, 0.06), (-0.04 + 0.08 * k, 0.03, t + 0.03), g,
                        mat("bb_box", "#5f7183", 0.5), mat("bb_band", "#e9e5da", 0.5), "BB  ·  HT2", M,
                        font_sz=0.0052, label_m=M["pin_white"])
        for s in (-1, 1):
            cyl(f"bb_cup{s}", 0.022, 0.012, (s * 0.03, -0.05, t + 0.022), M["steel_dk"], rot=(0, 90, 0), n=16, bev=0.002,
                parent=g)
        cyl("bb_sleeve", 0.016, 0.05, (0.0, -0.05, t + 0.022), M["plastic_blk"], rot=(0, 90, 0), n=14, parent=g)


def _drawer(g, w, d, h, label, kind, M, lab_m, number=None):
    """A clear organiser drawer (frosted plastic, a coloured lip and pull, a card label in Martin's hand)."""
    t = 0.0025
    frost = mat("clear_front", "#e3eaee", 0.1, spec=0.6, alpha=0.13)
    box("dr_front", (w, t, h), (0, -d / 2, h / 2), frost, bev=0.002, parent=g).visible_shadow = False
    box("dr_lip", (w, t * 1.6, 0.012), (0, -d / 2, h - 0.006), M["drawer_body"], bev=0.0015, parent=g)
    box("dr_back", (w, t, h * 0.8), (0, d / 2, h * 0.4), M["clear"], bev=0.001, parent=g)
    box("dr_floor", (w, d, t), (0, 0, t / 2), M["clear"], bev=0.001, parent=g)
    for s in (-1, 1):
        box(f"dr_side{s}", (t, d, h * 0.8), (s * w / 2, 0, h * 0.4), M["clear"], bev=0.001, parent=g)
    box("dr_pull", (min(w * 0.35, 0.06), 0.008, 0.005), (0, -d / 2 - 0.004, h * 0.18), M["drawer_body"], bev=0.002,
        parent=g)
    lw = min(w * 0.86, 0.14)
    box("dr_label", (lw, 0.001, 0.0135), (0, -d / 2 - 0.0026, h - 0.0075), lab_m, bev=0, parent=g)
    txt = f"{number}  {label}" if number else label
    text("dr_label_text", txt, "Inkfree.ttf", 0.0108, (0, -d / 2 - 0.0033, h - 0.0078), M["marker"], rot=(90, 0, 0),
         parent=g, fit=lw - 0.008)
    drawer_kit(kind, g, w - 2 * t, d - 2 * t, M)


def build_shelf(M):
    """Shelf A over the left of the desk (the parts list: "headset: shelf A"). The parts cabinet keeps the counter
    stock in drawers numbered to match Theo's parts list (1 pads, 2 cables, 3 bar tape, 4 chains and cassettes,
    5 bells, 6 tubes and spokes, 7 bottom brackets) plus four small unnumbered drawers; drawer 1 is pulled out with
    ONE pair of pads in it. Beside it, office storage: the 2009-14 invoices in an archive box, manuals in a shoebox
    on top, the window's Christmas lights up on the cabinet, then the binders and the headset box."""
    use("SET")
    sx0, sx1, sz = 0.22, 1.42, 1.5
    boxmm("shelf", (sx0, D - 0.25, sz), (sx1, D, sz + 0.028), M["oak_lt"], bev=0.006)
    for bx in (0.32, 1.3):
        boxmm(f"shelf_brk_h{bx}", (bx - 0.01, D - 0.2, sz - 0.012), (bx + 0.01, D, sz), M["steel_dk"], bev=0.002)
        boxmm(f"shelf_brk_v{bx}", (bx - 0.01, D - 0.012, sz - 0.17), (bx + 0.01, D, sz), M["steel_dk"], bev=0.002)
        tube(f"shelf_brk_d{bx}", (bx, D - 0.008, sz - 0.15), (bx, D - 0.17, sz - 0.008), 0.005, M["steel_dk"], n=6)
    top = sz + 0.028
    lab_m = mat("label", "#f4f0e4", 0.7)
    # shelf A's own label, on its front edge
    box("shelfA_label", (0.034, 0.001, 0.018), (1.36, D - 0.2505, sz + 0.014), lab_m, bev=0)
    text("shelfA_text", "SHELF A", "segoeprb.ttf", 0.0075, (1.36, D - 0.2512, sz + 0.0135), M["marker"], rot=(90, 0, 0),
         fit=0.03)
    # ---- the parts cabinet
    cab = grp("parts_cabinet", (0.5, D - 0.12, top))
    cw, cdp, chh, fr = 0.52, 0.22, 0.362, 0.012
    box("cab_top", (cw, cdp, fr), (0, 0, chh - fr / 2), M["drawer_body"], bev=0.004, parent=cab)
    box("cab_bot", (cw, cdp, fr), (0, 0, fr / 2), M["drawer_body"], bev=0.004, parent=cab)
    box("cab_back", (cw, 0.008, chh), (0, cdp / 2 - 0.004, chh / 2), M["drawer_body"], bev=0.002, parent=cab)
    for s in (-1, 1):
        box(f"cab_side{s}", (fr, cdp, chh), (s * (cw / 2 - fr / 2), 0, chh / 2), M["drawer_body"], bev=0.004, parent=cab)
    iw = cw - 2 * fr
    rows = [  # (height, [(width share, label, kind, number), ...]) from the top down
        (0.055, [(1, "M5 BOLTS", "bolts", None), (1, "SPOKE NIPPLES", "nipples", None), (1, "BEARINGS", "balls", None),
                 (1, "VALVE CORES", "cores", None)]),
        (0.085, [(1, "BRAKE PADS", "pads", 1), (1, "CABLES", "cables", 2), (1, "BAR TAPE", "tape", 3)]),
        (0.085, [(1.55, "CHAINS / CASSETTES", "chains", 4), (1, "BELLS", "bells", 5)]),
        (0.1, [(1.65, "TUBES / SPOKES", "tubes", 6), (1, "BB", "bb", 7)]),
    ]
    z = chh - fr
    for r, (h, cells) in enumerate(rows):
        z -= h
        if r:
            box(f"cab_shelf{r}", (iw, cdp, 0.004), (0, 0, z + h + 0.002), M["drawer_body"], bev=0.001, parent=cab)
        tot = sum(c[0] for c in cells)
        x = -iw / 2
        for k, (share, lab, kind, num) in enumerate(cells):
            wd = iw * share / tot
            if k:
                box(f"cab_div{r}{k}", (0.003, cdp, h), (x, 0, z + h / 2), M["drawer_body"], bev=0.0005, parent=cab)
            pull = -0.1 if num == 1 else -0.008
            dg = grp(f"drawer_{lab}", (x + wd / 2, pull, z + 0.002), parent=cab)
            _drawer(dg, wd - 0.005, cdp - 0.02, h - 0.006, lab, kind, M, lab_m, num)
            x += wd
        z -= 0.004
    # the Christmas lights, up on top of the cabinet
    xl = grp("xmas_box", (0.47, D - 0.12, top + chh), (0, 0, 3))
    box("xmas_body", (0.3, 0.19, 0.12), (0, 0, 0.06), M["card"], bev=0.004, parent=xl)
    box("xmas_tape", (0.05, 0.1925, 0.122), (0.0, 0, 0.061), M["tape"], bev=0, parent=xl)
    box("xmas_seam", (0.3, 0.002, 0.0015), (0, 0.0, 0.1206), M["kraft"], bev=0, parent=xl)
    box("xmas_label", (0.17, 0.001, 0.05), (-0.05, -0.0956, 0.06), lab_m, bev=0, parent=xl)
    text("xmas_text", "XMAS LIGHTS\n(window)", "Inkfree.ttf", 0.017, (-0.05, -0.0962, 0.062), M["marker"],
         rot=(90, 0, 0), parent=xl, line=0.85, fit=0.155)
    curve("xmas_wire", [(0.13, -0.09, 0.121), (0.14, -0.1, 0.11), (0.135, -0.1, 0.09), (0.125, -0.097, 0.07)], 0.0012,
          mat("xmas_green", "#2c4a2a", 0.5), parent=xl)
    sphere("xmas_bulb", 0.004, (0.125, -0.098, 0.066), mat("xmas_bulb", "#e8c060", 0.2), seg=8, rings=5, parent=xl,
           scale=(1, 1, 1.5))
    # the archive box (heavy, at the bottom) and the shoebox of manuals on it
    ab = grp("archive_box", (0.905, D - 0.125, top), (0, 0, -1.5))
    aw, ad, ah = 0.24, 0.225, 0.17
    kraft_c = noisy("kraft_c", "#b18a5a", "#a27e50", 0.85, scale=30.0, bump=0.03)
    box("archive_body", (aw, ad, ah - 0.02), (0, 0, (ah - 0.02) / 2), kraft_c, bev=0.003, parent=ab)
    box("archive_lid", (aw + 0.006, ad + 0.006, 0.035), (0, 0, ah - 0.0175), kraft_c, bev=0.003, parent=ab)
    box("archive_handle", (0.06, 0.002, 0.022), (0, -ad / 2 - 0.0005, ah - 0.06), M["hole"], bev=0.006, parent=ab)
    box("archive_label", (0.15, 0.001, 0.06), (0, -ad / 2 - 0.0008, 0.055), lab_m, bev=0, parent=ab)
    for k in range(3):
        box(f"archive_rule{k}", (0.13, 0.0008, 0.0006), (0, -ad / 2 - 0.0014, 0.038 + k * 0.012), M["print_grey"], bev=0,
            parent=ab)
    text("archive_print", "CONTENTS", "verdanab.ttf", 0.005, (-0.068, -ad / 2 - 0.0014, 0.078), M["print_grey"],
         ax="LEFT", rot=(90, 0, 0), parent=ab)
    text("archive_text", "INVOICES\n2009–2014", "Inkfree.ttf", 0.0165, (0.01, -ad / 2 - 0.0016, 0.052), M["marker"],
         rot=(90, 0, 0), parent=ab, line=0.85, fit=0.13)
    sb = grp("shoebox", (0.9, D - 0.13, top + ah), (0, 0, 2.5))
    sw, sd, sh = 0.23, 0.165, 0.1
    shoe_c = mat("shoebox", "#8a6a4e", 0.7)
    box("shoe_body", (sw - 0.004, sd - 0.004, sh - 0.02), (0, 0, (sh - 0.02) / 2), shoe_c, bev=0.002, parent=sb)
    box("shoe_lid", (sw, sd, 0.03), (0, 0, sh - 0.015), mat("shoebox_lid", "#e8e2d2", 0.6), bev=0.002, parent=sb)
    box("shoe_endlabel", (0.001, 0.05, 0.025), (sw / 2 - 0.001, 0.03, 0.04), M["pin_white"], bev=0, parent=sb)
    box("shoe_tape", (0.16, 0.0008, 0.028), (0, -sd / 2 - 0.0002, sh - 0.016), M["tape"], bev=0, parent=sb)
    text("shoe_text", "MANUALS & WARRANTIES", "Inkfree.ttf", 0.0135, (0, -sd / 2 - 0.0008, sh - 0.017), M["marker"],
         rot=(90, 0, 0), parent=sb, fit=0.15)
    # the binders, labelled in Martin's hand (the README: supplier logins are in the red one)
    bcols = [("binder_navy", "INVOICES\n2015–"), ("binder_red", "SUPPLIERS"), ("binder_green", "VAT"),
             ("binder_black", "WARRANTIES")]
    for i, (mn, lbl) in enumerate(bcols):
        x = 1.068 + i * 0.066
        b = grp(f"binder{i}", (x, D - 0.135, top), (0, 0, (-1.5, 1, -0.5, 2)[i]))
        box(f"binder{i}_body", (0.06, 0.26, 0.315), (0, 0, 0.1575), M[mn], bev=0.006, parent=b)
        box(f"binder{i}_pocket", (0.048, 0.0014, 0.11), (0, -0.1306, 0.17), mat("binder_pocket", "#dfe3e6", 0.15,
                                                                                spec=0.6), bev=0.001, parent=b)
        box(f"binder{i}_label", (0.044, 0.0012, 0.1), (0, -0.1304, 0.17), lab_m, bev=0, parent=b)
        text(f"binder{i}_text", lbl, "Inkfree.ttf", 0.0115, (0, -0.1316, 0.17), M["marker"], rot=(90, -90, 0), parent=b,
             fit=0.09, line=0.9)
        torus(f"binder{i}_hole", 0.0085, 0.0022, (0, -0.1305, 0.06), M["hole"], rot=(90, 0, 0), nR=14, nr=5, parent=b)
    # the spare headset, in its box, on shelf A (parts list: "Headset FSA 1-1/8in: shelf A")
    product_box("headset_box", (0.075, 0.075, 0.062), (1.375, D - 0.07, top + 0.031), None,
                mat("headset_box", "#26282c", 0.5), mat("headset_band", "#c9a54a", 0.4), "HEADSET\n1-1/8\"", M,
                rot=(0, 0, -6), font_sz=0.0072, label_m=M["pin_white"])


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


def build_headphones(M, hp, name="hp"):
    """Theo's headphones (teal pads), standing on their cups; they go to Lisbon with him."""
    pad_m = mat("hp_pad", "#2f6f6a", 0.85)
    for s in (-1, 1):
        cup = grp(f"{name}_cup{s}", (s * 0.072, 0, 0.044), (0, 90 * s, 0), parent=hp)
        cyl(f"{name}_shell{s}", 0.044, 0.03, (0, 0, -0.012), M["plastic_blk"], n=20, bev=0.01, seg=2, parent=cup)
        torus(f"{name}_pad{s}", 0.032, 0.012, (0, 0, 0.008), pad_m, nR=20, nr=8, parent=cup)
        cyl(f"{name}_cap{s}", 0.022, 0.004, (0, 0, -0.028), M["steel_dk"], n=16, parent=cup)
        tube(f"{name}_yoke{s}", (s * 0.09, 0, 0.07), (s * 0.084, 0, 0.115), 0.004, M["steel"], n=6, parent=hp)
    arc = [(0.086 * cos(radians(a)), 0.0, 0.082 + 0.085 * sin(radians(a))) for a in range(0, 181, 15)]
    curve(f"{name}_band", arc, 0.0085, M["plastic_blk"], parent=hp, res=6).scale = (1.0, 2.2, 1.0)
    return hp


def build_plant(M, parent, name="plant"):
    """Theo's desk plant, a little snake plant in a terracotta pot. Seeded so it's the same plant in Lisbon."""
    rr = random.Random(2009)
    lathe(name + "_pot", [(0.0, 0.0), (0.045, 0.0), (0.058, 0.11), (0.062, 0.11), (0.062, 0.125), (0.0, 0.125)], n=14,
          m=M["terracotta"], parent=parent)
    cyl(name + "_soil", 0.056, 0.004, (0, 0, 0.122), mat("soil", "#3a2a1f", 0.95), n=14, parent=parent)
    for k in range(9):
        a = 2 * pi * k / 9 + rr.uniform(-0.2, 0.2)
        L = rr.uniform(0.13, 0.2)
        lean = rr.uniform(18, 38)
        leaf = flat(f"{name}_leaf{k}", [(0, -0.012), (L * 0.6, -0.018), (L, 0), (L * 0.6, 0.018), (0, 0.012)], 0,
                    M["plant"] if k % 2 else M["plant_dk"], parent)
        leaf.location = (0, 0, 0.12)
        leaf.rotation_euler = (0.0, radians(-(90 - lean)), a)
        sd = leaf.modifiers.new("Solid", "SOLIDIFY")
        sd.thickness = 0.002
    return parent


def build_theo(M, kb, mug):
    """Theo's last week: his keys on the keyboard, the box for Lisbon, his headphones, cold coffee."""
    build_backoffice_key(M, kb)
    use("THEO")
    cyl("coffee", 0.0362, 0.002, (0, 0, 0.026), M["coffee"], n=24, parent=mug)
    # headphones on the desk, left of the keyboard
    hp = build_headphones(M, grp("headphones", (0.57, 2.2, DZ), (0, 0, 18)))
    port("hp_cup", (-0.112, 0.0, 0.03), (-0.4, -0.25, -0.88), hp)
    # the lead runs to the tower's front headphone jack
    at, d = port_frame("hp")
    st = connector("hp_jack_plug", "jack", at, d, M)
    cable("hp_cable", [st, st + d * 0.012, at + d * 0.05 + Vector((0.0, 0, -0.05)), (0.375, 2.2, DZ + 0.02),
                       (0.4, 2.16, DZ + 0.0018), (0.45, 2.13, DZ + 0.0018), (0.5, 2.15, DZ + 0.0018)] +
          bush_end("hp_lead", "hp_cup", M, out=0.03),
          0.0016, M["plastic_blk"])
    # the 2009 photo, framed, on his side of the desk (it goes to Lisbon with him)
    build_photo_frame(M, (1.585, 2.47, DZ), -14)
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
    build_plant(M, grp("plant", (0.1, 0.06, bh - 0.12), parent=bxg))
    tube("poster_tube", (-0.17, 0.08, 0.05), (-0.08, 0.02, bh + 0.25), 0.035, M["kraft"], n=12, parent=bxg)
    sphere("hoodie_lump", 0.13, (-0.07, -0.05, bh - 0.06), M["hoodie"], ico=2, parent=bxg, scale=(1.3, 0.95, 0.55))
    curve("hoodie_sleeve", [(-0.12, -0.08, bh - 0.02), (-0.2, -0.12, bh + 0.02), (-0.252, -0.12, bh - 0.005),
                            (-0.262, -0.12, bh - 0.12), (-0.258, -0.1, bh - 0.2)], 0.032, M["hoodie"], parent=bxg, res=6)


def _minimum(nt, a, b):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MINIMUM"
    nt.links.new(a.outputs[0], m.inputs[0])
    nt.links.new(b.outputs[0], m.inputs[1])
    return m


def rag_material():
    """A red cotton shop towel: a fine weave, a darker hem, black grease worked into it in patches."""
    if "shop_rag" in MATS:
        return MATS["shop_rag"]
    m = mat("shop_rag", "#8f2f28", 0.92)
    nt, b = m.node_tree, principled(m)
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    # hem: within 3% of any edge of the cloth (UV is the flat cloth before it was crumpled)
    edge = None
    for comp, inv in (("X", False), ("X", True), ("Y", False), ("Y", True)):
        mth = nt.nodes.new("ShaderNodeMath")
        if inv:
            mth.operation = "SUBTRACT"
            mth.inputs[0].default_value = 1.0
            nt.links.new(sep.outputs[comp], mth.inputs[1])
        else:
            mth.operation = "ADD"
            nt.links.new(sep.outputs[comp], mth.inputs[0])
            mth.inputs[1].default_value = 0.0
        edge = mth if edge is None else _minimum(nt, edge, mth)
    hem = nt.nodes.new("ShaderNodeMath")
    hem.operation = "LESS_THAN"
    nt.links.new(edge.outputs[0], hem.inputs[0])
    hem.inputs[1].default_value = 0.03
    cloth = _mix(nt, hem.outputs[0], "#8f2f28", "#6a221d")
    wave = nt.nodes.new("ShaderNodeTexWave")                  # the weave
    wave.inputs["Scale"].default_value = 160.0
    wave.inputs["Distortion"].default_value = 1.5
    nt.links.new(uv.outputs["UV"], wave.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")                   # grease: low-frequency blotches, sharpened
    nz.inputs["Scale"].default_value = 3.2
    nz.inputs["Detail"].default_value = 5.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(uv.outputs["UV"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.5
    mr.inputs["From Max"].default_value = 0.62
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(mr.outputs["Result"], sock(mx.inputs, "Factor_Float"))
    nt.links.new(cloth, sock(mx.inputs, "A_Color"))
    sock(mx.inputs, "B_Color").default_value = rgba("#2b201b")
    nt.links.new(sock(mx.outputs, "Result_Color"), b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.95
    rough.inputs["To Max"].default_value = 0.55
    nt.links.new(mr.outputs["Result"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    _bump(nt, b, wave.outputs["Fac"], 0.12, 0.0006)
    return m


def build_rag(M, loc, yaw):
    """Martin's workshop rag, dropped on the desk: a 30 cm red cotton square, bunched and folded, one corner turned
    over, the cloth drawn in where it buckles."""
    n = 28
    S = 0.3
    rr = random.Random(61)
    folds = [(rr.uniform(0, pi), rr.uniform(-0.08, 0.08), rr.uniform(0.006, 0.016), rr.uniform(0.008, 0.02))
             for _ in range(5)]
    bunch = Vector((0.03, -0.02))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(n):
        row = []
        for i in range(n):
            u, v = i / (n - 1), j / (n - 1)
            p = Vector(((u - 0.5) * S, (v - 0.5) * S))
            h = 0.0
            for a, off, amp, wid in folds:
                dd = p.x * cos(a) + p.y * sin(a) - off
                h += amp * math.exp(-(dd / wid) ** 2)
            r = (p - bunch).length
            h += 0.022 * math.exp(-(r / 0.06) ** 2)
            h += 0.002 * sin(p.x * 90 + p.y * 40) * cos(p.y * 70)
            pull = 0.35 * math.exp(-(r / 0.11) ** 2)            # the cloth gathers toward the bunch
            q = p + (bunch - p) * pull
            if u + v > 1.62:                                    # one corner turned over
                d = (u + v - 1.62) / 2
                q = Vector((q.x - d * S, q.y - d * S))
                h = 0.004 + 0.3 * h + 0.003 * d
            row.append((bm.verts.new((q.x, q.y, max(0.0, h))), (u, v)))
        grid.append(row)
    for j in range(n - 1):
        for i in range(n - 1):
            vs = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            f = bm.faces.new([a for a, _ in vs])
            for lp, (_, t) in zip(f.loops, vs):
                lp[uvl].uv = t
    rag = finish("rag", bm, rag_material(), None, loc, (0, 0, yaw), smooth=True, angle=80)
    sd = rag.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.0022
    sd.offset = 1
    return rag


def build_martin(M, mug):
    """Monday: Martin's reading glasses on a cord, his rag, a paper job card, a pencil, tea in Theo's mug."""
    use("MARTIN")
    cyl("tea", 0.0362, 0.002, (0, 0, 0.079), M["tea"], n=24, parent=mug)
    # job card, Monday's first job: Anika's brakes (job 4478 on the screens; she needs two pairs of pads)
    job_card(M, "job_card", (0.58, 2.2, DZ + 0.0006), 10, 4478,
             [("Name", "Anika Banerjee"), ("Bike", "Trek FX 3"), ("Work", "brake bleed + pads"), ("", "F + R (2 pairs)"),
              ("Due", "Tue 24/11")])
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
    build_rag(M, (1.66, 2.165, DZ + 0.0015), 18)
    # pencil behind the keyboard (still there on Tuesday)
    use("MARTIN_KIT")
    pc = grp("pencil", (1.07, 2.335, DZ + 0.0045), (0, 90, 8))
    cyl("pencil_body", 0.0045, 0.16, (0, 0, 0), M["pencil"], n=6, parent=pc)
    cyl("pencil_tip", 0.0045, 0.018, (0, 0, -0.089), M["pencil_wood"], r2=0.0012, n=6, parent=pc).rotation_euler = _rot((180, 0, 0))
    cyl("pencil_ferrule", 0.0046, 0.008, (0, 0, 0.084), M["steel"], n=10, parent=pc)
    cyl("pencil_eraser", 0.0044, 0.008, (0, 0, 0.092), M["eraser"], n=10, parent=pc)


def job_card(M, name, loc, yaw, no, fields, mech=None, parent=None, tilt=(0, 0)):
    """A Spokes & Sprockets paper job card, filled in by Martin at the counter (Ink Free is his hand). `mech` =
    (crossed-out name, new name) adds the mechanic line with a correction."""
    jc = grp(name, loc, (tilt[0], tilt[1], yaw), parent=parent)
    box(name + "_card", (0.1, 0.15, 0.0008), (0, 0, 0), M["manila"], bev=0, parent=jc)
    zt = 0.0006
    text(name + "_head", "SPOKES & SPROCKETS", "verdanab.ttf", 0.0062, (0, 0.062, zt), M["ink"], parent=jc, fit=0.088)
    text(name + "_head2", "JOB CARD", "verdana.ttf", 0.0055, (0, 0.053, zt), M["print_grey"], parent=jc)
    text(name + "_no", f"No. {no}", "consola.ttf", 0.005, (0.042, 0.043, zt), M["red_ink"], ax="RIGHT", parent=jc)
    ys = (0.03, 0.014, -0.002, -0.016, -0.032, -0.048)
    for i, ((lab, val), y) in enumerate(zip(fields, ys)):
        if lab:
            text(f"{name}_lab{i}", lab + ":", "verdana.ttf", 0.0046, (-0.044, y, zt), M["print_grey"], ax="LEFT",
                 parent=jc)
        rect(f"{name}_line{i}", -0.024, y - 0.0025, 0.044, y - 0.0022, zt, M["print_grey"], jc)
        text(f"{name}_val{i}", val, "Inkfree.ttf", 0.008, (-0.022, y + 0.0004, zt + 0.0001), M["blue_ink"], ax="LEFT",
             parent=jc, fit=0.064)
    if mech:
        y = -0.062
        text(name + "_mlab", "Mech:", "verdana.ttf", 0.0046, (-0.044, y, zt), M["print_grey"], ax="LEFT", parent=jc)
        text(name + "_mold", mech[0], "Inkfree.ttf", 0.008, (-0.022, y + 0.0004, zt + 0.0001), M["blue_ink"],
             ax="LEFT", parent=jc)
        box(name + "_strike", (0.016, 0.0009, 0.0002), (-0.0145, y + 0.0018, zt + 0.0002), M["blue_ink"],
            rot=(0, 0, 8), bev=0, parent=jc)
        text(name + "_mnew", mech[1], "Inkfree.ttf", 0.0088, (0.0, y + 0.0006, zt + 0.0001), M["blue_ink"],
             ax="LEFT", parent=jc, rot=(0, 0, 4))
    else:
        text(name + "_foot", "est. 1987", "georgia.ttf", 0.0045, (0, -0.066, zt), M["print_grey"], parent=jc)
    return jc


def build_helmet(M, parent, loc, rot):
    """Priya's road helmet: a matt shell with vents (cut through to the grey foam), a rear retention dial, black
    webbing straps and buckle; hung by its straps over the corner of the chair back."""
    g = grp("helmet", loc, rot, parent=parent)
    shell_m = mat("helmet_shell", "#c95b36", 0.42, coat=0.35)
    foam = mat("helmet_foam", "#8f9296", 0.85)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=16, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        z = max(z, -0.05)
        tail = 1.0 + 0.18 * max(0.0, y)                      # longer at the back, a little tail
        v.co = Vector((x * 0.1, y * 0.135 * tail, z * 0.105))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.co.z < -0.004 for v in f.verts)], context="FACES")
    shell = finish("helmet_shell", bm, [shell_m, foam], g, angle=50)
    sd = shell.modifiers.new("Solid", "SOLIDIFY")
    sd.thickness = 0.018
    sd.material_offset = 1
    cutters = []
    for k, (x, y0, y1, z) in enumerate(((0.0, -0.07, 0.075, 0.12), (-0.038, -0.065, 0.07, 0.11),
                                        (0.038, -0.065, 0.07, 0.11), (-0.07, -0.035, 0.05, 0.085),
                                        (0.07, -0.035, 0.05, 0.085))):
        c = tube(f"helmet_vent{k}", (x, y0, z), (x * 1.04, y1, z - 0.01), 0.011, foam, n=8, parent=g)
        c.scale = (1.0, 1.0, 1.0)
        c.hide_render = True
        cutters.append(c)
    for c in cutters:
        bo = shell.modifiers.new("Vent", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.object = c
        bo.solver = "EXACT"
        try:
            bo.material_mode = "TRANSFER"
        except (AttributeError, TypeError):
            pass
    torus("helmet_rim", 1.0, 0.07, (0, 0, -0.003), mat("helmet_trim", "#2a2b2e", 0.5), nR=40, nr=6, parent=g,
          scale=(0.1, 0.142, 0.1))
    box("helmet_dial", (0.034, 0.012, 0.018), (0, 0.15, 0.0), M["plastic_blk"], bev=0.005, parent=g)
    box("helmet_reflector", (0.03, 0.002, 0.008), (0, 0.157, 0.018), mat("reflector", "#d9d9d9", 0.25, metal=0.5),
        bev=0.001, parent=g)
    web = mat("webbing", "#1b1b1d", 0.8)
    for s in (-1, 1):
        curve(f"helmet_strap{s}", [(s * 0.095, -0.02, 0.005), (s * 0.085, 0.0, -0.06), (s * 0.03, 0.02, -0.11),
                                   (0.0, 0.03, -0.13)], 0.004, web, parent=g, res=6, bres=1).scale = (1, 1, 1)
    box("helmet_buckle", (0.022, 0.008, 0.016), (0, 0.03, -0.135), M["plastic_blk"], bev=0.003, parent=g)
    return g


def build_coffee_cup(M, loc, yaw, name="coffee_cup", label="PRIYA", font_file="MISTRAL.TTF"):
    """A takeaway coffee: white paper cup, a plain kraft sleeve, a white sip lid, the barista's marker on the cup."""
    g = grp(name, loc, (0, 0, yaw))
    r0, r1, h = 0.029, 0.044, 0.132
    cupm = mat("paper_cup", "#f3f0e9", 0.55, spec=0.35)
    lathe(name + "_body", [(0.0, 0.0), (r0, 0.0), (r0 + 0.0008, 0.003), (r1, h), (r1 + 0.0015, h + 0.002),
                           (r1 - 0.002, h + 0.001), (0.0, h - 0.004)], n=32, m=cupm, parent=g)
    zs0, zs1 = 0.035, 0.088
    rs0, rs1 = r0 + (r1 - r0) * zs0 / h + 0.0012, r0 + (r1 - r0) * zs1 / h + 0.0012
    lathe(name + "_sleeve", [(rs0 - 0.0012, zs0), (rs0, zs0), (rs1, zs1), (rs1 - 0.0012, zs1)], n=32,
          m=noisy("sleeve_kraft", "#a8814f", "#97723f", 0.85, scale=60.0, bump=0.15), parent=g)
    lid = mat("cup_lid", "#f6f4ef", 0.3, spec=0.5)
    lathe(name + "_lid", [(0.0, h + 0.012), (0.03, h + 0.012), (0.036, h + 0.0145), (0.043, h + 0.0135),
                          (0.0465, h + 0.006), (0.0462, h + 0.0005), (0.0445, h + 0.0002), (0.0, h + 0.002)], n=32,
          m=lid, parent=g)
    box(name + "_sip", (0.012, 0.004, 0.001), (0, -0.038, h + 0.0136), M["hole"], rot=(0, 0, 0), bev=0.0015,
        parent=g)
    # the name, in the barista's marker, wrapped round the cup above the sleeve (facing -y)
    t = text(name + "_src", label, font_file, 0.031, (0, 0, 0), M["marker"], extrude=0.0002)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
    bpy.data.objects.remove(t, do_unlink=True)
    zc = 0.111
    for v in me.vertices:
        x, y, _ = v.co
        z = zc + y * 0.95 + x * 0.12                         # written on the slant
        rr = r0 + (r1 - r0) * z / h + 0.0004
        th = x / rr + radians(8)
        v.co = Vector((rr * sin(th), -rr * cos(th), z))
    me.materials.clear()
    me.materials.append(M["marker"])
    link(bpy.data.objects.new(name + "_name", me), g)
    return g


def build_toolroll(M, loc, yaw):
    """Priya's toolroll, unrolled: waxed olive canvas, leather ties, one sewn pocket per tool and every tool in its
    pocket, clean. Tyre levers, a spoke key, cable cutters, hex keys, a chain tool, a lockring tool, a screwdriver,
    a pick."""
    g = grp("toolroll", loc, (0, 0, yaw))
    L, Wd = 0.46, 0.23
    canvas = noisy("waxed_canvas", "#55613f", "#4a5537", 0.55, scale=220.0, bump=0.08)
    pocket = noisy("waxed_canvas_lt", "#66734c", "#5a6643", 0.6, scale=220.0, bump=0.08)
    stitch = mat("stitch", "#c9c2a6", 0.7)
    leather = mat("leather", "#7a4a2a", 0.5, coat=0.2)
    box("roll_base", (L, Wd, 0.003), (0, 0, 0.0015), canvas, bev=0.0012, parent=g)
    cyl("roll_curl", 0.012, Wd - 0.004, (-L / 2 - 0.006, 0, 0.012), canvas, rot=(90, 0, 0), n=14, parent=g)
    box("roll_pocket", (L - 0.02, 0.105, 0.003), (0, -Wd / 2 + 0.06, 0.0042), pocket, bev=0.001, parent=g)
    box("roll_flap", (L - 0.01, 0.06, 0.0025), (0, Wd / 2 - 0.028, 0.0038), pocket, bev=0.001, parent=g)
    for k in range(10):
        x = -L / 2 + 0.02 + k * (L - 0.04) / 9
        box(f"roll_seam{k}", (0.0012, 0.105, 0.0004), (x, -Wd / 2 + 0.06, 0.006), stitch, bev=0, parent=g)
    box("roll_hem", (L - 0.02, 0.0012, 0.0004), (0, -Wd / 2 + 0.112, 0.006), stitch, bev=0, parent=g)
    for s in (-1, 1):                                         # leather ties lying out to the side
        curve(f"roll_tie{s}", [(L / 2 - 0.01, s * 0.05, 0.004), (L / 2 + 0.05, s * 0.06, 0.003),
                               (L / 2 + 0.11, s * 0.05 + 0.01, 0.003)], 0.0035, leather, parent=g, res=6,
              bres=1).scale = (1, 1, 0.35)
    slot = (L - 0.04) / 9
    zt = 0.0062

    def at(k):
        return -L / 2 + 0.02 + (k + 0.5) * slot

    blue = mat("lever_blue", "#2f5fa8", 0.35, coat=0.3)
    for k in range(3):                                        # tyre levers, a set of three
        box(f"tyre_lever{k}", (0.017, 0.11, 0.005), (at(0) - 0.006 + 0.006 * k, -0.04, zt + 0.0055 * k), blue,
            bev=0.004, parent=g)
    disc("spoke_key", at(1), 0.01, 0.017, zt, mat("spoke_key_red", "#b3392c", 0.35, coat=0.3), g, n=20)
    cyl("spoke_key_body", 0.017, 0.006, (at(1), 0.01, zt), mat("spoke_key_red", "#b3392c", 0.35), n=20, parent=g)
    red = mat("grip_red", "#a8322a", 0.5)
    for s in (-1, 1):                                         # cable cutters
        box(f"cutter_handle{s}", (0.011, 0.1, 0.007), (at(2) + s * 0.0065, -0.05, zt + 0.003), red, rot=(0, 0, -s * 3),
            bev=0.003, parent=g)
    box("cutter_jaw", (0.02, 0.035, 0.008), (at(2), 0.025, zt + 0.004), M["steel_dk"], bev=0.003, parent=g)
    for k, (Lk, r) in enumerate(((0.1, 0.0032), (0.088, 0.0026), (0.076, 0.002), (0.064, 0.0016))):   # hex keys
        x = at(3) - 0.008 + k * 0.0055
        cyl(f"hex{k}_long", r, Lk, (x, -0.06 + Lk / 2, zt + r), M["steel_dk"], rot=(90, 0, 0), n=6, parent=g)
        cyl(f"hex{k}_short", r, 0.028, (x + 0.014, -0.06 + Lk, zt + r), M["steel_dk"], rot=(0, 90, 0), n=6, parent=g)
    box("chain_tool", (0.024, 0.05, 0.016), (at(4), 0.0, zt + 0.008), M["plastic_blk"], bev=0.004, parent=g)
    cyl("chain_tool_screw", 0.003, 0.07, (at(4), -0.04, zt + 0.008), M["steel"], rot=(90, 0, 0), n=8, parent=g)
    cyl("chain_tool_handle", 0.004, 0.04, (at(4), -0.075, zt + 0.008), M["steel"], rot=(0, 90, 0), n=8, parent=g)
    cyl("lockring_tool", 0.013, 0.03, (at(5), 0.02, zt + 0.013), M["steel_dk"], rot=(90, 0, 0), n=12, parent=g)
    for k in range(12):
        a = 2 * pi * k / 12
        box(f"lockring_spline{k}", (0.003, 0.004, 0.003), (at(5) + 0.013 * cos(a), 0.037, zt + 0.013 + 0.013 * sin(a)),
            M["steel_dk"], bev=0, parent=g)
    cyl("driver_handle", 0.011, 0.075, (at(6), 0.01, zt + 0.011), mat("driver_yellow", "#e0b53a", 0.35, coat=0.3),
        rot=(90, 0, 0), n=10, bev=0.003, parent=g)
    cyl("driver_shaft", 0.0028, 0.08, (at(6), -0.065, zt + 0.011), M["chrome"], rot=(90, 0, 0), n=8, parent=g)
    cyl("pick_handle", 0.0065, 0.06, (at(7), 0.02, zt + 0.0065), M["plastic_blk"], rot=(90, 0, 0), n=8, parent=g)
    cyl("pick_shaft", 0.0014, 0.07, (at(7), -0.045, zt + 0.0065), M["chrome"], rot=(90, 0, 0), n=6, parent=g)
    box("pedal_spanner", (0.02, 0.15, 0.004), (at(8), -0.02, zt + 0.002), M["steel"], bev=0.002, parent=g)
    return g


def build_priya(M, mug):
    """Tuesday morning, Priya's first day: her helmet hooked on the chair, her takeaway coffee (PRIYA in the barista's
    marker), her toolroll unrolled and checked, the two wheel-build job cards Martin moved to her (Dev crossed out).
    Theo's things are gone; Martin's mug (his tea from earlier, half drunk) and his pencil stay. No sticky notes."""
    use("PRIYA")
    cyl("tea_half", 0.0362, 0.002, (0, 0, 0.052), M["tea"], n=24, parent=mug)
    build_coffee_cup(M, (1.585, 2.345, DZ), -12)
    build_toolroll(M, (0.535, 2.158, DZ), -3)
    kb = bpy.data.objects["keyboard"]                         # Martin left her the two cards on the keyboard
    job_card(M, "job_4471", (-0.13, 0.005, 0.0312), 9, 4471,
             [("Name", "Rachel Okafor"), ("Bike", "Genesis Croix de Fer"), ("Work", "wheel build, front"),
              ("", "32 hole · 6 hrs"), ("Due", "Tue 24/11")], mech=("Dev", "Priya"), parent=kb)
    job_card(M, "job_4472", (-0.06, -0.012, 0.0322), -6, 4472,
             [("Name", "Magnus Lindqvist"), ("Bike", "Bianchi Infinito"), ("Work", "wheel build, rear"),
              ("", "32 hole · 5.5 hrs"), ("Due", "Wed 25/11")], mech=("Dev", "Priya"), parent=kb)
    chair = bpy.data.objects["chair"]
    build_helmet(M, chair, (0.11, -0.318, 0.94), (78, 0, 8))
    web = mat("webbing", "#1b1b1d", 0.8)
    for k, dx in enumerate((-0.03, 0.03)):                   # the straps, looped over the top of the chair back
        curve(f"helmet_hang{k}", [(0.12 + dx, -0.33, 0.97), (0.12 + dx, -0.322, 1.08), (0.12 + dx * 0.6, -0.29, 1.125),
                                  (0.12 + dx * 0.4, -0.25, 1.12), (0.12 + dx * 0.3, -0.232, 1.07)], 0.0042, web,
              parent=chair, res=6, bres=1)


def build_close(M, kb):
    """The goodnight shot (scene 9): Martin's reading glasses folded on the keyboard, nothing else of the day left."""
    use("CLOSE")
    g = grp("glasses_folded", (-0.12, 0.0, 0.0312), (0, 0, 8), parent=kb)
    for s in (-1, 1):
        pts = []
        for i in range(16):
            a = 2 * pi * i / 16
            ca, sa = cos(a), sin(a)
            pts.append((s * 0.031 + 0.026 * math.copysign(abs(ca) ** 0.6, ca),
                        0.019 * math.copysign(abs(sa) ** 0.7, sa), 0.012))
        curve(f"glf_rim{s}", pts, 0.0024, M["tortoise"], parent=g, cyclic=True, res=3, bres=1)
        flat(f"glf_lens{s}", [(p[0], p[1]) for p in pts], 0.012, M["lens"], g)
        tube(f"glf_temple{s}", (s * 0.056, 0.004, 0.009), (-s * 0.03, 0.006 + 0.002 * s, 0.004 + 0.003 * (s + 1)),
             0.0013, M["tortoise"], n=6, parent=g)
    curve("glf_bridge", [(-0.007, 0.006, 0.012), (0.0, 0.01, 0.013), (0.007, 0.006, 0.012)], 0.0014, M["tortoise"],
          parent=g)
    curve("glf_cord", [(-0.056, 0.0, 0.009), (-0.08, -0.03, 0.002), (-0.05, -0.06, 0.001), (0.02, -0.065, 0.001),
                       (0.07, -0.04, 0.002), (0.056, 0.0, 0.009)], 0.0009, M["cord"], parent=g, res=8)


def build_note(M, head):
    """The one sticky note in the whole film: Theo's, on the bezel. Gone on Tuesday (Martin peeled it off once the
    report was built)."""
    use("NOTE")
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
    light("L_bell_rim", "AREA", (3.3, 3.9, 1.22), 5.0, (1.0, 0.86, 0.66), "NIGHT", target=(3.12, 3.62, 1.0),
          size=0.35, size_y=0.08)
    # --- monday: cool daylight through the window, sky fill, workshop strip light
    sun = light("L_sun", "SUN", (-2, 1.5, 3), 22.0, (1.0, 0.97, 0.93), "MONDAY")
    sun.data.angle = radians(3)
    aim(sun, (-2 + 0.65, 1.5 + 0.55, 3 - 0.52))
    light("L_window_day", "AREA", (-0.16, (wy0 + wy1) / 2, (wz0 + wz1) / 2 + 0.05), 90.0, (0.72, 0.84, 1.0), "MONDAY",
          target=(1.4, 2.3, 0.9), size=0.95, size_y=1.0)
    light("L_strip", "AREA", (3.1, 5.9, 2.12), 140.0, (0.93, 0.97, 1.0), "MONDAY", target=(3.0, 3.6, 0.6), size=1.15, size_y=0.12)
    light("L_screen_day", "AREA", c + n * 0.01, 2.0, (0.62, 0.76, 1.0), "MONDAY", target=c + n, size=0.4, size_y=0.25)
    light("L_drawer_bounce", "AREA", (2.0, 1.55, 0.62), 4.0, (1.0, 0.9, 0.8), "MONDAY", target=(1.96, 2.03, 0.29),
          size=0.4, size_y=0.3)
    light("L_drawer_bounce_n", "AREA", (2.0, 1.55, 0.62), 1.5, (1.0, 0.8, 0.6), "NIGHT", target=(1.96, 2.03, 0.29),
          size=0.4, size_y=0.3)
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
    camera("CAM_medium_tuesday", (1.5, 0.4, 1.33), (1.3, 2.5, 0.97), 27, 2.8, (1.3, 2.3, 0.85))
    camera("CAM_board", (1.84, 1.98, 1.42), (1.84, 2.8, 1.4), 36, 2.8, (1.84, 2.78, 1.4))
    camera("CAM_shelf", (0.74, 1.92, 2.08), (0.5, 2.6, 1.68), 36, 4.0, (0.36, 2.5, 1.77))
    camera("CAM_bell", (2.86, 3.31, 1.1), (3.17, 3.63, 0.997), 60, 6.3, (3.13, 3.615, 1.0))
    camera("CAM_screen", (1.16, 2.2, 1.075), (1.1, 2.51, 1.03), 40, 4.0, (1.1, 2.51, 1.03))
    camera("CAM_close_half", (1.18, 1.3, 1.34), (0.98, 2.52, 0.97), 30, 2.8, (1.0, 2.25, 0.82))
    camera("CAM_drawer", (2.04, 1.7, 1.1), (1.96, 1.98, 0.3), 32, 5.6, (1.96, 1.98, 0.3))
    camera("CAM_cables_top", (1.42, 2.66, 0.9), (0.5, 2.73, 0.77), 20, 16.0, (0.8, 2.73, 0.77))
    camera("CAM_cables_under", (0.75, 1.55, 0.32), (0.62, 2.74, 0.14), 22, 16.0, (0.62, 2.7, 0.1))


CHAIR_POSE = {"night": ((1.66, 1.55, 0.0), 58), "monday": ((1.66, 1.55, 0.0), 58),
              "tuesday": ((1.72, 1.68, 0.0), 18), "close": ((1.58, 1.62, 0.0), 40)}


def apply_preset(name, M, hands):
    """night = Thursday 19 Nov, 21:47 (Theo's last week); monday = 23 Nov, 08:52 (Martin); tuesday = 24 Nov, 08:34
    (Priya's first morning); close = the goodnight shot, 18:40, the PC asleep. See CONTINUITY.md."""
    night = name in ("night", "close")
    vis = {"NIGHT": night, "MONDAY": not night, "THEO": name == "night", "MARTIN": name == "monday",
           "MARTIN_KIT": name in ("monday", "tuesday"), "PRIYA": name == "tuesday", "CLOSE": name == "close",
           "NOTE": name in ("night", "monday")}
    for k, v in vis.items():
        COLL[k].hide_render = not v
    sc = bpy.context.scene
    bg = sc.world.node_tree.nodes["Background"]
    if night:
        bg.inputs[0].default_value = rgba("#1c2333")
        bg.inputs[1].default_value = 0.45
    else:
        bg.inputs[0].default_value = rgba("#b4c2d2")
        bg.inputs[1].default_value = 0.5
    lamp_on = name == "night"
    principled(M["bulb"]).inputs["Emission Strength"].default_value = 20.0 if lamp_on else 0.0
    LIGHTS["L_lamp"].data.energy = 40.0 if lamp_on else 0.0
    LIGHTS["L_box_kick"].data.energy = 7.0 if name == "night" else 0.0
    LIGHTS["L_worklamp"].data.energy = 90.0 if name == "night" else 30.0
    LIGHTS["L_pegboard"].data.energy = 28.0 if name == "night" else 12.0
    LIGHTS["L_floor_spill"].data.energy = 9.0 if lamp_on else 2.5
    LIGHTS["L_bounce"].data.energy = 7.0 if lamp_on else 2.0
    principled(M["tube"]).inputs["Emission Strength"].default_value = 0.0 if night else 9.0
    sky = principled(M["outside_sky"])
    sky.inputs["Emission Color"].default_value = rgba("#0c1424") if night else rgba("#dfe8ef")
    sky.inputs["Emission Strength"].default_value = 1.0 if night else 3.0
    principled(M["outside_win"]).inputs["Emission Strength"].default_value = 3.0 if night else 0.0
    principled(M["outside_brick"]).inputs["Base Color"].default_value = rgba("#6c4537")
    # daylight: Monday's cool morning; Tuesday's sun earlier, lower and warmer, raking across the desk
    sun = LIGHTS["L_sun"]
    d = Vector((0.72, 0.5, -0.3)) if name == "tuesday" else Vector((0.65, 0.55, -0.52))
    sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sun.data.energy = 30.0 if name == "tuesday" else 22.0
    sun.data.color = (1.0, 0.86, 0.68) if name == "tuesday" else (1.0, 0.97, 0.93)
    LIGHTS["L_window_day"].data.color = (0.86, 0.88, 0.95) if name == "tuesday" else (0.72, 0.84, 1.0)
    LIGHTS["L_room_fill"].data.energy = 24.0 if name == "tuesday" else 40.0
    bpy.data.objects["mug"].location = (1.4, 2.385, DZ) if name == "tuesday" else (1.74, 2.36, DZ)
    loc, rz = CHAIR_POSE[name]
    ch = bpy.data.objects["chair"]
    ch.location = loc
    ch.rotation_euler = (0, 0, radians(rz))
    set_screen(SCREEN_PATHS[name], SCREEN_FIT[0])
    SCREEN["bright"].outputs[0].default_value = SCREEN_BRIGHT[name]
    mean = SCREEN.get("mean")
    if mean is not None:                                      # the screen lights the desk with its own picture
        lum = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
        tint = tuple(float(c) for c in (mean / max(mean.max(), 1e-6)) * 0.75 + 0.25)
        for nm, base in (("L_screen", 5.0), ("L_screen_day", 2.0)):
            LIGHTS[nm].data.energy = base * SCREEN_BRIGHT[name] * max(lum, 0.01) / 0.16
            LIGHTS[nm].data.color = tint
    for bs, st in REFLECT_EMIT:
        bs.inputs["Emission Strength"].default_value = st * REFLECT_LEVEL[name]
    sc.view_settings.exposure = {"night": 0.3, "monday": 0.0, "tuesday": 0.05, "close": 0.75}[name]
    hh, mm = CLOCK[name]
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
    try:
        ee.shadow_pool_size = "1024"                          # the screen's planar probe renders the set twice
    except TypeError:
        pass
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
    for name in ("SET", "WORKSHOP", "THEO", "MARTIN", "MARTIN_KIT", "PRIYA", "CLOSE", "NOTE", "NIGHT", "MONDAY",
                 "REFLECT", "CAMS"):
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    if args.regen_screen or not os.path.exists(PLACEHOLDER):
        make_placeholder(PLACEHOLDER)
        print("wrote", PLACEHOLDER)
    setup_render(args)
    M = build_materials()
    ensure_photo(M, args.regen_photo)
    for k, default in SCREENS.items():
        p = args.screen or getattr(args, "screen_" + k) or default
        SCREEN_PATHS[k] = os.path.abspath(p) if os.path.exists(p) else PLACEHOLDER
    SCREEN_FIT[0] = args.screen_fit
    screen_m = lcd_material(plain=args.lcd == "plain")

    build_room(M)
    if args.lcd != "plain":
        build_reflect_room(M)
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
    build_cables(M)
    hands = build_corkboard(M)
    build_shelf(M)
    mug = build_desk_props(M)
    build_theo(M, kb, mug)
    build_martin(M, mug)
    build_priya(M, mug)
    build_close(M, kb)
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
        cam, preset, fname, ev = SHOTS[shot][:4]
        res = SHOTS[shot][4] if len(SHOTS[shot]) > 4 else (1920, 1080)
        sc.render.resolution_x, sc.render.resolution_y = res
        apply_preset(preset, M, hands)
        sc.view_settings.exposure += ev
        sc.camera = bpy.data.objects[cam]
        grid_for_camera(sc.camera, args.scale)
        sc.render.filepath = os.path.join(OUT, fname)
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {shot} -> {fname} in {time.time() - t1:.1f}s")


if __name__ == "__main__":
    main()
