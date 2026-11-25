"""Wire Blender's late v2.3 sequences: x_mug_night_off (the lamp-off baked on the mug), x_mug_dawn (the match at
dawn, replacing x_mug_night's frame in scene 3), s9_lisbon_night (the dim baked), s9_two_desks (the matched push);
x_key_rack stays unused (the coordinator). Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """    if (s.kind === 'still' || (s.start == null && !s.events)) continue;            // stills swap in by file (pick)""",
"""    if (s.kind === 'still' || (s.start == null && !s.events)) continue;            // stills swap in by file (pick)
    if (UNUSED.includes(s.id)) continue;                                           // left out by the director's call""")
sub('shots.js', """function blenderFor(key, a, b, scene) {""", """const UNUSED = ['x_key_rack'];                   // the key has its moment already (the drop, the mug, the lamp)
function blenderFor(key, a, b, scene) {""")

# 2.9: the mug insert: Blender's x_mug_night_off bakes the lamp-off; the still keeps the film's grade
sub('scenes/s2.js', """      ].concat(MUG ? [{ src: MUG, at: M('lamp_off') - 1.4, cam: hold(960, 540, 1.0), keepGrade: true,""",
"""      ].concat(MUG ? [{ src: MUG, at: M('lamp_off') - 1.4, cam: hold(960, 540, 1.0),""")
sub('scenes/s2.js', """      const MUG = pick('world/x_mug_night.png', '');""",
"""      const MUG = pick('world/x_mug_night.png', '') || (shotDone('x_mug_night_off') ? 'world/x_mug_night.png' : '');""")
# 3.1: the dawn match: Blender's x_mug_dawn (it replaces x_mug_night's frame), or a still x_mug_dawn.png, or the time-lapse
sub('scenes/s3.js', """      const DAWN = pick('world/x_mug_dawn.png', '');            // the match cut on the mug (with the night one)""",
"""      const DAWN_SEQ = shotDone('x_mug_dawn'), DAWN = DAWN_SEQ ? 'world/x_mug_night.png' : pick('world/x_mug_dawn.png', '');   // the match on the mug""")
sub('scenes/s3.js', """        { src: DAWN, at: S, cam: hold(960, 540, 1.0), keepGrade: true, grade: t => `brightness(${lerp(.05, 1, easeInOutSine(P(t, S + .5, M('monday') - S - .8))).toFixed(3)})` },""",
"""        { src: DAWN, at: S, cam: hold(960, 540, 1.0), grade: DAWN_SEQ ? '' : t => `brightness(${lerp(.05, 1, easeInOutSine(P(t, S + .5, M('monday') - S - .8))).toFixed(3)})` },""")
# 9.2: with s9_lisbon_night the dim is in the sequence: no asleep still, no dimmer
sub('scenes/s9.js', """      ].concat(ASLEEP ? [{ src: ASLEEP, at: M('dim'), fi: 1.6, cam: hold(1010, 525, 1.06) }] : []).concat([""",
"""      ].concat(ASLEEP && !LNIGHT ? [{ src: ASLEEP, at: M('dim'), fi: 1.6, cam: hold(1010, 525, 1.06) }] : []).concat([""")
sub('scenes/s9.js', """          over: t => { dimmer.style.opacity = ASLEEP ? '0' : easeInOutSine(P(t, M('dim'), 1.6)).toFixed(3); } },""",
"""          over: t => { dimmer.style.opacity = ASLEEP || LNIGHT ? '0' : easeInOutSine(P(t, M('dim'), 1.6)).toFixed(3); } },""")
sub('scenes/s9.js', """      const ASLEEP = pick(""", """      const LNIGHT = shotDone('s9_lisbon_night');
      const ASLEEP = pick(""")
print('sequences wired')
