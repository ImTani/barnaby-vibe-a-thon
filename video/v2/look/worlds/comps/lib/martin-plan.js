/* Shared plan geometry for Martin's worlds: every card draws the same building (data/building.js) in its own medium.
   Gives a transform (landscape: street on the left; portrait: street at the bottom), wall footprints cut by their
   openings, door swings, fixtures, the route, and small SVG helpers. Units in: metres. Out: screen px. */
window.MPLAN = (function () {
  const B = WORLDS.building;
  const NS = 'http://www.w3.org/2000/svg';

  /** transform. land: x right (street left), y down (north wall up). port: street at the bottom, north wall on the left. */
  function tf(o) {
    const { orient = 'land', s, ox, oy } = o;
    const f = orient === 'land' ? (x, y) => [ox + x * s, oy + y * s] : (x, y) => [ox + y * s, oy + (B.size.w - x) * s];
    f.s = s; f.orient = orient;
    /** a metre rect -> screen rect {x,y,w,h} */
    f.rect = (x0, y0, x1, y1) => { const a = f(x0, y0), b = f(x1, y1); return { x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), w: Math.abs(b[0] - a[0]), h: Math.abs(b[1] - a[1]) }; };
    return f;
  }

  const wallId = seg => seg[0] === seg[2] ? 'x' + seg[0] : 'y' + seg[1];
  const T_EXT = 0.32, T_INT = 0.16;

  /** Wall footprints (axis-aligned metre rects) after cutting openings. kind: wall | sill (window, low) */
  function wallPieces(opts = {}) {
    const built = !!opts.built;   // Reports room built (Workload)
    const out = [];
    for (const w of B.walls) {
      if (w.planned && !built) continue;
      const seg = w.seg, id = wallId(seg), vert = seg[0] === seg[2];
      const t = w.ext ? T_EXT : T_INT;
      const a0 = vert ? Math.min(seg[1], seg[3]) : Math.min(seg[0], seg[2]);
      const a1 = vert ? Math.max(seg[1], seg[3]) : Math.max(seg[0], seg[2]);
      const c = vert ? seg[0] : seg[1];
      const cuts = B.openings.filter(o => o.wall === id && o.from >= a0 - 1e-6 && o.to <= a1 + 1e-6)
        .filter(o => !(o.planned && !built)).sort((p, q) => p.from - q.from);
      let cur = a0 - t / 2;
      const push = (p, q, kind, o) => {
        if (q - p < 1e-3) return;
        const r = vert ? [c - t / 2, p, c + t / 2, q] : [p, c - t / 2, q, c + t / 2];
        out.push({ r, ext: !!w.ext, planned: !!w.planned, kind, opening: o, vert });
      };
      for (const o of cuts) {
        push(cur, o.from, 'wall');
        if (o.kind === 'window') push(o.from, o.to, 'sill', o);
        cur = o.to;
      }
      push(cur, a1 + t / 2, 'wall');
    }
    return out;
  }

  /** Planned (unbuilt) walls as centre lines, for dashed drawing */
  function plannedLines() { return B.walls.filter(w => w.planned).map(w => w.seg); }

  /** Doors: leaves and swing arcs in metres. Each: {o, hinge:[x,y], leaf:[x,y], arcEnd:[x,y], r, planned} */
  function doors(opts = {}) {
    const built = !!opts.built, res = [];
    for (const o of B.openings) {
      if (!(o.kind === 'door' || o.kind === 'double')) continue;
      if (o.planned && built) { /* built: real door */ }
      const vert = o.wall[0] === 'x', c = parseFloat(o.wall.slice(1));
      const sgn = o.swing === '-' ? -1 : 1;
      const P = (along, across) => vert ? [c + across, along] : [along, c + across];
      const leaves = o.kind === 'double' ? [[o.from, (o.from + o.to) / 2, 1], [o.to, (o.from + o.to) / 2, -1]] : [[o.from, o.to, 1]];
      for (const [h, e, dir] of leaves) {
        const r = Math.abs(e - h);
        res.push({ o, hinge: P(h, 0), leaf: P(h, sgn * r), arcEnd: P(e, 0), r, planned: !!o.planned && !built });
      }
    }
    return res;
  }
  function windows() { return B.openings.filter(o => o.kind === 'window'); }
  function fixture(id) { return B.fixtures.find(f => f.id === id); }
  function room(id) { return B.rooms[id]; }

  /** numbered abilities: 1..23 in building order (the built one, workload, is 24) */
  function numbered(momentId) {
    const st = WORLDS.state(momentId); let n = 0;
    return st.map(a => Object.assign(a, { n: a.start === 'built' ? 24 : ++n }));
  }

  /* SVG helpers */
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function svg(container, w, h) {
    const s = el('svg', { width: w, height: h, viewBox: `0 0 ${w} ${h}` });
    container.appendChild(s);
    return s;
  }
  function text(parent, x, y, str, attrs = {}) { const t = el('text', Object.assign({ x, y }, attrs), parent); t.textContent = str; return t; }
  const pts = arr => arr.map(p => p.map(v => v.toFixed(1)).join(',')).join(' ');
  /** swing arc path in screen space from leaf tip to arc end around hinge */
  function arcPath(f, d) {
    const h = f(...d.hinge), a = f(...d.leaf), b = f(...d.arcEnd), r = d.r * f.s;
    // choose sweep so the arc bulges away from the wall
    const cross = (a[0] - h[0]) * (b[1] - h[1]) - (a[1] - h[1]) * (b[0] - h[0]);
    return `M${a[0].toFixed(1)},${a[1].toFixed(1)} A${r.toFixed(1)},${r.toFixed(1)} 0 0 ${cross > 0 ? 1 : 0} ${b[0].toFixed(1)},${b[1].toFixed(1)}`;
  }

  /* Drawn pictograms (24x24 design box, stroke-based), shared vocabulary */
  const ICON = {
    key: 'M7 12 a4 4 0 1 1 0.01 0 M11 12 H21 M18 12 V15.5 M21 12 V15',
    keyBow: [7, 12, 4],
    lock: 'M7 11 V8 a5 5 0 0 1 10 0 V11 M5 11 H19 V20 H5 Z',
  };

  return { B, tf, wallPieces, plannedLines, doors, windows, fixture, room, numbered, el, svg, text, pts, arcPath, ICON, T_EXT, T_INT };
})();
