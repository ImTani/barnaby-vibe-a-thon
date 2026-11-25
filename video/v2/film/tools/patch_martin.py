"""Film state keys for Martin's floor plan (worlds2 lib/martin.js), added minimally; every new option defaults to the
approved drawing. Run once from the repo root: python video/v2/film/tools/patch_martin.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('lib/martin.js', """     labelSize, pipR, route: [[x,y]...], stops: [[x,y,label,dx,dy]...], marker: [x,y], keyAsk: [x,y], passage: bool,
     newSticker: [mx,my,rot,w,h], pads: [mx,my,rot,w] } */""", """     labelSize, pipR, route: [[x,y]...], stops: [[x,y,label,dx,dy]...], marker: [x,y], keyAsk: [x,y], passage: bool,
     newSticker: [mx,my,rot,w,h], pads: [mx,my,rot,w] }
     film state (each optional, default = the approved drawing): passageK (0..1 the band drawn so far, its label at 1),
     stickerK (0..1 the NEW sticker slapped on), keyK (0..1 the key disc popping in), keyRot (deg, the key turning),
     routeOpacity */""")
# the passage drawn progressively
sub('lib/martin.js', """    if (o.passage) {
      const path = o.passagePath || B.passage.path.slice(0, 3);
      const d = path.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');""",
"""    if (o.passage && !(o.passageK <= 0)) {
      const path = cut(o.passagePath || B.passage.path.slice(0, 3), o.passageK);
      const d = path.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');""")
sub('lib/martin.js', """      if (o.passageLabel) pill(pg, ...T(o.passageLabel[0], o.passageLabel[1]), 'Hand back a bike', { fs: o.passageLabelSize || 20 });""",
"""      if (o.passageLabel && !(o.passageK < 1)) pill(pg, ...T(o.passageLabel[0], o.passageLabel[1]), 'Hand back a bike', { fs: o.passageLabelSize || 20 });""")
sub('lib/martin.js', """    if (o.route) {
      const d = o.route.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');
      el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': 10, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: .85 }, g);
      el('path', { d, fill: 'none', stroke: INK, 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-dasharray': '0.1 11' }, g);
      for (const sp of o.stops || []) {
        const p = T(sp[0], sp[1]);
        el('circle', { cx: p[0], cy: p[1], r: 8, fill: '#fff', stroke: INK, 'stroke-width': 3.5 }, g);
        if (sp[2]) pill(g, p[0] + (sp[3] || 16), p[1] + (sp[4] || 0), sp[2], { fs: 18 });
      }
    }""", """    if (o.route && o.route.length > 1) {
      const rg = o.routeOpacity != null && o.routeOpacity < 1 ? el('g', { opacity: o.routeOpacity }, g) : g;
      const d = o.route.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');
      el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': 10, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: .85 }, rg);
      el('path', { d, fill: 'none', stroke: INK, 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-dasharray': '0.1 11' }, rg);
      for (const sp of o.stops || []) {
        const p = T(sp[0], sp[1]);
        el('circle', { cx: p[0], cy: p[1], r: 8, fill: '#fff', stroke: INK, 'stroke-width': 3.5 }, rg);
        if (sp[2]) pill(rg, p[0] + (sp[3] || 16), p[1] + (sp[4] || 0), sp[2], { fs: 18 });
      }
    }""")
sub('lib/martin.js', """    if (o.keyAsk) {
      const p = T(o.keyAsk[0], o.keyAsk[1]), r = o.keyR || 38;
      el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.2)' }, g);
      el('circle', { cx: p[0], cy: p[1], r, fill: '#fff', stroke: INK, 'stroke-width': 4 }, g);
      key(g, p[0], p[1], r * 1.34, GOLD);
    }""", """    if (o.keyAsk && !(o.keyK <= 0)) {
      const p = T(o.keyAsk[0], o.keyAsk[1]), r = o.keyR || 38;
      const kg = o.keyK != null && o.keyK < 1 ? el('g', { transform: `translate(${p[0]},${p[1]}) scale(${o.keyK}) translate(${-p[0]},${-p[1]})` }, g) : g;
      el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.2)' }, kg);
      el('circle', { cx: p[0], cy: p[1], r, fill: '#fff', stroke: INK, 'stroke-width': 4 }, kg);
      key(kg, p[0], p[1], r * 1.34, GOLD, o.keyRot || 0);
    }""")
sub('lib/martin.js', """    if (o.newSticker) {
      const q = o.newSticker, p = T(q[0], q[1]), R = W.ROOMS.find(r => r.id === 'reports');
      const sg = el('g', { transform: `translate(${p[0]},${p[1]}) rotate(${q[2] || -8})` }, g);""",
"""    if (o.newSticker && !(o.stickerK <= 0)) {
      const q = o.newSticker, p = T(q[0], q[1]), R = W.ROOMS.find(r => r.id === 'reports'), sk = o.stickerK == null ? 1 : o.stickerK;
      const sg = el('g', { transform: `translate(${p[0]},${p[1]}) rotate(${q[2] || -8})` + (sk < 1 || sk > 1 ? ` scale(${sk})` : '') }, g);""")
# helper: a polyline cut at a fraction of its length
sub('lib/martin.js', """  function mapper(o) {""", """  // film: the first k (0..1) of a polyline, by length
  function cut(path, k) {
    if (k == null || k >= 1) return path;
    const seg = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
    let d = Math.max(0, k) * seg.reduce((a, b) => a + b, 0); const out = [path[0]];
    for (let i = 0; i < seg.length; i++) {
      if (d >= seg[i]) { out.push(path[i + 1]); d -= seg[i]; continue; }
      const u = seg[i] ? d / seg[i] : 0; out.push([path[i][0] + (path[i + 1][0] - path[i][0]) * u, path[i][1] + (path[i + 1][1] - path[i][1]) * u]); break;
    }
    return out;
  }

  function mapper(o) {""")
sub('lib/martin.js', """  window.MARTIN = { plan, legend, pill, INK, PAPER, GOLD, GOLD_LT };""",
"""  window.MARTIN = { plan, legend, pill, cut, INK, PAPER, GOLD, GOLD_LT };""")
print('patched martin.js')

