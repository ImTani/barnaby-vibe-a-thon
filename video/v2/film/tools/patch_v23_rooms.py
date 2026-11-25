"""v2.3 rooms (SHOTLIST v2.3 revisions 1 and 3): slow motivated pans on room holds over ~4 s (constant scale, no zoom),
the 4K wide plates when they land, and the desk-state transitions on Blender's new inserts, each with its fallback.
Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

# a pan: the same scale, a slow eased 2D move across the plate (optically a pan on a wide render)
sub('shots.js', """/** One motivated move: holds `from`""", """/** A pan or tilt: from (x0, y0) to (x1, y1) at scale s, starting at a (an action or a line), over d s, eased. */
const pan = (a, d, x0, y0, x1, y1, s) => move(a, d, [x0, y0, s], [x1, y1, s], 0);
/** One motivated move: holds `from`""")
sub('shots.js', """cursor, path2, clickK, typed, LIVE_FRAMES: frames, FILM_FPS, hold, move,""", """cursor, path2, clickK, typed, LIVE_FRAMES: frames, FILM_FPS, hold, move, pan,""")

# ---- 1.1 the opening: on Blender's 4K wide plate (when it lands), a slow pan from the rain on the window to the lamp
# pool, then Blender's s1_open from its approach (frame 133); otherwise s1_open (or the stills) as before
sub('scenes/s1.js', """        { src: 'world/01_wide_night.png', at: S, cam: hold(960, 540, 1.0),
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },""",
"""      ].concat(WIDE4K ? [
        { src: WIDE4K, at: S, cam: pan(M('light_up') + 1.2, APPROACH - M('light_up') - 1.6, 640, 470, 1180, 560, 1.22),
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/01_wide_night.png', at: APPROACH, cam: hold(960, 540, 1.0) },
      ] : [
        { src: 'world/01_wide_night.png', at: S, cam: hold(960, 540, 1.0),
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
      ]).concat([""")
sub('scenes/s1.js', """        { src: 'live/shop', at: M('screen'), fi: .12, pin: { shot: 's1_open', d: .6 }, cam: tabCam, state: t => state(t) },
      ], E);""", """        { src: 'live/shop', at: M('screen'), fi: .12, pin: { shot: 's1_open', d: .6 }, cam: tabCam, state: t => state(t) },
      ]), E);""")
sub('scenes/s1.js', """      run = seq(root, [""", """      const WIDE4K = pick('world/01_wide_night_4k.png', ''), APPROACH = -.5 + 132 / 24;      // s1_open's approach: frame 133
      run = seq(root, [""")
sub('scenes/s1.js', """      live = run.list[2].s;""", """      live = run.list.find(it => it.src === 'live/shop').s;""")

# ---- 2.3 / 2.8 slow pans across the night desk
sub('scenes/s2.js', """        { src: 'world/02_medium_night.png', at: M('box'), cam: hold(960, 610, 1.08) },""",
"""        { src: 'world/02_medium_night.png', at: M('box'), cam: pan(M('box') + .3, M('close_tabs') - M('box') - .5, 880, 610, 1040, 600, 1.12) },""")
sub('scenes/s2.js', """        { src: 'world/02_medium_night.png', at: M('desk_detail'), cam: hold(960, 620, 1.1) },""",
"""        { src: 'world/02_medium_night.png', at: M('desk_detail'), cam: pan(V(7), M('key') - V(7) - .3, 1050, 620, 890, 630, 1.12) },""")
# ---- night -> Monday: the match cut on the mug. Theo's mug in lamplight, the lamp clicks off on it, dark (scene 2's
# end); scene 3 opens on the same framing at dawn, the light rising, Martin's mug; then the Monday desk
sub('scenes/s2.js', """        { src: 'world/03_keys_night.png', at: M('key'), cam: move(M('key') + .2, 1.6, [760, 700, 1.1], [700, 800, 1.3], 0),
          grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` },""",
"""        { src: 'world/03_keys_night.png', at: M('key'), cam: move(M('key') + .2, 1.6, [760, 700, 1.1], [700, 800, 1.3], 0),
          grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` },
      ].concat(MUG ? [{ src: MUG, at: M('lamp_off') - 1.4, cam: hold(960, 540, 1.0), keepGrade: true,
          grade: t => `brightness(${lerp(1, .05, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` }] : []).concat([""")
sub('scenes/s2.js', """      run = seq(root, [""", """      const MUG = pick('world/x_mug_night.png', '');
      run = seq(root, [""")
sub('scenes/s2.js', """          grade: t => `brightness(${lerp(1, .05, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` }] : []).concat([
      ], E);""", """          grade: t => `brightness(${lerp(1, .05, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` }] : []), E);""")
sub('scenes/s3.js', """        { src: 'world/02_medium_night.png', at: S, cam: [960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5, keepFi: true, cam: hold(960, 600, 1.12, -.01),
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },""",
"""      ].concat(DAWN ? [
        { src: DAWN, at: S, cam: hold(960, 540, 1.0), keepGrade: true, grade: t => `brightness(${lerp(.05, 1, easeInOutSine(P(t, S + .5, M('monday') - S - .8))).toFixed(3)})` },
        { src: 'world/04_medium_monday.png', at: M('monday'), cam: hold(960, 600, 1.12) },
      ] : [
        { src: 'world/02_medium_night.png', at: S, cam: [960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5, keepFi: true, cam: hold(960, 600, 1.12, -.01),
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },
      ]).concat([""")
sub('scenes/s3.js', """        { src: 'world/x_shelf_monday.png', at: M('shelf'), cam: hold(680, 400, 1.18) },
      ], E);""", """        { src: 'world/x_shelf_monday.png', at: M('shelf'), cam: hold(680, 400, 1.18) },
      ]), E);""")
sub('scenes/s3.js', """      run = seq(root, [""", """      const DAWN = pick('world/x_mug_dawn.png', '');            // the match cut on the mug (with the night one)
      run = seq(root, [""")
sub('scenes/s3.js', """      mk = run.list[3].s;""", """      mk = run.list.find(it => it.src === 'comp/martin-key').s;""")
sub('scenes/s3.js', """    render(t) { run.render(t); if (!run.list[1].bl) sw.render(t, S + .2, S + 2.6, .9); },""",
"""    render(t) { run.render(t); if (!run.list[1].bl && run.list[1].src === 'world/04_medium_monday.png' && run.list[1].keepFi) sw.render(t, S + .2, S + 2.6, .9); },""")

# ---- 6.4 the dusk desk: a slow pan; dusk -> Tuesday: the empty chair at dusk ends scene 6 (matched in scene 7)
sub('scenes/s6.js', """        { src: DUSK, at: V(30), grade: DUSK === MON ? LATE : '', cam: hold(960, 610, 1.08) },""",
"""        { src: DUSK, at: V(30), grade: DUSK === MON ? LATE : '', cam: pan(V(30) + .3, M('code') - V(30) - .8, 880, 610, 1040, 600, 1.1) },""")
sub('scenes/s6.js', """          state: t => ({ preset: 'shop-jobs-after', reassign: +clamp((t - M('reassign') - .25) / 1.3).toFixed(3), secs: 5 + Math.floor(t - M('reassign')) }) },
      ], E);""", """          state: t => ({ preset: 'shop-jobs-after', reassign: +clamp((t - M('reassign') - .25) / 1.3).toFixed(3), secs: 5 + Math.floor(t - M('reassign')) }) },
      ].concat(CHAIR ? [{ src: CHAIR, at: Math.max(M('reassign') + 3.0, E - 1.6), cam: hold(960, 540, 1.0) }] : []), E);""")
sub('scenes/s6.js', """      const cb = sfxT('mouse_click', M('click_build')), cardAt = V(33);""",
"""      const cb = sfxT('mouse_click', M('click_build')), cardAt = V(33), CHAIR = pick('world/x_chair_dusk.png', '');""")

# ---- 7.1 the Tuesday desk: the chair in morning sun first (matched on the dusk chair), then a slow pan across the desk
sub('scenes/s7.js', """        { src: 'world/05_medium_tuesday.png', at: S, cam: hold(960, 600, 1.12) },""",
"""        ...(CHAIR_T ? [{ src: CHAIR_T, at: S, cam: hold(960, 540, 1.0) }] : []),
        { src: 'world/05_medium_tuesday.png', at: CHAIR_T ? S + 1.8 : S, cam: pan((CHAIR_T ? S + 1.8 : S) + .3, M('priya_world') - (CHAIR_T ? S + 1.8 : S) - .6, 1060, 600, 900, 600, 1.12) },""")
sub('scenes/s7.js', """      run = seq(root, [""", """      const CHAIR_T = pick('world/x_chair_tuesday.png', '');
      run = seq(root, [""")

# ---- Tuesday -> Lisbon: the desk-to-desk match; then Lisbon's wide (Blender's approach, or a pan on the 4K plate)
sub('scenes/s8.js', """        { src: 'world/lisbon_01_wide_day.png', at: S, cam: move(S + .4, M('nata') - S - .6, [970, 540, 1.0], [1000, 560, 1.12], 0) },""",
"""        ...(MATCH ? [{ src: MATCH, at: S, cam: hold(960, 600, 1.12) }] : []),
        LW4K ? { src: LW4K, at: MATCH ? S + 1.6 : S, cam: pan((MATCH ? S + 1.6 : S) + .2, M('nata') - (MATCH ? S + 1.6 : S) - .5, 760, 520, 1160, 560, 1.2) }
          : { src: 'world/lisbon_01_wide_day.png', at: MATCH ? S + 1.6 : S, cam: move((MATCH ? S + 1.6 : S) + .4, M('nata') - (MATCH ? S + 1.6 : S) - .6, [970, 540, 1.0], [1000, 560, 1.12], 0) },""")
sub('scenes/s8.js', """      run = seq(root, [""", """      const MATCH = pick('world/lisbon_match_day.png', ''), LW4K = pick('world/lisbon_01_wide_day_4k.png', '');
      run = seq(root, [""")
print('rooms patched')
