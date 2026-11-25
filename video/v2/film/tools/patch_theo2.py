"""Film state for the Build in Theo's world (worlds2 theo-scenes.js buildTall, shown in same-butler.html): the change
being written and the checks running. With no state the panel draws exactly the approved frame. Run once from the repo
root: python video/v2/film/tools/patch_theo2.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('lib/theo-scenes.js', """  function buildTall(svg, w, h) {
    const d = H.defs(svg), b = S.build.technical;""", """  /* film state (optional; none = the approved frame): files 0..3 (the change being written: each file's count climbs
     while its code line types), tests 0..22 (the checks running, one mark each, then the tick), added 0|1 (the
     endpoint's "added 16:16 · Martin clicked" note), rediscover 0..1 */
  function buildTall(svg, w, h, fs = {}) {
    const d = H.defs(svg), b = S.build.technical;
    const nf = fs.files == null ? 3 : fs.files, nt = fs.tests == null ? 22 : fs.tests;""")
sub('lib/theo-scenes.js', """    H.callout(svg, p, [40, 452], 'GET', '/api/reports/workload/{day}', { fs: 17, accent: C.accent, note: 'written today · added 16:16 · Martin clicked', noteFill: C.white });""",
"""    H.callout(svg, p, [40, 452], 'GET', '/api/reports/workload/{day}', { fs: 17, accent: C.accent, note: fs.added === 0 ? 'written today · on a copy' : 'written today · added 16:16 · Martin clicked', noteFill: C.white });""")
sub('lib/theo-scenes.js', """    for (const [f, n] of b.files) {
      text(svg, 40, y, f, { 'font-family': FONT.mono, 'font-size': 20, fill: C.white });
      text(svg, w - 40, y, n, { 'font-family': FONT.mono, 'font-size': 20, fill: '#9BD08A', 'text-anchor': 'end' });
      y += 33;
    }
    text(svg, 40, y + 2, `+${b.added} −${b.removed} · on a git worktree · fast-forward after approval`, { 'font-family': FONT.mono, 'font-size': 14, fill: C.mute });""",
"""    const CODE = [b.route, b.fn, 'def test_workload_counts_booked_hours():'];
    b.files.forEach(([f, n], i) => {
      const k = Math.max(0, Math.min(1, nf - i)); if (k <= 0) return;
      text(svg, 40, y, f, { 'font-family': FONT.mono, 'font-size': 20, fill: C.white });
      text(svg, w - 40, y, k < 1 ? '+' + Math.round(+n.slice(1) * k) : n, { 'font-family': FONT.mono, 'font-size': 20, fill: '#9BD08A', 'text-anchor': 'end' });
      y += 33;
    });
    y += 33 * (b.files.length - Math.min(b.files.length, Math.ceil(nf)));
    if (nf >= 3) text(svg, 40, y + 2, `+${b.added} −${b.removed} · on a git worktree · fast-forward after approval`, { 'font-family': FONT.mono, 'font-size': 14, fill: C.mute });
    else if (nf > 0) {                     // the line being written, in the file being written
      const i = Math.floor(nf), k = nf - i, ln = CODE[i];
      text(svg, 40, y + 2, ln.slice(0, Math.round(ln.length * Math.min(1, k * 1.25))) + (Math.floor(k * 14) % 2 ? '▍' : ' '), { 'font-family': FONT.mono, 'font-size': 14, fill: C.amber });
    }""")
sub('lib/theo-scenes.js', """    W2.tick(svg, 60, y - 13, 42, '#9BD08A', 3);
    text(svg, 96, y, '22 passed', { 'font-family': FONT.mono, 'font-size': 38, 'font-weight': 700, fill: C.white });
    text(svg, 96, y + 30, '1 warning · 1.55 s · your 19, and 3 new ones', { 'font-family': FONT.mono, 'font-size': 15, fill: C.whiteDim });""",
"""    if (nt >= 22) {
      W2.tick(svg, 60, y - 13, 42, '#9BD08A', 3);
      text(svg, 96, y, '22 passed', { 'font-family': FONT.mono, 'font-size': 38, 'font-weight': 700, fill: C.white });
      text(svg, 96, y + 30, '1 warning · 1.55 s · your 19, and 3 new ones', { 'font-family': FONT.mono, 'font-size': 15, fill: C.whiteDim });
    } else if (fs.tests != null && nt >= 0) {   // the checks running: one mark per test, green as each passes
      const n = Math.floor(nt);
      text(svg, 96, y, `${n} passed`, { 'font-family': FONT.mono, 'font-size': 38, 'font-weight': 700, fill: n ? C.white : C.mute });
      for (let i = 0; i < 22; i++) el('rect', { x: 96 + i * 19, y: y + 18, width: 13, height: 13, rx: 2, fill: i < n ? '#9BD08A' : 'none', stroke: i < n ? '#9BD08A' : C.amberDim, 'stroke-width': 1.3 }, svg);
    }""")
sub('lib/theo-scenes.js', """    text(svg, 40, y, `$ ${b.rediscover.split(' · ')[0]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.white });
    text(svg, 40, y + 24, `Extracted 24 endpoint(s) · ${b.rediscover.split(' · ')[2]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.amber });""",
"""    if (!(fs.rediscover <= 0)) {
      text(svg, 40, y, `$ ${b.rediscover.split(' · ')[0]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.white });
      if (!(fs.rediscover < 1)) text(svg, 40, y + 24, `Extracted 24 endpoint(s) · ${b.rediscover.split(' · ')[2]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.amber });
    }""")
sub('same-butler.html', """    const tc = document.getElementById('theo'), ts = W2.svg(tc, 640, 1080);
    THEO_SCENES.buildTall(ts, 640, 1080);""", """    const tc = document.getElementById('theo'), ts = W2.svg(tc, 640, 1080);
    THEO_SCENES.buildTall(ts, 640, 1080);
    // film use: COMP.render(state) redraws Theo's panel from its state (buildTall: files, tests, added, rediscover)
    window.COMP = { render(st) { ts.innerHTML = ''; THEO_SCENES.buildTall(ts, 640, 1080, st || {}); } };""")
print('patched buildTall')
