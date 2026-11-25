"""v2.3: an operator's handheld on room shots (SHOTLIST v2.3 revisions 1): over a 4% overscan, low-frequency drift
(about +-0.5% position, +-0.2 deg roll, 2-5 s periods, smooth), deterministic and seeded per shot; screens stay locked,
worlds still. It replaces the old <=1.2% drift (hold() now holds). Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """const hold = (x, y, s = 1, k = .012) => (t, it) => {""", """const hold = (x, y, s = 1, k = 0) => (t, it) => {""")
sub('shots.js', """        if (it.finish) it.finish(t);""", """        if (it.hh) {                                     // the operator's hand, over the placement (frame px)
          const h = it.hh(t), m = `translate(${(W / 2 + h[0]).toFixed(2)}px,${(H / 2 + h[1]).toFixed(2)}px) rotate(${h[2].toFixed(4)}deg) scale(1.04) translate(${-W / 2}px,${-H / 2}px) `;
          it.s.img.style.transform = m + it.s.img.style.transform;
          it.s.layer.style.transform = m + it.s.layer.style.transform;
        }
        if (it.finish) it.finish(t);""")
sub('shots.js', """    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);""",
"""    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);
    if (isRoom(it.src) && !it.tripod) it.hh = handheld(it.src + '@' + it.at.toFixed(2));""")
sub('shots.js', """/* ---- the room finish:""", """/* ---- an operator's handheld (room shots): smooth, low-frequency, seeded per shot -------------------------------- */
function handheld(seedKey) {
  let h = 2166136261; for (const ch of seedKey) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  const r = k => rand(h >>> 0, k);
  // each axis: two sines with periods in 2-5 s and random phases, mixed 0.62 / 0.38 (never jittery)
  const ax = n => { const p1 = 2 + 3 * r(n), p2 = 2 + 3 * r(n + 1), f1 = 6.2832 * r(n + 2), f2 = 6.2832 * r(n + 3);
    return t => .62 * Math.sin(6.2832 * t / p1 + f1) + .38 * Math.sin(6.2832 * t / p2 + f2); };
  const X = ax(10), Y = ax(20), R = ax(30);
  return t => [W * .005 * X(t), H * .005 * Y(t), .2 * R(t)];
}

/* ---- the room finish:""")
print('handheld patched')
