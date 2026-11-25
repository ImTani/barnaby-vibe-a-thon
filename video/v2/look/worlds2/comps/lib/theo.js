/* THEO: the workshop hologram, calm. The shop as a low model of tungsten light, and one thing in focus at a time:
   first the system being read (one scan plane, one label), then what matters (the six endpoints he took, each named
   once, in place). Everything else is quiet: 17 faint outlines and a single count line. Two lights only (amber = Theo
   built it; white = Barnaby may use it), and one accent reserved for the moment's single event (the scan plane, the
   new endpoint). fidelity: 'modest' (the 2009 PC: flat light, no bloom) | 'full' (Lisbon: bloom, depth).
   Reuses ../../worlds/comps/lib/theo-shared.js (projection, walls with openings cut) and the building's 24 abilities. */
(function () {
  const { el, text, bell, FONT } = window.W2;
  const T0 = window.THEO, W = window.WORLDS, B = W.building;
  const C = {
    amber: '#F0A458', amberLine: 'rgba(240,164,88,.62)', amberDim: 'rgba(240,164,88,.30)', amberFaint: 'rgba(240,164,88,.07)',
    white: '#F6F4EE', whiteDim: 'rgba(246,244,238,.66)', accent: '#FF5A3C', ground: '#0A0908', mute: '#8F8576',
  };
  const WALL_H = 1.05, BR = 0.58, BZ = 0.22;

  let uid = 0;
  function defs(svg) {
    const d = svg.querySelector('defs') || el('defs', {}, svg), id = 'h' + (++uid);
    const bloom = el('filter', { id: id + 'bloom', x: '-80%', y: '-80%', width: '260%', height: '260%' }, d);
    el('feGaussianBlur', { stdDeviation: 7 }, bloom);
    const pool = el('radialGradient', { id: id + 'pool' }, d);
    el('stop', { offset: 0, 'stop-color': C.amber, 'stop-opacity': .13 }, pool); el('stop', { offset: 1, 'stop-color': C.amber, 'stop-opacity': 0 }, pool);
    const lamp = el('radialGradient', { id: id + 'lamp', cx: 0, cy: 1, r: 1 }, d);
    el('stop', { offset: 0, 'stop-color': '#E09A4E', 'stop-opacity': .20 }, lamp); el('stop', { offset: .55, 'stop-color': '#A86A2C', 'stop-opacity': .05 }, lamp); el('stop', { offset: 1, 'stop-color': '#000', 'stop-opacity': 0 }, lamp);
    return { bloom: `url(#${id}bloom)`, pool: `url(#${id}pool)`, lamp: `url(#${id}lamp)` };
  }

  function cubeFaces(P, x0, y0, z0, s) {
    const x1 = x0 + s, y1 = y0 + s, z1 = z0 + s;
    const v = { a: [x0, y0, z0], b: [x1, y0, z0], c: [x1, y1, z0], d: [x0, y1, z0], e: [x0, y0, z1], f: [x1, y0, z1], g: [x1, y1, z1], h: [x0, y1, z1] };
    const faces = [{ n: [0, 0, 1], p: 'efgh' }, { n: [0, -1, 0], p: 'abfe' }, { n: [1, 0, 0], p: 'bcgf' }, { n: [0, 1, 0], p: 'cdhg' }, { n: [-1, 0, 0], p: 'daeh' }];
    const edges = ['ab', 'bc', 'cd', 'da', 'ef', 'fg', 'gh', 'he', 'ae', 'bf', 'cg', 'dh'];
    const pt = k => P(...v[k]);
    return { faces: faces.filter(f => P.faceVisible(...f.n)), edges, pt, top: P(x0 + s / 2, y0 + s / 2, z1) };
  }
  function brick(g, P, a, o) {
    const s = o.size || BR, cb = cubeFaces(P, a.anchor[0] - s / 2, a.anchor[1] - s / 2, BZ, s);
    const poly = f => f.p.split('').map(k => cb.pt(k).map(n => n.toFixed(1)).join(',')).join(' ');
    const bg = el('g', {}, g), st = a.state;
    if (st === 'lit' || st === 'new') {
      if (o.bloom) el('circle', { cx: cb.top[0], cy: cb.top[1] + s * o.px * .35, r: s * o.px * .9, fill: st === 'new' ? C.accent : C.white, opacity: st === 'new' ? .55 : .32, filter: o.bloom }, bg);
      cb.faces.forEach(f => el('polygon', { points: poly(f), fill: C.white, 'fill-opacity': f.n[2] ? 1 : (f.n[0] ? .74 : .55), stroke: st === 'new' ? C.accent : C.amber, 'stroke-width': st === 'new' ? 2 : 1.2, 'stroke-linejoin': 'round' }, bg));
    } else if (st === 'key' || st === 'asking' || st === 'shut') {
      const col = o.dimAll ? C.amberDim : C.amberLine;
      cb.edges.forEach(e => { const A = cb.pt(e[0]), Bq = cb.pt(e[1]); el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1], stroke: col, 'stroke-width': 1.1, opacity: o.keyOpacity || .55 }, bg); });
      if (st === 'shut') cb.faces.filter(f => f.n[2]).forEach(f => { const q = f.p.split('').map(cb.pt);
        el('line', { x1: q[0][0], y1: q[0][1], x2: q[2][0], y2: q[2][1], stroke: C.amber, 'stroke-width': 1.4 }, bg);
        el('line', { x1: q[1][0], y1: q[1][1], x2: q[3][0], y2: q[3][1], stroke: C.amber, 'stroke-width': 1.4 }, bg); });
    }
    return cb;
  }

  /* the building: floor plate, low walls with the doors cut, the planned room dashed until it's built */
  function building(g, P, o) {
    const built = !!o.built, px = o.px;
    el('polygon', { points: P.pts([[0, 0], [20, 0], [20, 9], [0, 9]]), fill: C.amberFaint }, g);
    if (o.pool) { const c = P(10, 4.5, 0); el('ellipse', { cx: c[0], cy: c[1] + px * .6, rx: px * 12.5, ry: px * 4.2, fill: o.pool }, g); }
    const { walls } = T0.wallPieces(built);
    const wg = el('g', {}, g);
    for (const p of walls) {
      const planned = p.planned && !built, newWall = p.planned && built;
      const col = newWall ? (o.newWallCol || C.accent) : planned ? C.amberDim : (p.ext ? C.amberLine : 'rgba(240,164,88,.45)');
      const a0 = P(p.a[0], p.a[1], 0), b0 = P(p.b[0], p.b[1], 0), a1 = P(p.a[0], p.a[1], WALL_H), b1 = P(p.b[0], p.b[1], WALL_H);
      if (!planned) el('polygon', { points: [a0, b0, b1, a1].map(q => q.join(',')).join(' '), fill: newWall ? 'rgba(255,90,60,.10)' : 'rgba(240,164,88,.05)' }, wg);
      const dash = planned ? '5 5' : null, sw = p.ext ? 1.5 : 1.1;
      el('line', { x1: a0[0], y1: a0[1], x2: b0[0], y2: b0[1], stroke: col, 'stroke-width': sw, 'stroke-dasharray': dash }, wg);
      el('line', { x1: a1[0], y1: a1[1], x2: b1[0], y2: b1[1], stroke: col, 'stroke-width': sw, 'stroke-dasharray': dash }, wg);
    }
  }

  /* draw the hologram. o: { P (projection), px (px per metre), moment, scanX (reading beat: bricks past it unread),
     fidelity, built, defs } -> { pos: {tool: [x,y] top of brick} } */
  function model(svg, o) {
    const P = o.P, g = el('g', {}, svg), full = o.fidelity === 'full';
    building(g, P, { built: o.built, px: o.px, pool: o.defs.pool, newWallCol: o.newWallCol });
    const st = W.state(o.moment).filter(a => a.state !== 'planned')
      .map(a => o.allFound ? Object.assign({}, a, { state: 'key' }) : a)
      .filter(a => o.scanX == null || a.anchor[0] < o.scanX)
      .sort((a, b) => P.depth(a.anchor[0], a.anchor[1]) - P.depth(b.anchor[0], b.anchor[1]));
    const pos = {};
    const bg = el('g', {}, svg);
    for (const a of st) { const cb = brick(bg, P, a, { px: o.px, bloom: full ? o.defs.bloom : null, dimAll: o.dimKeys, keyOpacity: o.keyOpacity }); pos[a.tool] = cb.top; }
    return { pos, g };
  }

  /* the scan plane, the reading beat's one event: a vertical sheet at x = xs, in the accent */
  function scan(svg, P, xs) {
    const g = el('g', {}, svg), z1 = 2.2;
    el('polygon', { points: P.pts([[xs, -0.6, 0], [xs, 9.6, 0], [xs, 9.6, z1], [xs, -0.6, z1]]), fill: C.accent, 'fill-opacity': .08, stroke: C.accent, 'stroke-width': 1.2, 'stroke-opacity': .7 }, g);
    const a = P(xs, 0, 0), b = P(xs, 9, 0); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.accent, 'stroke-width': 2.4 }, g);
    return P(xs, -0.6, z1);
  }

  /* one callout: a leader from the brick to its label; method dim, path bright */
  function callout(svg, from, to, method, path, o = {}) {
    const g = el('g', {}, svg), fs = o.fs || 17, right = o.align === 'right';
    el('circle', { cx: from[0], cy: from[1], r: 3, fill: o.accent || C.white }, g);
    const elbowX = right ? to[0] + 10 : to[0] - 10;
    el('polyline', { points: `${from[0]},${from[1]} ${elbowX},${to[1] - fs * .35}`, fill: 'none', stroke: o.accent || C.whiteDim, 'stroke-width': 1.1 }, g);
    const anchor = right ? 'end' : 'start';
    const tx = right ? to[0] : to[0];
    if (right) {
      const t2 = text(g, tx, to[1], path, { 'font-family': FONT.mono, 'font-size': fs, fill: o.accent || C.white, 'text-anchor': 'end', 'font-weight': 600 });
      text(g, tx - t2.getComputedTextLength() - 10, to[1], method, { 'font-family': FONT.mono, 'font-size': fs * .8, fill: C.mute, 'text-anchor': 'end' });
    } else {
      const t1 = text(g, tx, to[1], method, { 'font-family': FONT.mono, 'font-size': fs * .8, fill: C.mute });
      text(g, tx + t1.getComputedTextLength() + 10, to[1], path, { 'font-family': FONT.mono, 'font-size': fs, fill: o.accent || C.white, 'font-weight': 600 });
    }
    if (o.note) text(g, right ? tx : tx, to[1] + fs * 1.35, o.note, { 'font-family': FONT.mono, 'font-size': fs * .8, fill: o.noteFill || C.amber, 'text-anchor': anchor, 'font-style': 'italic' });
    return g;
  }

  /* the count line: the three states as marks, once */
  function counts(svg, x, y, items, o = {}) {
    const g = el('g', { 'font-family': FONT.mono, 'font-size': o.fs || 16 }, svg); let cx = x; const sz = (o.fs || 16) * .72;
    for (const [state, label] of items) {
      const cy = y - sz + 1;
      const r = el('rect', { x: cx, y: cy, width: sz, height: sz, fill: state === 'lit' ? C.white : 'none', stroke: state === 'lit' ? C.white : C.amberLine, 'stroke-width': 1.3 }, g);
      if (state === 'shut') { el('line', { x1: cx, y1: cy, x2: cx + sz, y2: cy + sz, stroke: C.amber, 'stroke-width': 1.3 }, g); el('line', { x1: cx + sz, y1: cy, x2: cx, y2: cy + sz, stroke: C.amber, 'stroke-width': 1.3 }, g); }
      if (state === 'new') { r.setAttribute('fill', C.white); r.setAttribute('stroke', C.accent); r.setAttribute('stroke-width', 2); }
      const t = text(g, cx + sz + 9, y, label, { fill: state === 'lit' || state === 'new' ? C.white : C.amberLine });
      cx += sz + 9 + t.getComputedTextLength() + (o.gap || 30);
    }
    return g;
  }

  /* his words, with his bell; light weight, large */
  function says(svg, x, y, lines, o = {}) {
    const g = el('g', {}, svg), fs = o.fs || 44, lh = o.lh || fs * 1.18;
    bell(g, x + fs * .36, y - fs * .36, fs * .72, o.bellFill || C.white);
    lines.forEach((l, i) => text(g, x + fs * 1.0, y + i * lh, l, { 'font-family': FONT.theo, 'font-size': fs, 'font-weight': 300, fill: C.white }));
    return g;
  }
  function heard(svg, x, y, who, line, o = {}) {
    const g = el('g', {}, svg), fs = o.fs || 19;
    const t = text(g, x, y, who, { 'font-family': FONT.theo, 'font-size': fs * .82, 'font-weight': 700, fill: C.amber, 'letter-spacing': '0.14em' });
    (Array.isArray(line) ? line : [line]).forEach((l, i) => text(g, x + (o.indent != null ? o.indent : t.getComputedTextLength() + 16), y + i * fs * 1.35, l, { 'font-family': FONT.theo, 'font-size': fs, fill: 'rgba(240,164,88,.86)' }));
    return g;
  }

  window.HOLO2 = { C, defs, model, scan, callout, counts, says, heard, brick, WALL_H };
})();
