/* THE WORKSHOP HOLOGRAM (Theo, assigned). Barnaby's Jarvis form: the building as a volumetric model of light in the
   rain-dark back office. Two lights only (tungsten amber = Theo built it; bell-white = Barnaby may use it), one
   reserved accent on the scan plane. Every endpoint is the same brick; state by fill alone (solid / outline / struck /
   dashed). States print themselves beside the model; no panels.
   HOLO.draw(container, { moment, w, h, layout: 'hero' | 'panel', scan: x-position or null }) */
(function () {
  const T = window.THEO, W = window.WORLDS, B = W.building, S = W.story;
  const { el, text } = T;
  const C = {
    amber: '#F0A458', amberLine: 'rgba(240,164,88,.78)', amberDim: 'rgba(240,164,88,.34)', amberFaint: 'rgba(240,164,88,.10)',
    white: '#F3F4EF', whiteDim: 'rgba(243,244,239,.72)', accent: '#FF4B36', ground: '#05070A',
  };
  const WALL_H = 2.4, BRICK = 0.5, BZ = 0.5;

  /* seeded random so every render is identical */
  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  /* ---------- the room around it: window, rain, lamp, desk ---------- */
  function room(svg, w, h, o) {
    const defs = el('defs', {}, svg);
    const lg = el('linearGradient', { id: 'glass', x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    el('stop', { offset: 0, 'stop-color': '#0A1017' }, lg); el('stop', { offset: 1, 'stop-color': '#0D141C' }, lg);
    const lamp = el('radialGradient', { id: 'lamp', cx: 0, cy: 1, r: 1 }, defs);
    el('stop', { offset: 0, 'stop-color': '#E8A050', 'stop-opacity': .34 }, lamp);
    el('stop', { offset: .45, 'stop-color': '#C07A30', 'stop-opacity': .10 }, lamp);
    el('stop', { offset: 1, 'stop-color': '#000', 'stop-opacity': 0 }, lamp);
    const pool = el('radialGradient', { id: 'pool' }, defs);
    el('stop', { offset: 0, 'stop-color': C.amber, 'stop-opacity': .16 }, pool);
    el('stop', { offset: 1, 'stop-color': C.amber, 'stop-opacity': 0 }, pool);
    const soft = el('filter', { id: 'soft', x: '-50%', y: '-50%', width: '200%', height: '200%' }, defs);
    el('feGaussianBlur', { stdDeviation: 6 }, soft);
    const smear = el('filter', { id: 'smear', x: '-10%', y: '-10%', width: '120%', height: '120%' }, defs);
    el('feGaussianBlur', { stdDeviation: '1.2 5' }, smear);

    el('rect', { x: 0, y: 0, width: w, height: h, fill: C.ground }, svg);
    const win = o.window; // {x,y,w,h, mullionX, transomY}
    el('rect', { x: win.x, y: win.y, width: win.w, height: win.h, fill: 'url(#glass)' }, svg);
    // the lane beyond: a wall across the way and two sodium lamps, out of focus through wet glass
    const beyond = el('g', { filter: 'url(#soft)', opacity: .9 }, svg);
    for (const L of o.beyondLights) el('circle', { cx: L[0], cy: L[1], r: L[2], fill: L[3], opacity: L[4] }, beyond);
    el('rect', { x: win.x, y: win.y + win.h * .62, width: win.w, height: win.h * .38, fill: '#070A0E', opacity: .85 }, svg);
    return { defs };
  }

  function rain(svg, o, near) {
    const r = rng(o.seed || 7), g = el('g', {}, svg), win = o.window;
    // running trails
    for (let i = 0; i < o.trails; i++) {
      const x = win.x + r() * win.w, y0 = win.y + r() * win.h * .5, len = 60 + r() * 260;
      let d = `M${x.toFixed(1)},${y0.toFixed(1)}`, cx = x;
      for (let y = y0; y < y0 + len; y += 14) { cx += (r() - .5) * 3; d += ` L${cx.toFixed(1)},${(y + 14).toFixed(1)}`; }
      const lit = near(cx, y0 + len / 2);
      el('path', { d, fill: 'none', stroke: lit ? 'rgba(240,164,88,.30)' : 'rgba(170,190,210,.13)', 'stroke-width': 1.3 + r() * 1.2, 'stroke-linecap': 'round' }, g);
      el('circle', { cx: cx, cy: y0 + len, r: 2.6, fill: lit ? 'rgba(240,164,88,.42)' : 'rgba(180,200,220,.22)' }, g);
    }
    // beads on the glass: dark body, one bright catch-light; beads near the model catch its amber
    for (let i = 0; i < o.drops; i++) {
      const x = win.x + r() * win.w, y = win.y + r() * win.h, s = .8 + r() * r() * 3.6;
      const lit = near(x, y);
      el('ellipse', { cx: x, cy: y, rx: s, ry: s * 1.15, fill: lit ? 'rgba(240,164,88,.20)' : 'rgba(150,170,190,.10)' }, g);
      el('circle', { cx: x - s * .3, cy: y - s * .35, r: Math.max(.5, s * .32), fill: lit ? 'rgba(255,214,160,.85)' : 'rgba(210,225,240,.42)' }, g);
    }
  }

  function frameAndDesk(svg, w, h, o) {
    const win = o.window, f = '#101317', fe = 'rgba(240,164,88,.16)';
    // window frame and glazing bars, lit on their lamp-facing edge
    el('rect', { x: win.x - 18, y: win.y - 18, width: win.w + 36, height: win.h + 36, fill: 'none', stroke: f, 'stroke-width': 36 }, svg);
    el('rect', { x: win.mullionX - 9, y: win.y, width: 18, height: win.h, fill: f }, svg);
    el('rect', { x: win.x, y: win.transomY - 8, width: win.w, height: 16, fill: f }, svg);
    el('line', { x1: win.mullionX - 9, y1: win.y, x2: win.mullionX - 9, y2: win.y + win.h, stroke: fe, 'stroke-width': 1 }, svg);
    el('line', { x1: win.x, y1: win.transomY + 8, x2: win.x + win.w, y2: win.transomY + 8, stroke: fe, 'stroke-width': 1 }, svg);
    // sill and wall below the window
    el('rect', { x: 0, y: win.y + win.h + 18, width: w, height: h, fill: '#07090C' }, svg);
    el('rect', { x: win.x - 40, y: win.y + win.h + 14, width: win.w + 80, height: 10, fill: '#13171C' }, svg);
    // desk top
    el('rect', { x: 0, y: o.deskY, width: w, height: h - o.deskY, fill: '#0B0C0D' }, svg);
    el('line', { x1: 0, y1: o.deskY, x2: w, y2: o.deskY, stroke: 'rgba(240,164,88,.22)', 'stroke-width': 1.2 }, svg);
    // lamp light pooling from the left edge, and the model's own light on the desk under it
    el('rect', { x: 0, y: 0, width: w * .55, height: h, fill: 'url(#lamp)' }, svg);
    if (o.pool) el('ellipse', { cx: o.pool[0], cy: o.pool[1], rx: o.pool[2], ry: o.pool[3], fill: 'url(#pool)' }, svg);
    // the lamp: its shade cut by the frame edge, warm rim inside
    if (o.lamp) {
      const L = o.lamp, sh = el('g', {}, svg);
      el('line', { x1: L.x + 40, y1: L.y - 20, x2: L.x + 150, y2: -40, stroke: '#16130F', 'stroke-width': 10, 'stroke-linecap': 'round' }, sh);
      el('path', { d: `M${L.x - 120},${L.y + 120} C${L.x - 110},${L.y - 10} ${L.x + 10},${L.y - 40} ${L.x + 60},${L.y - 20} C${L.x + 120},${L.y + 5} ${L.x + 150},${L.y + 70} ${L.x + 150},${L.y + 120} Z`, fill: '#15120E' }, sh);
      el('path', { d: `M${L.x + 52},${L.y - 18} C${L.x + 110},${L.y + 6} ${L.x + 142},${L.y + 66} ${L.x + 146},${L.y + 112}`, fill: 'none', stroke: 'rgba(243,184,102,.35)', 'stroke-width': 2 }, sh);
      el('ellipse', { cx: L.x + 15, cy: L.y + 121, rx: 136, ry: 11, fill: '#2A1E10' }, sh);
      el('ellipse', { cx: L.x + 15, cy: L.y + 122, rx: 122, ry: 7, fill: '#FFD596', opacity: .9 }, sh);
      el('ellipse', { cx: L.x + 15, cy: L.y + 123, rx: 60, ry: 4, fill: '#FFF3DC' }, sh);
    }
  }

  /* ---------- the model ---------- */
  function cube(P, x0, y0, z0, s, hgt) {
    const x1 = x0 + s, y1 = y0 + s, z1 = z0 + hgt;
    const v = { a: [x0, y0, z0], b: [x1, y0, z0], c: [x1, y1, z0], d: [x0, y1, z0], e: [x0, y0, z1], f: [x1, y0, z1], g: [x1, y1, z1], hh: [x0, y1, z1] };
    const faces = [
      { n: [0, 0, 1], p: ['e', 'f', 'g', 'hh'] }, { n: [0, -1, 0], p: ['a', 'b', 'f', 'e'] }, { n: [1, 0, 0], p: ['b', 'c', 'g', 'f'] },
      { n: [0, 1, 0], p: ['c', 'd', 'hh', 'g'] }, { n: [-1, 0, 0], p: ['d', 'a', 'e', 'hh'] },
    ];
    const edges = [['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'a'], ['e', 'f'], ['f', 'g'], ['g', 'hh'], ['hh', 'e'], ['a', 'e'], ['b', 'f'], ['c', 'g'], ['d', 'hh']];
    return { v, faces, edges, P };
  }
  function drawBrick(g, P, a, opt) {
    const s = BRICK, x0 = a.anchor[0] - s / 2, y0 = a.anchor[1] - s / 2, z0 = opt.z != null ? opt.z : BZ;
    const cb = cube(P, x0, y0, z0, s, s), pt = k => P(...cb.v[k]);
    const poly = ks => ks.map(k => pt(k).map(n => n.toFixed(1)).join(',')).join(' ');
    const st = a.state, bg = el('g', {}, g);
    const vis = cb.faces.filter(f => P.faceVisible(...f.n));
    if (st === 'lit' || st === 'new') {
      // both lights: bell-white body, amber edges
      vis.forEach(f => el('polygon', { points: poly(f.p), fill: C.white, 'fill-opacity': f.n[2] ? .96 : (f.n[0] ? .70 : .52), stroke: C.amber, 'stroke-width': 1.1, 'stroke-linejoin': 'round' }, bg));
    } else {
      // Theo's light only: see-through outline; shut is struck through; planned is dashed
      const dash = st === 'planned' ? '3 3' : null, sw = st === 'planned' ? 1 : 1.15;
      cb.edges.forEach(([p1, p2]) => { const A = pt(p1), Bp = pt(p2);
        el('line', { x1: A[0], y1: A[1], x2: Bp[0], y2: Bp[1], stroke: st === 'planned' ? C.amberDim : C.amberLine, 'stroke-width': sw, 'stroke-dasharray': dash }, bg); });
      if (st === 'shut') vis.forEach(f => { const q = f.p.map(pt);
        el('line', { x1: q[0][0], y1: q[0][1], x2: q[2][0], y2: q[2][1], stroke: C.amber, 'stroke-width': 1.3 }, bg);
        el('line', { x1: q[1][0], y1: q[1][1], x2: q[3][0], y2: q[3][1], stroke: C.amber, 'stroke-width': 1.3 }, bg); });
    }
    return bg;
  }

  function model(svg, P, moment, o) {
    const built = moment === 'build' || moment === 'priyaTuesday';
    const g = el('g', {}, svg);
    const { walls, openings } = T.wallPieces(built);
    // floor plate: the building's footprint, barely lit
    el('polygon', { points: P.pts([[0, 0], [20, 0], [20, 9], [0, 9]]), fill: C.amberFaint, stroke: 'none' }, g);
    // room floors faintly ruled so the rooms read
    const floors = el('g', { transform: P.matrix(0) }, g);
    for (let x = 0.5; x < 20; x += 0.5) el('line', { x1: x, y1: 0, x2: x, y2: 9, stroke: 'rgba(240,164,88,.06)', 'stroke-width': .02 }, floors);
    // fixtures, low and faint (counter, desk, shelves, stands, benches)
    const fx = el('g', {}, g);
    for (const f of B.fixtures) {
      if (f.outside) continue;
      if (f.rect) { const [x, y, ww, hh] = f.rect, z = /shelf/.test(f.id) ? 1.9 : f.id === 'jobboard' || f.id === 'rota' || f.id === 'pegboard' ? 1.7 : 0.9;
        box(fx, P, x, y, ww, hh, z, 'rgba(240,164,88,.30)', .9); }
      if (f.stand) { const [x, y] = f.stand; standBike(fx, P, x, y); }
    }
    // walls: bottom and top lines, posts at the ends of every piece
    const wg = el('g', {}, g);
    for (const p of walls) {
      const ext = p.ext, col = p.planned ? (built ? C.amber : C.amberDim) : (ext ? C.amberLine : 'rgba(240,164,88,.6)');
      const dash = p.planned && !built ? '6 5' : null, H = WALL_H;
      const a0 = P(p.a[0], p.a[1], 0), b0 = P(p.b[0], p.b[1], 0), a1 = P(p.a[0], p.a[1], H), b1 = P(p.b[0], p.b[1], H);
      el('polygon', { points: [a0, b0, b1, a1].map(q => q.join(',')).join(' '), fill: p.planned && !built ? 'none' : (built && p.planned ? 'rgba(243,244,239,.10)' : 'rgba(240,164,88,.045)') }, wg);
      el('line', { x1: a0[0], y1: a0[1], x2: b0[0], y2: b0[1], stroke: col, 'stroke-width': ext ? 1.6 : 1.2, 'stroke-dasharray': dash }, wg);
      el('line', { x1: a1[0], y1: a1[1], x2: b1[0], y2: b1[1], stroke: col, 'stroke-width': ext ? 1.3 : 1, 'stroke-dasharray': dash }, wg);
      el('line', { x1: a0[0], y1: a0[1], x2: a1[0], y2: a1[1], stroke: col, 'stroke-width': .9, 'stroke-dasharray': dash }, wg);
      el('line', { x1: b0[0], y1: b0[1], x2: b1[0], y2: b1[1], stroke: col, 'stroke-width': .9, 'stroke-dasharray': dash }, wg);
    }
    // glazing in the windows: a thin pane line at sill and head
    for (const op of openings) if (op.kind === 'window') {
      [0.9, WALL_H - .3].forEach(z => { const A = P(op.a[0], op.a[1], z), Bq = P(op.b[0], op.b[1], z);
        el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1], stroke: C.amberDim, 'stroke-width': 1 }, wg); });
    }
    // the planned room's door, dashed until built
    // bricks, far to near
    const st = W.state(moment).slice().sort((a, b) => P.depth(a.anchor[0], a.anchor[1]) - P.depth(b.anchor[0], b.anchor[1]));
    const bricks = el('g', {}, g);
    for (const a of st) drawBrick(bricks, P, a, {});
    return g;
  }
  function box(g, P, x, y, w, h, z, col, sw) {
    const top = [[x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z]], bot = top.map(p => [p[0], p[1], 0]);
    el('polygon', { points: P.pts(top), fill: 'none', stroke: col, 'stroke-width': sw }, g);
    for (let i = 0; i < 4; i++) { const A = P(...top[i]), Bq = P(...bot[i]);
      if (P.depth(...bot[i]) > P.depth(x + w / 2, y + h / 2) - .2) el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1], stroke: col, 'stroke-width': sw * .8 }, g); }
  }
  function standBike(g, P, x, y) {
    // a bike in a work stand: two wheels in a vertical plane along x, a post
    const col = 'rgba(240,164,88,.36)';
    for (const dx of [-0.52, 0.52]) {
      const pts = []; for (let i = 0; i <= 28; i++) { const t = i / 28 * Math.PI * 2; pts.push([x + dx + Math.cos(t) * .34, y, 1.05 + Math.sin(t) * .34]); }
      el('polyline', { points: P.pts(pts), fill: 'none', stroke: col, 'stroke-width': .9 }, g);
    }
    el('polyline', { points: P.pts([[x - .52, y, 1.05], [x - .1, y, 1.45], [x + .52, y, 1.05], [x + .05, y, 1.05], [x - .1, y, 1.45]]), fill: 'none', stroke: col, 'stroke-width': .9 }, g);
    el('polyline', { points: P.pts([[x, y, 0], [x, y, 1.45]]), fill: 'none', stroke: col, 'stroke-width': .9 }, g);
  }

  /* the scan plane: the one reserved accent. A vertical sheet at x = xs, its section line cut through the walls. */
  function scan(svg, P, xs) {
    const g = el('g', {}, svg), y0 = -0.7, y1 = 9.7, z1 = 3.3;
    el('polygon', { points: P.pts([[xs, y0, -0.15], [xs, y1, -0.15], [xs, y1, z1], [xs, y0, z1]]), fill: C.accent, 'fill-opacity': .075, stroke: C.accent, 'stroke-width': 1, 'stroke-opacity': .55 }, g);
    const fl = [P(xs, 0, 0), P(xs, 9, 0)];
    el('line', { x1: fl[0][0], y1: fl[0][1], x2: fl[1][0], y2: fl[1][1], stroke: C.accent, 'stroke-width': 2 }, g);
    // where the sheet cuts a wall running along x, the section shows as a short bright upright
    for (const p of T.wallPieces(false).walls) {
      if (p.a[1] !== p.b[1]) continue;
      const lo = Math.min(p.a[0], p.b[0]), hi = Math.max(p.a[0], p.b[0]);
      if (xs > lo && xs < hi) { const A = P(xs, p.a[1], 0), Bq = P(xs, p.a[1], WALL_H);
        el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1], stroke: C.accent, 'stroke-width': 3 }, g); }
    }
    return g;
  }

  /* ---------- states print themselves ---------- */
  function callouts(svg, P, moment, blocks, opt) {
    const groups = T.groups(moment), g = el('g', {}, svg);
    for (const b of blocks) {
      const grp = groups.find(x => x.id === b.group);
      let ax = 0, ay = 0; grp.items.forEach(i => { ax += i.anchor[0]; ay += i.anchor[1]; });
      ax /= grp.items.length; ay /= grp.items.length;
      const tgt = P(b.to ? b.to[0] : ax, b.to ? b.to[1] : ay, WALL_H + .15);
      const lh = opt.lh || 23, fs = opt.fs || 15.5;
      // leader: from the block's anchor corner to the room, with a dot on the room
      const lx = b.side === 'left' ? b.x + (b.w || 330) : b.x, ly = b.y - 6;
      el('polyline', { points: `${lx},${ly} ${b.elbow ? b.elbow + ',' + ly : ''} ${tgt[0].toFixed(1)},${tgt[1].toFixed(1)}`.replace(/\s+/g, ' ').trim(), fill: 'none', stroke: C.amberDim, 'stroke-width': 1 }, g);
      el('circle', { cx: tgt[0], cy: tgt[1], r: 3.2, fill: C.amber }, g);
      text(g, b.x, b.y, grp.name.replace(/^The /, '').toUpperCase(), { fill: C.amber, 'font-family': 'Bahnschrift', 'font-size': fs - 1, 'font-weight': 600, 'letter-spacing': '0.14em', style: "font-variation-settings:'wdth' 85" });
      text(g, b.x + 235 * (opt.hdrK || 1), b.y, `${grp.items.filter(i => i.state === 'lit' || i.state === 'new').length}/${grp.items.filter(i => i.state !== 'planned').length}`, { fill: C.amberDim, 'font-family': 'Cascadia Code', 'font-size': fs - 2.5 });
      grp.items.forEach((it, k) => {
        const y = b.y + 12 + (k + 1) * lh;
        // before the Build there is no route: Theo's 2011 "reports page (coming soon)" is all that exists
        const [m, path] = it.state === 'planned' ? ['', 'reports page: coming soon (since 2011)'] : T.splitKey(it.key);
        const lit = it.state === 'lit' || it.state === 'new';
        T.mark(g, b.x, y - 11.5, 11, it.state, { line: lit ? C.white : C.amberLine, fill: C.white, w: 1.3 });
        text(g, b.x + 22, y, m, { fill: lit ? C.white : C.amberLine, 'font-family': 'Cascadia Code', 'font-size': fs - 2.5, 'font-weight': lit ? 600 : 400 });
        text(g, b.x + 22 + (opt.methodW || 62), y, path, { fill: lit ? C.white : C.amberLine, 'font-family': 'Cascadia Code', 'font-size': fs, 'font-weight': lit ? 600 : 350 });
        if (it.state === 'shut') text(g, b.x + 22 + (opt.methodW || 62) + path.length * fs * .6 + 12, y, 'denied', { fill: C.amber, 'font-family': 'Cascadia Code', 'font-size': fs - 2.5, 'font-style': 'italic' });
        if (it.state === 'new') text(g, b.x + 22 + (opt.methodW || 62) + path.length * fs * .6 + 12, y, 'written today', { fill: C.white, 'font-family': 'Cascadia Code', 'font-size': fs - 2.5, 'font-style': 'italic' });
      });
    }
    return g;
  }

  window.HOLO = { C, room, rain, frameAndDesk, model, scan, callouts, rng, WALL_H };
})();
