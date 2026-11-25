"""Event anchoring for the Blender sequences: a shot's "events": {"<mark>": <frame>} pin those frames to the cue
sheet's marks; between events the frames stretch or compress linearly; before the first and after the last they
play 1:1 at 24 fps from that event (clamped to the frames there are). Without events, the shot's own `start`
(scene-scoped). The screen quads follow the same frame map. Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """function blenderFor(key, a, b, scene) {""", """/** A sequence's clock: frameAt(t) (1-based, clamped) and the film times of its first and last frames. */
function seqClock(s, fps = FILM_FPS) {
  if (s.__clock) return s.__clock;
  const pts = [];
  for (const k in s.events || {}) if (CUES.marks[k] != null) pts.push([CUES.marks[k], +s.events[k]]);
  pts.sort((p, q) => p[0] - q[0]);
  let frameAt;
  if (!pts.length) frameAt = t => (t - s.start) * fps + 1;
  else frameAt = t => {
    if (t <= pts[0][0]) return pts[0][1] + (t - pts[0][0]) * fps;
    for (let i = 1; i < pts.length; i++) if (t <= pts[i][0]) {
      const [ta, fa] = pts[i - 1], [tb, fb] = pts[i]; return tb > ta ? fa + (fb - fa) * (t - ta) / (tb - ta) : fb;
    }
    const [tl, fl] = pts[pts.length - 1]; return fl + (t - tl) * fps;
  };
  // the film times of frame 1 and the last frame (outside the events the clock runs 1:1)
  const tOf = f => {
    if (!pts.length) return s.start + (f - 1) / fps;
    if (f <= pts[0][1]) return pts[0][0] - (pts[0][1] - f) / fps;
    const l = pts[pts.length - 1]; if (f >= l[1]) return l[0] + (f - l[1]) / fps;
    for (let i = 1; i < pts.length; i++) if (f <= pts[i][1]) { const [ta, fa] = pts[i - 1], [tb, fb] = pts[i]; return fb > fa ? ta + (tb - ta) * (f - fa) / (fb - fa) : tb; }
    return l[0];
  };
  return (s.__clock = { frame: t => clamp(Math.floor(frameAt(t) + 1e-6), 1, s.frames), t0: tOf(1), t1: tOf(s.frames) + 1 / fps, anchored: pts.length > 0 });
}

function blenderFor(key, a, b, scene) {""")
sub('shots.js', """    if (s.kind === 'still' || s.start == null) continue;                           // stills swap in by file (pick)""",
"""    if (s.kind === 'still' || (s.start == null && !s.events)) continue;            // stills swap in by file (pick)""")
sub('shots.js', """    const s0 = s.start, s1 = s.start + s.frames / (m.fps || FILM_FPS);""",
"""    const ck = seqClock(s, m.fps || FILM_FPS), s0 = ck.t0, s1 = ck.t1;""")
sub('shots.js', """          const n = clamp(Math.floor((t - it.bl.start) * FILM_FPS) + 1, 1, it.bl.frames);""",
"""          const n = seqClock(it.bl).frame(t);""")
sub('shots.js', """  const pf = clamp(Math.floor((at - sh.start) * (m.fps || FILM_FPS)) + 1, 1, sh.frames);""",
"""  const pf = seqClock(sh, m.fps || FILM_FPS).frame(at);""")
print('events patched')
