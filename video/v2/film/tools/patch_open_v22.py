"""Screen -> world (SHOTLIST section 1): Barnaby's own window opens out of the screen, his bell mark leading. A shot
item with `open: {x, y, d}` is revealed by a circle growing from (x, y) (screen px) over d s, his mark at its heart
fading as it opens; the shot before stays up underneath until it has. Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """    it.end = it.until != null ? it.until : nx ? nx.at + Math.max(nx.fi || 0, nx.quad ? nx.pin.d || .6 : 0) : end;""",
"""    it.end = it.until != null ? it.until : nx ? nx.at + Math.max(nx.fi || 0, nx.quad ? nx.pin.d || .6 : 0, nx.open ? nx.open.d || .55 : 0) : end;""")
sub('shots.js', """    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);""",
"""    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);
    if (it.open) {                                     // his mark, at the heart of the opening
      it.openMark = el('div', { html: markSVG('#D3A14A') }, it.s.box);
      css(it.openMark, { position: 'absolute', width: '132px', height: '132px', left: (it.open.x - 66) + 'px', top: (it.open.y - 74) + 'px', zIndex: 60, pointerEvents: 'none',
        filter: 'drop-shadow(0 0 18px rgba(211,161,74,.55))' });
    }""")
sub('shots.js', """        if (it.finish) it.finish(t);""", """        if (it.finish) it.finish(t);
        if (it.open) {                                   // Barnaby's window opening out of the screen
          const d = it.open.d || .55, u = clamp((t - it.at) / d);
          if (u < 1) {
            const R = 2300 * easeInOutCubic(u) + 40 * (1 - u);
            it.s.box.style.clipPath = `circle(${R.toFixed(1)}px at ${it.open.x}px ${it.open.y}px)`;
          } else if (it.s.box.style.clipPath) it.s.box.style.clipPath = '';
          const mk = clamp(1 - (t - it.at) / (d * .9));
          it.openMark.style.display = mk > .01 ? 'block' : 'none';
          it.openMark.style.opacity = mk.toFixed(3);
          it.openMark.style.transform = `scale(${(1 + .35 * (1 - mk)).toFixed(3)})`;
        }""")

# where the screen gives way to his world
sub('scenes/s2.js', """        { src: 'comp/theo-handover-1-reading', at: M('reading'), cam: [960, 540, 1],""",
"""        { src: 'comp/theo-handover-1-reading', at: M('reading'), cam: [960, 540, 1], open: { x: 1542, y: 520, d: .6 },""")
sub('scenes/s3.js', """        { src: 'comp/martin-key', at: M('martin_world'),""",
"""        { src: 'comp/martin-key', at: M('martin_world'), open: { x: 1542, y: 520, d: .6 },""")
sub('scenes/s6.js', """        { src: 'comp/martin-build', at: M('new_room'), cam:""",
"""        { src: 'comp/martin-build', at: M('new_room'), open: { x: 1542, y: 520, d: .55 }, cam:""")
sub('scenes/s8.js', """        { src: TL, at: M('theo_world'), cam: [960, 540, 1],""",
"""        { src: TL, at: M('theo_world'), cam: [960, 540, 1], open: { x: 1650, y: 540, d: .6 },""")
print('open patched')
