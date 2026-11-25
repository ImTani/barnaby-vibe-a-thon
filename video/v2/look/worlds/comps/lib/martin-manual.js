/* Martin · THE DEALER MANUAL PLATE. The building as a cutaway plan-oblique plate in the bike trade's service-manual
   line art: the plan stays true, walls rise at an angle and are cut at waist height (cut tops solid black, the plan's
   poche), tall fixtures cut and hatched, bikes drawn in side elevation on their stands. Each ability is a numbered
   callout on the object where it happens; Barnaby's route is drawn like a cable-routing line.
   State by line and pattern only: solid disc = he can use it; open ring + key = needs Martin's key; struck = kept shut.
   One spot colour (blue) for the route and the room he is in; red once, for the shortfall.
   MANUAL.draw(svg, opts) -> {P, f, bubble(n)}  opts: {moment, orient:'land'|'port', s, ox, oy, detail:'full'|'low'} */
window.MANUAL = (function () {
  const M = MPLAN, B = M.B, el = M.el;
  const INK = '#111111', PAPER = '#FFFFFF', SPOT = '#1B4FD8', RED = '#D32212';
  const K = { x: 0.40, y: 0.72 };
  const CUT = 0.9, CUT_NEAR = 0.22;

  function draw(svg, o) {
    const moment = o.moment, built = moment === 'build' || moment === 'priyaTuesday';
    const f = M.tf(o), s = o.s, low = o.detail === 'low';
    const d = [K.x * s, -K.y * s];
    const P = (x, y, z = 0) => { const p = f(x, y); return [p[0] + z * d[0], p[1] + z * d[1]]; };
    const pstr = arr => arr.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
    const lw = Math.max(1, s / 40);   // base line weight

    /* defs: hatches */
    const defs = el('defs', {}, svg);
    const hatch = (id, color, gap, w, ang) => {
      const p = el('pattern', { id, patternUnits: 'userSpaceOnUse', width: gap, height: gap, patternTransform: `rotate(${ang})` }, defs);
      el('line', { x1: 0, y1: 0, x2: 0, y2: gap, stroke: color, 'stroke-width': w }, p);
    };
    hatch('mh-cut', INK, 5, 1.1, 45);
    hatch('mh-spot', SPOT, 9, 1.4, -45);
    hatch('mh-new', INK, 4, 1.2, -45);
    const mk = el('marker', { id: 'mh-arrow', viewBox: '0 0 10 10', refX: 6, refY: 5, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse' }, defs);
    el('path', { d: 'M0,0 L10,5 L0,10 Z', fill: SPOT }, mk);

    const gFloor = el('g', {}, svg), gObj = el('g', {}, svg), gOver = el('g', {}, svg);

    /* where Barnaby is: the active room */
    const activeRoom = moment === 'martinKey' ? 'goodsin' : moment === 'build' ? 'reports' : null;

    /* floor: building outline, room floors */
    const outline = [[0, 0], [20, 0], [20, 9], [0, 9]].map(p => P(...p));
    el('polygon', { points: pstr(outline), fill: PAPER, stroke: 'none' }, gFloor);
    if (activeRoom) {
      const r = B.rooms[activeRoom];
      el('polygon', { points: pstr(r.poly.map(p => P(...p))), fill: 'url(#mh-spot)', opacity: 0.55 }, gFloor);
    }
    /* planned (unbuilt) Reports room: dashed on the floor */
    if (!built) {
      for (const sg of M.plannedLines()) el('line', { x1: P(sg[0], sg[1])[0], y1: P(sg[0], sg[1])[1], x2: P(sg[2], sg[3])[0], y2: P(sg[2], sg[3])[1], stroke: INK, 'stroke-width': lw * 1.3, 'stroke-dasharray': `${s * 0.18} ${s * 0.12}` }, gFloor);
    }
    /* door swings (floor level) */
    for (const dr of M.doors({ built })) {
      const h = P(...dr.hinge), lf = P(...dr.leaf);
      const dash = dr.planned ? `${s * 0.12} ${s * 0.1}` : null;
      el('path', { d: M.arcPath(f, dr), fill: 'none', stroke: INK, 'stroke-width': lw * 0.8, 'stroke-dasharray': dash || `${s * 0.06} ${s * 0.05}` }, gFloor);
      el('line', { x1: h[0], y1: h[1], x2: lf[0], y2: lf[1], stroke: INK, 'stroke-width': lw * 1.6, 'stroke-dasharray': dash }, gFloor);
    }

    /* ---------- prisms, painter-sorted ---------- */
    const items = [];
    const prism = (r, z0, z1, top, opts = {}) => items.push({ r, z0, z1, top, opts });
    const centerDot = r => { const c = f((r[0] + r[2]) / 2, (r[1] + r[3]) / 2); return c[0] * d[0] + c[1] * d[1]; };

    for (const w of M.wallPieces({ built })) {
      const r = w.r;
      // near exterior walls (facing the viewer) are cut low so the interior reads
      let z = CUT;
      if (w.ext) {
        const c = f((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), mid = f(10, 4.5);
        const out = [c[0] - mid[0], c[1] - mid[1]];
        if (out[0] * -d[0] + out[1] * -d[1] > 0) z = CUT_NEAR;
      }
      if (w.kind === 'sill') prism(r, 0, Math.min(z, 0.55), 'glass', { wall: true });
      else prism(r, 0, z, w.planned ? 'new' : 'cut', { wall: true });
    }
    const fx = id => M.fixture(id);
    const R = (id) => { const q = fx(id).rect; return [q[0], q[1], q[0] + q[2], q[1] + q[3]]; };
    prism(R('counter'), 0, 0.95, 'plain');
    prism(R('till'), 0.95, 1.18, 'plain', { label: 'till' });
    prism(R('desk'), 0, 0.75, 'plain');
    prism([7.6, 0.3, 8.6, 0.5], 0.75, 1.15, 'plain', { label: 'pc' });   // the shop PC's monitor
    prism(R('bench'), 0, 0.9, 'plain');
    prism(R('wheelbench'), 0, 0.9, 'plain');
    prism([13.5, 0.4, 13.62, 0.7], 0.9, 1.35, 'plain');   // truing stand upright
    prism([14.1, 0.4, 14.22, 0.7], 0.9, 1.35, 'plain');
    prism(R('shelf-n'), 0, CUT, 'cut'); prism(R('shelf-e'), 0, CUT, 'cut'); prism(R('shelf-mid'), 0, CUT, 'cut');
    prism([16.35, 2.25, 16.85, 2.65], CUT, CUT + 0.16, 'pads', { label: 'pads' });
    prism([15.45, 7.7, 16.15, 8.6], 0, 0.5, 'plain'); prism([16.2, 7.95, 16.75, 8.6], 0, 0.42, 'plain'); prism([15.55, 7.85, 16.05, 8.45], 0.5, 0.85, 'plain');
    // the van in the back lane, cut off at a break line
    if (!o.noVan) prism([20.85, 5.5, o.vanTo || 22.9, 8.4], 0, 1.1, 'plain', { van: true });

    items.sort((a, b) => centerDot(b.r) - centerDot(a.r));
    for (const it of items) drawPrism(it);

    function drawPrism({ r, z0, z1, top, opts }) {
      const base = [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]];
      const B0 = base.map(p => P(p[0], p[1], z0)), T = base.map(p => P(p[0], p[1], z1));
      const cx = B0.reduce((a, p) => a + p[0], 0) / 4, cy = B0.reduce((a, p) => a + p[1], 0) / 4;
      const sw = opts.wall ? lw * 1.1 : lw * 0.9;
      for (let i = 0; i < 4; i++) {
        const a = B0[i], b = B0[(i + 1) % 4];
        const mx = (a[0] + b[0]) / 2 - cx, my = (a[1] + b[1]) / 2 - cy;
        if (mx * -d[0] + my * -d[1] <= 0) continue;
        el('polygon', { points: pstr([a, b, T[(i + 1) % 4], T[i]]), fill: PAPER, stroke: INK, 'stroke-width': sw, 'stroke-linejoin': 'round' }, gObj);
      }
      const fill = top === 'cut' ? INK : top === 'new' ? 'url(#mh-new)' : top === 'pads' ? PAPER : PAPER;
      el('polygon', { points: pstr(T), fill, stroke: top === 'pads' ? RED : INK, 'stroke-width': top === 'pads' ? lw * 2.2 : sw, 'stroke-linejoin': 'round' }, gObj);
      if (top === 'new') el('polygon', { points: pstr(T), fill: 'none', stroke: SPOT, 'stroke-width': lw * 2.2 }, gObj);
      if (top === 'glass') {   // glazing: two lines along the sill
        const m1 = [(T[0][0] + T[3][0]) / 2, (T[0][1] + T[3][1]) / 2], m2 = [(T[1][0] + T[2][0]) / 2, (T[1][1] + T[2][1]) / 2];
        const ln = (r[2] - r[0]) > (r[3] - r[1]);
        const A = ln ? m1 : [(T[0][0] + T[1][0]) / 2, (T[0][1] + T[1][1]) / 2], Bq = ln ? m2 : [(T[2][0] + T[3][0]) / 2, (T[2][1] + T[3][1]) / 2];
        el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1], stroke: INK, 'stroke-width': lw * 0.8 }, gObj);
      }
      if (opts.label === 'till' && !low) {   // drawer line on the till
        el('line', { x1: (T[0][0] * 0.7 + T[1][0] * 0.3), y1: (T[0][1] * 0.7 + T[1][1] * 0.3), x2: (T[3][0] * 0.7 + T[2][0] * 0.3), y2: (T[3][1] * 0.7 + T[2][1] * 0.3), stroke: INK, 'stroke-width': lw * 0.7 }, gObj);
      }
    }

    /* bikes in side elevation (in the vertical plane along x); top view in portrait */
    const bike = (x0, yc, lift, dir) => {
      const r = 0.34, wb = 1.02;
      const L = (u, z) => P(x0 + dir * u, yc, z + lift);
      const g = el('g', { fill: 'none', stroke: INK, 'stroke-width': lw * 0.95, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, gObj);
      const wheel = (uc) => {
        const pts = [];
        for (let i = 0; i <= 36; i++) { const t = i / 36 * Math.PI * 2; pts.push(L(uc + r * Math.cos(t), r + r * Math.sin(t))); }
        el('polyline', { points: pstr(pts) }, g);
        if (!low) { const pts2 = []; for (let i = 0; i <= 36; i++) { const t = i / 36 * Math.PI * 2; pts2.push(L(uc + r * 0.86 * Math.cos(t), r + r * 0.86 * Math.sin(t))); } el('polyline', { points: pstr(pts2), 'stroke-width': lw * 0.5 }, g); }
        const hub = L(uc, r); el('circle', { cx: hub[0], cy: hub[1], r: Math.max(1.5, s * 0.03), fill: INK }, g);
      };
      wheel(0); wheel(wb);
      const bb = [0.42, 0.27], st = [0.30, 0.86], ht = [0.90, 0.84], hb = [0.94, 0.64], ra = [0, r], fa = [wb, r];
      const seg = (a, b) => { const A = L(...a), Bq = L(...b); el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1] }, g); };
      [[ra, bb], [ra, st], [bb, st], [st, ht], [bb, hb], [hb, fa], [ht, hb]].forEach(p => seg(...p));
      seg([0.22, 0.97], [0.40, 0.97]); seg([0.29, 0.86], [0.30, 0.97]);   // saddle
      seg([0.90, 0.84], [0.86, 0.98]); seg([0.86, 0.98], [0.96, 0.99]);    // stem + bars
      return g;
    };
    const stand = (xc, yc) => {
      const g = el('g', { fill: 'none', stroke: INK, 'stroke-width': lw * 1.3, 'stroke-linecap': 'round' }, gObj);
      const a = P(xc, yc, 0), b = P(xc, yc, 1.15), c = P(xc + 0.35, yc, 1.12);
      el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, g); el('line', { x1: b[0], y1: b[1], x2: c[0], y2: c[1] }, g);
      for (const [dx, dy] of [[-0.35, 0], [0.25, -0.3], [0.25, 0.3]]) { const e = P(xc + dx, yc + dy, 0); el('line', { x1: a[0], y1: a[1], x2: e[0], y2: e[1] }, g); }
    };
    const topBike = (xc, yc, rot) => {   // plan view of a bike: wheels as thin tyres, bar across
      const g = el('g', { stroke: INK, 'stroke-width': lw * 1.1, fill: 'none', 'stroke-linecap': 'round' }, gObj);
      const ax = (u, v) => rot ? P(xc + v, yc + u) : P(xc + u, yc + v);
      const ln = (u1, v1, u2, v2) => { const A = ax(u1, v1), Bq = ax(u2, v2); el('line', { x1: A[0], y1: A[1], x2: Bq[0], y2: Bq[1] }, g); };
      ln(-0.85, 0, -0.17, 0); ln(0.17, 0, 0.85, 0); ln(-0.5, 0, 0.62, 0); ln(0.62, -0.22, 0.62, 0.22);
    };
    if (o.orient === 'land' && !low) {
      for (const st of B.fixtures.filter(q => q.stand)) { stand(st.stand[0], st.stand[1]); bike(st.stand[0] - 0.42, st.stand[1], 0.28, 1); }
      for (const [bx, by] of fx('forsale').bikes) bike(bx - 0.1, by, 0, 1);
    } else {
      for (const st of B.fixtures.filter(q => q.stand)) topBike(st.stand[0], st.stand[1], false);
      for (const [bx, by] of fx('forsale').bikes) topBike(bx + 0.5, by, false);
    }

    /* wall-mounted boards as plan symbols on the floor: job board, rota, pegboard */
    for (const id of ['jobboard', 'rota', 'pegboard']) {
      const q = fx(id).rect, a = P(q[0], q[1]), b = P(q[0] + q[2], q[1] + q[3]);
      const rr = M.tf(o).rect(q[0], q[1], q[0] + q[2] + 0.12, q[1] + q[3]);
      el('rect', { x: rr.x, y: rr.y, width: Math.max(rr.w, 4), height: Math.max(rr.h, 4), fill: PAPER, stroke: INK, 'stroke-width': lw * 1.2 }, gObj);
    }
    // the service bell on the counter
    const bl = P(...fx('bell').at, 0.95);
    el('path', { d: `M${bl[0] - s * 0.13},${bl[1]} a${s * 0.13},${s * 0.11} 0 0 1 ${s * 0.26},0 Z`, fill: PAPER, stroke: INK, 'stroke-width': lw }, gObj);
    el('line', { x1: bl[0] - s * 0.17, y1: bl[1], x2: bl[0] + s * 0.17, y2: bl[1], stroke: INK, 'stroke-width': lw * 1.4 }, gObj);

    /* ---------- overlays: route, callouts ---------- */
    const st = M.numbered(moment);
    const api = { P, f, s, items: st, d };

    if (moment === 'martinKey') {
      const way = [[7.25, 8.1], [7.4, 5.2], [13.8, 5.2], [13.8, 1.7], [15.6, 1.7], [15.6, 3.3], [16.6, 3.3], [17.7, 3.6], [17.7, 5.6], [18.9, 6.6]];
      const pts = way.map(p => P(p[0], p[1], 0.02));
      el('polyline', { points: pstr(pts), fill: 'none', stroke: PAPER, 'stroke-width': lw * 7, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, gOver);
      el('polyline', { points: pstr(pts), fill: 'none', stroke: SPOT, 'stroke-width': lw * 3.2, 'stroke-dasharray': `${s * 0.32} ${s * 0.14}`, 'stroke-linejoin': 'round', 'marker-end': 'url(#mh-arrow)' }, gOver);
      api.routePts = pts;
    }

    /* callout bubbles: plan positions for each ability's number (landscape tuned), leader to the object */
    const BUB = {
      search: [2.55, 3.2], customer_detail: [2.55, 2.4], add_customer: [2.55, 4.0], book_job: [2.55, 4.8],
      notify: [5.7, 3.25], recent_notifications: [5.7, 4.05], unpaid: [5.7, 0.85], create_invoice: [5.7, 1.65], takings: [5.7, 2.45],
      open_jobs: [7.75, 7.35], jobs_due: [7.75, 8.15], job_detail: [9.5, 5.85], update_status: [11.9, 5.85], assign: [12.4, 4.4],
      mechanics: [7.75, 4.3], cancel_job: [10.0, 8.05],
      parts_low: [16.95, 3.98], parts: [18.3, 1.45], adjust: [19.05, 4.3],
      create_purchase_order: [18.35, 7.55], purchase_orders: [17.3, 7.05], receive: [16.25, 6.75],
      today_at_a_glance: [9.15, 1.75], workload: [11.1, 1.5],
    };
    const ZA = { counter: 0.95, till: 1.18, office: 0.75, stockroom: CUT, workshop: 0.0, backdoor: 0.0 };
    const R0 = o.bubbleR || Math.max(11, s * 0.27);
    const font = o.font || 'Bahnschrift';
    api.bubble = {};
    const drawBubble = (a, x, y, r, big) => {
      const g = el('g', {}, gOver);
      const stt = a.state;
      if (stt === 'lit') el('circle', { cx: x, cy: y, r, fill: INK }, g);
      else if (stt === 'asking') { el('circle', { cx: x, cy: y, r: r * 1.0, fill: SPOT }, g); }
      else if (stt === 'new') { el('circle', { cx: x, cy: y, r, fill: SPOT }, g); }
      else el('circle', { cx: x, cy: y, r: r - lw * 0.9, fill: PAPER, stroke: INK, 'stroke-width': lw * 1.8 }, g);
      const t = M.text(g, x, y + r * 0.36, String(a.n), { 'text-anchor': 'middle', 'font-family': font, 'font-weight': 700, 'font-size': r * 1.02, fill: (stt === 'lit' || stt === 'asking' || stt === 'new') ? PAPER : INK });
      if (stt === 'shut') el('line', { x1: x - r * 0.95, y1: y + r * 0.95, x2: x + r * 0.95, y2: y - r * 0.95, stroke: INK, 'stroke-width': lw * 2.2 }, g);
      if (stt === 'key' || stt === 'asking') keyGlyph(g, x + r * 1.02, y + r * 0.5, r * 0.5, stt === 'asking' ? SPOT : INK);
      return g;
    };
    function keyGlyph(g, x, y, k, col) {   // a drawn key, bow on the left (k = bow radius-ish)
      const kg = el('g', { transform: `translate(${x},${y}) rotate(-28)` }, g);
      const w = Math.max(1.7, k * 0.34);
      el('circle', { cx: k * 0.62, cy: 0, r: k * 0.62, fill: PAPER, stroke: col, 'stroke-width': w }, kg);
      el('path', { d: `M${k * 1.24},0 H${k * 2.9} M${k * 2.3},0 V${k * 0.75} M${k * 2.85},0 V${k * 0.6}`, fill: 'none', stroke: col, 'stroke-width': w, 'stroke-linecap': 'butt' }, kg);
    }
    api.keyGlyph = keyGlyph;
    const show = o.callouts !== false;
    for (const a of st) {
      if (a.state === 'planned') continue;
      if (!show && a.state !== 'new') continue;
      const bp = o.bubblePos && o.bubblePos[a.tool] || BUB[a.tool];
      const z = a.group === 'counter' || a.group === 'till' ? ZA[a.group] : a.group === 'office' ? (a.tool === 'workload' ? 0 : 0.75) : a.tool === 'parts' || a.tool === 'adjust' ? CUT : 0.05;
      const an = P(a.anchor[0], a.anchor[1], z);
      const bb = P(bp[0], bp[1], 0);
      const r = a.state === 'asking' ? R0 * 1.25 : R0;
      el('line', { x1: an[0], y1: an[1], x2: bb[0], y2: bb[1], stroke: a.state === 'asking' ? SPOT : INK, 'stroke-width': lw * (a.state === 'asking' ? 1.6 : 0.9) }, gOver);
      el('circle', { cx: an[0], cy: an[1], r: Math.max(2, lw * 1.6), fill: a.state === 'asking' ? SPOT : INK }, gOver);
      drawBubble(a, bb[0], bb[1], r);
      api.bubble[a.tool] = { x: bb[0], y: bb[1], r, n: a.n };
    }
    api.drawBubble = drawBubble;
    api.gOver = gOver;
    return api;
  }
  return { draw, INK, PAPER, SPOT, RED };
})();
