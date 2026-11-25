/* THE MULTIPLANE STAND (Theo, pick). Barnaby takes in the system as painted glass planes under a rostrum camera:
   background = the building painted in gouache; plane 2 = the endpoints he would ask a key for, inked but unpainted;
   plane 1 = the ones he may use, painted; the one kept shut on a frosted patch. The camera looks down through all.
   MULTI.draw(svg, { moment, P, z: [bg, p2, p1], labels: true }) */
(function () {
  const T = window.THEO, W = window.WORLDS, B = W.building;
  const { el, text } = T;
  const CEL = { shop: '#D2553C', office: '#3F78B5', reports: '#3F78B5', workshop: '#4E8A56', stockroom: '#D9A23A', goodsin: '#8058A8' };
  const GROUP_ROOM = { counter: 'shop', till: 'shop', workshop: 'workshop', stockroom: 'stockroom', backdoor: 'goodsin', office: 'office' };
  const INK = '#1B120C', GLASS = '#E9F0EA', CREAM = '#F4EBD8', UMBER = '#140D09';
  const PL = [-2, -2.2, 24, 13.4];   // plate in plan metres: x, y, w, h

  function defs(svg) {
    const d = el('defs', {}, svg);
    const fr = el('filter', { id: 'frost', x: 0, y: 0, width: '100%', height: '100%' }, d);
    el('feTurbulence', { type: 'fractalNoise', baseFrequency: 2.4, numOctaves: 2, seed: 3, result: 'n' }, fr);
    el('feColorMatrix', { in: 'n', type: 'matrix', values: '0 0 0 0 0.95  0 0 0 0 0.97  0 0 0 0 0.96  0 0 0 0.55 0' }, fr);
    const key = el('radialGradient', { id: 'keylight', cx: .28, cy: .2, r: .8 }, d);
    el('stop', { offset: 0, 'stop-color': '#F6D9A8', 'stop-opacity': .20 }, key);
    el('stop', { offset: .6, 'stop-color': '#B07A3A', 'stop-opacity': .05 }, key);
    el('stop', { offset: 1, 'stop-color': '#000', 'stop-opacity': 0 }, key);
    return d;
  }

  function plate(svg, P, z, opt) {
    const [x, y, w, h] = PL, g = el('g', {}, svg);
    const pts = [[x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z]];
    el('polygon', { points: P.pts(pts), fill: GLASS, 'fill-opacity': opt.tint || .035, stroke: 'none' }, g);
    // edges: the front edge catches the key light, the back edge stays dim; plate thickness as a second line
    const q = pts.map(p => P(...p)), q2 = pts.map(p => P(p[0], p[1], z - .16));
    el('polyline', { points: [q[3], q[2], q[1]].map(p => p.join(',')).join(' '), fill: 'none', stroke: CREAM, 'stroke-width': 1.6, 'stroke-opacity': .85 }, g);
    el('polyline', { points: [q2[3], q2[2], q2[1]].map(p => p.join(',')).join(' '), fill: 'none', stroke: CREAM, 'stroke-width': 1, 'stroke-opacity': .35 }, g);
    el('polyline', { points: [q[3], q[0], q[1]].map(p => p.join(',')).join(' '), fill: 'none', stroke: CREAM, 'stroke-width': .8, 'stroke-opacity': .3 }, g);
    // peg bar along the front edge: three pegs (the registration every cel shares)
    const pb = el('g', { transform: P.matrix(z) }, g);
    el('rect', { x: 8.5, y: y + h - .75, width: 7, height: .45, fill: '#2B2420', stroke: '#6E6258', 'stroke-width': .04 }, pb);
    [9.4, 12, 14.6].forEach(px => el('rect', { x: px - .28, y: y + h - .66, width: .56, height: .27, rx: .1, fill: '#EDE6D8' }, pb));
    return g;
  }

  function bg(svg, P, z, moment) {
    const built = moment === 'build' || moment === 'priyaTuesday';
    const g = el('g', { transform: P.matrix(z) }, svg);
    // painted floors, one gouache wash per room
    for (const [id, r] of Object.entries(B.rooms)) {
      if (id === 'reports' && !built) continue;
      el('polygon', { points: r.poly.map(p => p.join(',')).join(' '), fill: CEL[id], 'fill-opacity': id === 'reports' ? .95 : .78 }, g);
    }
    // fixtures painted a shade darker
    for (const f of B.fixtures) if (f.rect && !f.outside) el('rect', { x: f.rect[0], y: f.rect[1], width: f.rect[2], height: f.rect[3], fill: INK, 'fill-opacity': .28 }, g);
    for (const f of B.fixtures) if (f.stand) el('ellipse', { cx: f.stand[0], cy: f.stand[1], rx: .9, ry: .14, fill: INK, 'fill-opacity': .35 }, g);
    // walls in thick umber, the planned room in pencil until it is built
    const { walls } = T.wallPieces(built);
    for (const p of walls) el('line', { x1: p.a[0], y1: p.a[1], x2: p.b[0], y2: p.b[1], stroke: p.planned && !built ? '#B8AE9C' : INK,
      'stroke-width': p.planned && !built ? .06 : (p.ext ? .32 : .2), 'stroke-dasharray': p.planned && !built ? '.25 .2' : null, 'stroke-linecap': 'square' }, g);
    if (!built) { el('text', { x: 11.1, y: 1.35, 'font-family': 'Cascadia Code', 'font-size': .46, fill: '#C9BFAE', 'text-anchor': 'middle' }, g).textContent = 'reports';
      el('text', { x: 11.1, y: 2.05, 'font-family': 'Cascadia Code', 'font-size': .46, fill: '#C9BFAE', 'text-anchor': 'middle' }, g).textContent = '2011'; }
    return g;
  }

  /* cels are laid out on a neat grid inside their room (the animator's layout), not at raw anchors */
  const REGION = { counter: [0.3, 0.6, 3.8, 4.9, 2], till: [4.5, 0.8, 1.8, 3.2, 1], office: [6.9, 0.6, 2.6, 2.6, 1],
    workshop: [7.0, 4.3, 7.6, 4.2, 4], stockroom: [15.5, 1.1, 4.0, 3.2, 2], backdoor: [15.5, 5.7, 4.0, 2.8, 2] };
  function layout(st) {
    const by = {}; st.forEach(a => (by[a.group] = by[a.group] || []).push(a));
    const out = {};
    for (const [gid, items] of Object.entries(by)) {
      const [x, y, w, h, cols] = REGION[gid], list = items.filter(a => a.tool !== 'workload'), rows = Math.ceil(list.length / cols);
      list.forEach((a, i) => { const c = i % cols, r = Math.floor(i / cols);
        out[a.tool] = [x + (c + .5) * w / cols, y + (r + .5) * h / Math.max(rows, 1)]; });
    }
    out.workload = [11.1, 1.4];
    return out;
  }
  /* a cel plaque: painted (open), inked only (key), frosted and struck (shut) */
  function plaque(g, a, kind, at) {
    const [x, y] = at || a.anchor, w = 1.5, h = .95, col = CEL[GROUP_ROOM[a.group]];
    if (kind === 'painted') {
      el('rect', { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: .16, fill: col, stroke: INK, 'stroke-width': .07 }, g);
      el('rect', { x: x - w / 2 + .14, y: y - h / 2 + .12, width: w - .28, height: .16, rx: .06, fill: CREAM, 'fill-opacity': .6 }, g);
    } else if (kind === 'inked') {
      // inked, unpainted: the line catches the key light; a faint wash of the room's colour shows where paint would go
      el('rect', { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: .16, fill: col, 'fill-opacity': .10, stroke: CREAM, 'stroke-opacity': .78, 'stroke-width': .055 }, g);
    } else if (kind === 'frosted') {
      el('rect', { x: x - 1.3, y: y - .9, width: 2.6, height: 1.8, rx: .14, fill: '#DDE5E0', 'fill-opacity': .38 }, g);
      el('rect', { x: x - 1.3, y: y - .9, width: 2.6, height: 1.8, rx: .14, filter: 'url(#frost)', opacity: .9 }, g);
      el('rect', { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: .16, fill: 'none', stroke: INK, 'stroke-width': .06 }, g);
      el('line', { x1: x - w / 2, y1: y - h / 2, x2: x + w / 2, y2: y + h / 2, stroke: INK, 'stroke-width': .07 }, g);
      el('line', { x1: x + w / 2, y1: y - h / 2, x2: x - w / 2, y2: y + h / 2, stroke: INK, 'stroke-width': .07 }, g);
    }
  }

  function planes(svg, P, moment, z) {
    const st = W.state(moment), L = layout(st);
    st.forEach(a => { a.at = L[a.tool]; });
    const p2 = el('g', { transform: P.matrix(z[1]) }, svg);
    st.filter(a => a.state === 'key' || a.state === 'planned' || a.state === 'asking').forEach(a => plaque(p2, a, 'inked', a.at));
    st.filter(a => a.state === 'shut').forEach(a => plaque(p2, a, 'frosted', a.at));
    const p1 = el('g', { transform: P.matrix(z[2]) }, svg);
    st.filter(a => a.state === 'lit' || a.state === 'new').forEach(a => plaque(p1, a, 'painted', a.at));
    return st;
  }

  /* upright labels at projected anchors, inked on the cel the endpoint sits on */
  function labels(svg, P, st, z, opt) {
    const g = el('g', { 'font-family': 'Cascadia Code' }, svg);
    for (const a of st) {
      const lit = a.state === 'lit' || a.state === 'new', zz = lit ? z[2] : z[1];
      if (!lit && !opt.keys) continue;
      const at = a.at || a.anchor, p = P(at[0], at[1] + .5, zz), d = (opt.off || {})[a.tool] || [0, 0];
      const t = text(g, p[0] + d[0], p[1] + 15 + d[1], a.tool, { fill: lit ? CREAM : 'rgba(244,235,216,.62)', 'font-size': lit ? 13.5 : 11.5, 'font-weight': lit ? 600 : 400, 'text-anchor': 'middle' });
      if (lit) t.setAttribute('paint-order', 'stroke'), t.setAttribute('stroke', UMBER), t.setAttribute('stroke-width', 3.5);
    }
    return g;
  }

  function stand(svg, P, zTop, front) {
    const [x, y, w, h] = PL, cols = [[x - .5, y - .5], [x + w + .5, y - .5], [x + w + .5, y + h + .5], [x - .5, y + h + .5]];
    const g = el('g', {}, svg);
    cols.forEach((c, i) => {
      if (!!front !== (i >= 2)) return;
      const a = P(c[0], c[1], -1.2), b = P(c[0], c[1], zTop);
      el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: '#2C2017', 'stroke-width': i >= 2 ? 16 : 11, 'stroke-linecap': 'butt' }, g);
      el('line', { x1: a[0] - (i >= 2 ? 6 : 4), y1: a[1], x2: b[0] - (i >= 2 ? 6 : 4), y2: b[1], stroke: '#6B4E36', 'stroke-width': 1.4, 'stroke-opacity': .8 }, g);
    });
    return g;
  }

  window.MULTI = { CEL, GROUP_ROOM, INK, CREAM, UMBER, GLASS, PL, defs, plate, bg, planes, labels, stand, plaque };
})();
