/* Shared helpers for Theo's worlds: one orthographic projection of the building (data/building.js), wall pieces with
   openings cut, the endpoint list grouped by room, and small SVG builders. Pure functions of their inputs. */
(function () {
  const W = window.WORLDS, B = W.building;
  const NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function svgRoot(container, w, h) {
    const s = el('svg', { width: w, height: h, viewBox: `0 0 ${w} ${h}` });
    container.appendChild(s);
    return s;
  }
  function text(parent, x, y, str, attrs) {
    const t = el('text', Object.assign({ x, y }, attrs || {}), parent);
    t.textContent = str;
    return t;
  }

  /* Orthographic view of the building. yaw turns the plan, pitch tilts the camera down (radians). Plan point (x, y)
     at height z (metres) -> screen [sx, sy]. P.matrix(z) maps the plan plane at height z onto the screen (affine), so
     text and shapes can be drawn lying on a floor. P.depth(x,y,z) sorts far-to-near. */
  function projection({ cx, cy, s, yaw, pitch, ox = 10, oy = 4.5 }) {
    const cf = Math.cos(yaw), sf = Math.sin(yaw), st = Math.sin(pitch), ct = Math.cos(pitch);
    const P = (x, y, z = 0) => {
      const xc = x - ox, yc = y - oy, u = xc * cf - yc * sf, v = xc * sf + yc * cf;
      return [cx + u * s, cy + (v * st - z * ct) * s];
    };
    P.matrix = z => { const [e, f] = P(0, 0, z); return `matrix(${s * cf},${s * sf * st},${-s * sf},${s * cf * st},${e},${f})`; };
    P.depth = (x, y, z = 0) => { const xc = x - ox, yc = y - oy; return (xc * sf + yc * cf) * ct + z * st; };
    P.faceVisible = (nx, ny, nz) => (nx * sf + ny * cf) * ct + nz * st > 1e-6;
    P.pts = arr => arr.map(p => P(p[0], p[1], p[2] || 0).map(n => n.toFixed(1)).join(',')).join(' ');
    return P;
  }

  /* Walls with door/arch/window openings removed. A planned opening stays closed until the room is built. */
  function wallPieces(built) {
    const out = [], ops = [];
    for (const w of B.walls) {
      const [x1, y1, x2, y2] = w.seg, vertical = x1 === x2, c = vertical ? x1 : y1;
      const lo = vertical ? Math.min(y1, y2) : Math.min(x1, x2), hi = vertical ? Math.max(y1, y2) : Math.max(x1, x2);
      const mine = B.openings.filter(o => o.wall === (vertical ? 'x' : 'y') + c && o.from >= lo - 1e-6 && o.to <= hi + 1e-6
        && !(o.planned && !built)).sort((a, b) => a.from - b.from);
      const push = (a, b) => out.push(vertical ? { a: [c, a], b: [c, b], ext: w.ext, planned: w.planned }
        : { a: [a, c], b: [b, c], ext: w.ext, planned: w.planned });
      let cur = lo;
      for (const o of mine) { if (o.from > cur) push(cur, o.from); cur = o.to; }
      if (cur < hi) push(cur, hi);
    }
    for (const o of B.openings) {
      const c = parseFloat(o.wall.slice(1)), vertical = o.wall[0] === 'x';
      ops.push(Object.assign({}, o, { a: vertical ? [c, o.from] : [o.from, c], b: vertical ? [c, o.to] : [o.to, c] }));
    }
    return { walls: out, openings: ops };
  }

  /* Endpoints grouped by room, in the plan's order (front door to back door). */
  function groups(moment) {
    const st = W.state(moment);
    return B.groups.map(g => Object.assign({}, g, { items: st.filter(a => a.group === g.id) }));
  }
  function splitKey(key) { const i = key.indexOf(' '); return [key.slice(0, i), key.slice(i + 1)]; }
  function centroid(poly) {
    let x = 0, y = 0; poly.forEach(p => { x += p[0]; y += p[1]; }); return [x / poly.length, y / poly.length];
  }

  /* A state mark drawn, not typed: filled square (open), outline (key), outline struck through (shut), dashed (planned). */
  function mark(parent, x, y, size, state, c) {
    const g = el('g', {}, parent);
    const r = el('rect', { x, y, width: size, height: size, fill: 'none', stroke: c.line, 'stroke-width': c.w || 1.4 }, g);
    if (state === 'lit' || state === 'new') r.setAttribute('fill', c.fill);
    if (state === 'planned') r.setAttribute('stroke-dasharray', '2.5 2');
    if (state === 'shut') { el('line', { x1: x, y1: y, x2: x + size, y2: y + size, stroke: c.line, 'stroke-width': c.w || 1.4 }, g);
      el('line', { x1: x + size, y1: y, x2: x, y2: y + size, stroke: c.line, 'stroke-width': c.w || 1.4 }, g); }
    return g;
  }

  /* Diff lines from video/data.js are not loaded in the browser; the panels quote these verbatim from build.diff. */
  const DIFF = {
    route: ['@router.get("/api/reports/workload/{day}")', 'def workload(day: str):', '    if day == "today":', '        day = today()', '    return services.mechanic_workload(day)'],
    service: ['def mechanic_workload(day):', '    week_start, week_end = week_bounds(day)', '    rows = con.execute(', '        """SELECT m.id AS mechanic_id, m.name, m.weekly_capacity_hours,', '                  coalesce(sum(j.estimate_hours), 0) AS workload_hours, count(j.id) AS job_count', '           FROM mechanics m', '           LEFT JOIN jobs j ON j.mechanic_id = m.id AND j.due_date BETWEEN ? AND ?', '                           AND j.status NOT IN (\'ready\', \'collected\')', '           GROUP BY m.id ORDER BY m.id""",', '    rows.sort(key=lambda r: r["spare_hours"])'],
    tests: ['def test_workload_week_and_exclusions(client):', 'def test_workload_week_boundaries(client):', 'def test_workload_bad_date(client):'],
  };

  /* The real modules of systems/spokes-and-sprockets (checked on disk; data/story.js's handover.files list is not
     the real one). Route counts per file are from its @router decorators: 23 in all. */
  const FILES = [['app.py', 0], ['db.py', 0], ['services.py', 0], ['routes_customers.py', 5], ['routes_jobs.py', 7],
    ['routes_mechanics.py', 1], ['routes_money.py', 2], ['routes_parts.py', 6], ['routes_reports.py', 2]];

  /* Theo's Lisbon desk: a thin tiling-WM status bar (a stand-in; video/v2/look/lisbon-pc/ has no desk yet). */
  function wmBar(svg, w, { title, ws = 2, when = 'Mon 23 Nov  15:05', fg = '#C9C7BF', bg = '#0E0F12', accent = '#F0A458' }) {
    const g = el('g', { 'font-family': 'Cascadia Code', 'font-size': 12.5 }, svg);
    el('rect', { x: 0, y: 0, width: w, height: 26, fill: bg }, g);
    [1, 2, 3, 4].forEach((n, i) => {
      if (n === ws) el('rect', { x: 8 + i * 24, y: 4, width: 20, height: 18, rx: 2, fill: accent }, g);
      text(g, 18 + i * 24, 17.5, String(n), { fill: n === ws ? bg : fg, 'text-anchor': 'middle', 'font-weight': n === ws ? 700 : 400 });
    });
    text(g, 112, 17.5, title, { fill: fg });
    text(g, w - 10, 17.5, when, { fill: fg, 'text-anchor': 'end' });
    return g;
  }
  /* a block of code lines, cut with an ellipsis at maxChars (never silently clipped) */
  function code(parent, x, y, lines, { lh = 16, fs = 12, maxChars = 80, fill = '#ddd', plus = null, plusFill } = {}) {
    const g = el('g', { 'font-family': 'Cascadia Code', 'font-size': fs }, parent);
    lines.forEach((l, i) => {
      let s = l.length > maxChars ? l.slice(0, maxChars - 1) + '…' : l;
      if (plus && s.startsWith('+')) { text(g, x, y + i * lh, '+', { fill: plusFill || fill }); s = s.slice(1); text(g, x + fs * .6, y + i * lh, s, { fill, style: 'white-space:pre' }); }
      else text(g, x, y + i * lh, s, { fill, style: 'white-space:pre' });
    });
    return g;
  }

  window.THEO = { el, svgRoot, text, projection, wallPieces, groups, splitKey, centroid, mark, DIFF, NS, FILES, wmBar, code };
})();
