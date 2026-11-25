"""Film state keys for Martin's floor plan (worlds2 lib/martin.js), added minimally; every new option defaults to the
approved drawing. (Second pass.) Run once from the repo root: python video/v2/film/tools/patch_martin.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

# (second pass) Barnaby's marker on its own (drawn over a crossfade of two plans)
s = (C / 'lib/martin.js').read_text(encoding='utf-8')
if 'function marker(' not in s:
    sub('lib/martin.js', """    // Barnaby: an ink disc with his bell, where he is
    if (o.marker) {
      const p = T(o.marker[0], o.marker[1]), r = o.markerR || 30;""", """    // Barnaby: an ink disc with his bell, where he is
    if (o.marker) marker(g, T, o);""")
    sub('lib/martin.js', """      if (o.markerLabel) text(g, p[0] + (o.markerLabel[1] || 0), p[1] + r + (o.markerLabel[2] || 26), o.markerLabel[0], { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': o.markerLabelSize || 20, 'font-weight': 700, fill: o.markerLabelFill || '#fff' });
    }
""", """""")
    sub('lib/martin.js', """    el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.22)' }, g);
      el('circle', { cx: p[0], cy: p[1], r, fill: INK, stroke: '#fff', 'stroke-width': 4 }, g);
      bell(g, p[0], p[1] + 1, r * 1.2, GOLD_LT);
""", """""")
    sub('lib/martin.js', """  function plan(svg, o) {
    const T = mapper(o), s = o.s, g = el('g', {}, svg);""", """  function marker(g, T, o) {
    const p = T(o.marker[0], o.marker[1]), r = o.markerR || 30;
    el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.22)' }, g);
    el('circle', { cx: p[0], cy: p[1], r, fill: INK, stroke: '#fff', 'stroke-width': 4 }, g);
    bell(g, p[0], p[1] + 1, r * 1.2, GOLD_LT);
    if (o.markerLabel) text(g, p[0] + (o.markerLabel[1] || 0), p[1] + r + (o.markerLabel[2] || 26), o.markerLabel[0], { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': o.markerLabelSize || 20, 'font-weight': 700, fill: o.markerLabelFill || '#fff' });
  }

  function plan(svg, o) {
    if (o.onlyMarker) { const T = mapper(o), g = el('g', {}, svg); marker(g, T, o); return { T, g }; }   // film: the marker alone
    const T = mapper(o), s = o.s, g = el('g', {}, svg);""")
    print('marker extracted')
